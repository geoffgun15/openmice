"""Run with KiCad's bundled Python. Prepare native boards and two-layer DSN.

The final PCB uses four copper layers. Signal routing is confined to the outer
layers; the inner layers are uninterrupted ground references outside cutouts.
"""
import sys
import json
import uuid
from pathlib import Path
import pcbnew as pcb

ROOT=Path(__file__).resolve().parents[1]
def mm(value):return pcb.FromMM(value)
def vec(x,y):return pcb.VECTOR2I(mm(x),mm(y))

def wire(board,net,points,layer=pcb.F_Cu,width=0.17):
    code=board.GetNetsByName()[net].GetNetCode()
    for start,end in zip(points,points[1:]):
        track=pcb.PCB_TRACK(board)
        track.SetStart(vec(*start));track.SetEnd(vec(*end))
        track.SetWidth(mm(width));track.SetLayer(layer);track.SetNetCode(code)
        track.SetLocked(True)
        board.Add(track)

def via(board,net,point):
    item=pcb.PCB_VIA(board)
    item.SetPosition(vec(*point));item.SetWidth(mm(0.5));item.SetDrill(mm(0.2))
    item.SetViaType(pcb.VIATYPE_THROUGH);item.SetLayerPair(pcb.F_Cu,pcb.B_Cu)
    item.SetNetCode(board.GetNetsByName()[net].GetNetCode());item.SetLocked(True)
    board.Add(item)

def usb_routing(board,name):
    # USB-C duplicated contacts need short crossover stubs. Main USB pair stays
    # on F.Cu over In1 ground, with 0.17mm width / 0.15mm gap along long runs.
    cx=32 if name=='mouse' else 14
    dpx,dmx=cx-0.75,cx+0.75
    for net,primary,secondary,y in [('USB_DP',dpx,cx+0.25,8.6),('USB_DM',dmx,cx-0.25,9.12)]:
        wire(board,net,[(secondary,7.645),(secondary,y)])
        via(board,net,(secondary,y));via(board,net,(primary,y))
        wire(board,net,[(secondary,y),(primary,y)],pcb.B_Cu)
    for net,x,pad_x in [('USB_DP',dpx,cx-0.95),('USB_DM',dmx,cx+0.95)]:
        wire(board,net,[(x,7.645),(x,9.75),(pad_x,10.3625),(pad_x,12.6375)])
    if name=='receiver':
        wire(board,'USB_DP',[(13.05,12.6375),(13.05,14.5),(6,21.55),(6,37.8),(6.85,38.65),(9.35,38.65)])
        wire(board,'USB_DM',[(14.95,12.6375),(14.95,13.052),(6.32,21.682),(6.32,36.95),(7.22,37.85),(9.35,37.85)])
    else:
        wire(board,'USB_DP',[(31.05,12.6375),(31.05,14.5),(52,35.45),(52,67),(50,69),(25.5,69),(24.5,70),(24.5,77.5),(25.65,78.65),(27.35,78.65)])
        wire(board,'USB_DM',[(32.95,12.6375),(32.95,15.948),(52.32,35.318),(52.32,67.132),(50.132,69.32),(25.632,69.32),(24.82,70.132),(24.82,77.368),(25.302,77.85),(27.35,77.85)])

for name in sys.argv[1:] or ('mouse','receiver'):
    folder=ROOT/'hardware'/name
    path=folder/(name+'.kicad_pcb')
    board=pcb.LoadBoard(str(path))
    settings=board.GetDesignSettings()
    settings.m_MinClearance=mm(0.125)
    settings.m_TrackMinWidth=mm(0.125)
    settings.m_ViasMinSize=mm(0.5)
    settings.m_ViasMinAnnularWidth=mm(0.15)
    settings.m_MinThroughDrill=mm(0.2)
    settings.m_CopperEdgeClearance=mm(0.25)
    settings.m_HoleToHoleMin=mm(0.25)
    settings.SetCustomTrackWidth(mm(0.17))
    for fp in board.GetFootprints():
        fp.Reference().SetLayer(pcb.F_Fab)
        fp.Reference().SetVisible(True)
        root_uuid=uuid.uuid5(uuid.NAMESPACE_URL,'https://github.com/geoffgun15/OpenMice-Proto/'+name)
        fullpath=pcb.KIID_PATH()
        fullpath.push_back(pcb.KIID(str(root_uuid)))
        fullpath.push_back(pcb.KIID(str(uuid.uuid5(uuid.NAMESPACE_URL,'https://github.com/geoffgun15/OpenMice-Proto/'+name+'/'+fp.GetReference()))))
        fp.SetPath(fullpath)
    if name=='mouse':
        for x,y in ((3.5,10),(60.5,10),(3.5,90),(60.5,90)):
            hole=pcb.PCB_SHAPE()
            hole.SetShape(pcb.SHAPE_T_CIRCLE)
            hole.SetCenter(vec(x,y))
            hole.SetEnd(vec(x+1.35,y))
            hole.SetLayer(pcb.Edge_Cuts)
            hole.SetWidth(mm(0.05))
            board.Add(hole)
    usb_routing(board,name)
    # Routing-only DSN has just the outer layers, preserving plane layers later.
    board.SetCopperLayerCount(2)
    routing=folder/'routing'
    routing.mkdir(exist_ok=True)
    pcb.SaveBoard(str(path),board)
    if not pcb.ExportSpecctraDSN(board,str(routing/(name+'.dsn'))):
        raise RuntimeError('DSN export failed: '+name)
    dsn=routing/(name+'.dsn')
    data=dsn.read_text().replace('(clearance 31.25 (type smd_smd))','(clearance 125 (type smd_smd))')
    # Clearance to machined optical aperture must meet the 0.25mm edge rule.
    if name=='mouse':
        keepouts='\n'.join(f'    (keepout "optical-edge-margin-{layer}" (rect {layer} 22930 -48550 40690 -39450))' for layer in ('F.Cu','B.Cu'))+'\n'
        data=data.replace('    (via "Via[0-1]',keepouts+'    (via "Via[0-1]',1)
    dsn.write_text(data)
    board.SetCopperLayerCount(4)
    pcb.SaveBoard(str(path),board)
    print(name,'native board saved; DSN exported')
