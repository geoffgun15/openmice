"""Import routes, add ground references/thermal vias, and remove redundant vias.

Run using KiCad's Python. Inspect DRC before exporting fabrication files.
"""
import sys
import json
import re
from pathlib import Path
import pcbnew as pcb

ROOT=Path(__file__).resolve().parents[1]
def mm(x):return pcb.FromMM(x)
def point(x,y):return pcb.VECTOR2I(mm(x),mm(y))

def track(board,net,points,layer,width=0.17):
    for a,b in zip(points,points[1:]):
        t=pcb.PCB_TRACK(board);t.SetStart(point(*a));t.SetEnd(point(*b))
        t.SetWidth(mm(width));t.SetLayer(layer);t.SetNetCode(board.GetNetsByName()[net].GetNetCode())
        board.Add(t)

def ground_via(board,x,y,thermal=False):
    v=pcb.PCB_VIA(board);v.SetPosition(point(x,y));v.SetWidth(mm(0.5));v.SetDrill(mm(0.2))
    v.SetViaType(pcb.VIATYPE_THROUGH);v.SetLayerPair(pcb.F_Cu,pcb.B_Cu)
    v.SetNetCode(board.GetNetsByName()['GND'].GetNetCode())
    v.SetFrontTentingMode(pcb.TENTING_MODE_NOT_TENTED if thermal else pcb.TENTING_MODE_TENTED)
    v.SetBackTentingMode(pcb.TENTING_MODE_TENTED)
    board.Add(v)

def make_plane(board,layer,w,h):
    z=pcb.ZONE(board);z.SetLayer(layer);z.SetNetCode(board.GetNetsByName()['GND'].GetNetCode())
    z.SetLocalClearance(mm(0.2));z.SetMinThickness(mm(0.125))
    z.SetPadConnection(pcb.ZONE_CONNECTION_FULL)
    z.Outline().NewOutline()
    for x,y in [(0.25,0.25),(w-0.25,0.25),(w-0.25,h-0.25),(0.25,h-0.25)]:
        z.Outline().Append(mm(x),mm(y))
    board.Add(z)

for name in sys.argv[1:] or ('mouse','receiver'):
    folder=ROOT/'hardware'/name;path=folder/(name+'.kicad_pcb')
    b=pcb.LoadBoard(str(path))
    if not pcb.ImportSpecctraSES(b,str(folder/'routing'/(name+'.ses'))):
        raise RuntimeError('Session import failed: '+name)
    b.SetCopperLayerCount(4)
    for t in b.GetTracks():
        if isinstance(t,pcb.PCB_VIA):
            t.SetViaType(pcb.VIATYPE_THROUGH);t.SetLayerPair(pcb.F_Cu,pcb.B_Cu)
            t.SetFrontTentingMode(pcb.TENTING_MODE_TENTED);t.SetBackTentingMode(pcb.TENTING_MODE_TENTED)
    # A through via with tracks only on one outer layer contributes no routing.
    # Remove it while retaining continuous tracks through that coordinate.
    b.BuildConnectivity();connectivity=b.GetConnectivity()
    redundant=[]
    for item in b.GetTracks():
        if not isinstance(item,pcb.PCB_VIA) or item.GetNetname()=='GND':continue
        tracks=list(connectivity.GetConnectedTracks(item))
        pads=list(connectivity.GetConnectedPads(item))
        layers={t.GetLayer() for t in tracks}
        if len(layers)<2 and not pads:redundant.append(item)
    for item in redundant:b.Remove(item)
    for footprint in b.GetFootprints():
        if any(p.GetAttribute()==pcb.PAD_ATTRIB_PTH for p in footprint.Pads()):
            footprint.SetAttributes(pcb.FP_THROUGH_HOLE)
    for drawing in b.GetDrawings():
        if isinstance(drawing,pcb.PCB_TEXT):
            drawing.SetText(drawing.GetText().replace('PLACEMENT DRAFT - NOT FOR FABRICATION','A1 ROUTED PROTOTYPE - PHYSICAL TESTS NOT RUN').replace('RECEIVER A0','RECEIVER A1'))
    if name=='receiver':
        # Connect the ESD supply escape to the existing rear-side VBUS via.
        track(b,'USB_VBUS',[(14,11.4223),(11.55,9.9849)],pcb.B_Cu)
        ground_via(b,14,12.6375)
    else:
        # Three corner vias and the center via from TI's thermal-pad pattern.
        # Lower-right corner is occupied by a rear-side configuration trace.
        for x,y in ((15.42,13.42),(16.58,13.42),(15.42,14.58),(16,14)):
            ground_via(b,x,y,thermal=True)
    for area in list(b.Zones()):
        if area.GetIsRuleArea():
            layers=pcb.LSET()
            for layer in (pcb.F_Cu,pcb.In1_Cu,pcb.In2_Cu,pcb.B_Cu):layers.AddLayer(layer)
            area.SetLayerSet(layers)
        else:b.Remove(area)
    size=json.loads((folder/'connectivity.json').read_text())
    w,h=size['width_mm'],size['height_mm']
    b.SetLayerType(pcb.In1_Cu,pcb.LT_POWER);b.SetLayerType(pcb.In2_Cu,pcb.LT_POWER)
    for layer in (pcb.In1_Cu,pcb.In2_Cu):make_plane(b,layer,w,h)
    # Perimeter ground ties keep both reference planes at the same potential.
    for x,y in [(1.5,1.5),(w-1.5,1.5),(1.5,h/2),(w-1.5,h/2),(1.5,h-1.5),(w-1.5,h-1.5)]:
        ground_via(b,x,y)
    b.BuildConnectivity()
    pcb.ZONE_FILLER(b).Fill(b.Zones())
    # KiCad local labels produce sheet-qualified net names in the schematic.
    for net in list(b.GetNetsByName().values()):
        if net.GetNetname() and not net.GetNetname().startswith('/'):
            net.SetNetname('/'+net.GetNetname())
    # Give intentional NC pads the same distinct net names as Eeschema.
    tokens=re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+',(folder/(name+'.net')).read_text())
    stack=[];tree=None
    for token in tokens:
        if token=='(':
            node=[]
            if stack:stack[-1].append(node)
            else:tree=node
            stack.append(node)
        elif token==')':stack.pop()
        else:stack[-1].append(json.loads(token) if token.startswith('"') else token)
    def child(node,key):return next(x for x in node if isinstance(x,list) and x[0]==key)
    footprints={f.GetReference():f for f in b.GetFootprints()}
    for net in child(tree,'nets')[1:]:
        netname=child(net,'name')[1]
        if not netname.startswith('unconnected-'):continue
        native=pcb.NETINFO_ITEM(b,netname);b.Add(native)
        for node in net:
            if not isinstance(node,list) or node[0]!='node':continue
            ref=child(node,'ref')[1];number=child(node,'pin')[1]
            for pad in footprints[ref].Pads():
                if pad.GetNumber()==number:pad.SetNet(native)
    pcb.SaveBoard(str(path),b)
    size['status']='routed A1 prototype; physical tests NOT RUN'
    (folder/'connectivity.json').write_text(json.dumps(size,indent=2)+'\n')
    print(name,'ground planes filled;',len(redundant),'redundant vias removed')
