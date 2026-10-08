"""Generate editable KiCad schematic/placement drafts from one connectivity model.

No fabrication exports: routing, ERC/DRC, RF and mechanics still require KiCad review.
Uses official KiCad 5 footprints (KiCad can migrate the PCB on first open).
"""
import csv
import json
import math
import re
import uuid
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
HW = ROOT/'hardware'
LIB = HW/'libraries/OpenMice.pretty'

def uid(name):
    return str(uuid.uuid5(uuid.NAMESPACE_URL,'https://github.com/geoffgun15/OpenMice-Proto/'+name))

def quote(value):
    return json.dumps(str(value))

def parse(text):
    tokens = re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+',text)
    stack,root = [],None
    for token in tokens:
        if token == '(':
            node = []
            if stack:
                stack[-1].append(node)
            else:
                root = node
            stack.append(node)
        elif token == ')':
            if not stack:
                raise ValueError('Unbalanced expression')
            stack.pop()
        else:
            if not stack:
                raise ValueError('Stray token')
            stack[-1].append(token)
    if stack:
        raise ValueError('Unclosed expression')
    return root

def sexp(node):
    return '('+' '.join(sexp(item) if isinstance(item,list) else str(item) for item in node)+')'

def child(node,name):
    return next((item for item in node if isinstance(item,list) and item[0]==name),None)

def atom(value):
    return json.loads(value) if value.startswith('"') else value

def footprint(name,pads,width,height):
    content = f'(module {name} (layer F.Cu) (tedit 0) (attr smd)\n'
    content += f'(fp_text reference REF** (at 0 {-height/2-1.4}) (layer F.SilkS) (effects (font (size 1 1) (thickness 0.15))))\n'
    content += f'(fp_text value {name} (at 0 {height/2+1.4}) (layer F.Fab) (effects (font (size 0.8 0.8) (thickness 0.12))))\n'
    for start,end in [((-width/2,-height/2),(width/2,-height/2)),((width/2,-height/2),(width/2,height/2)),((width/2,height/2),(-width/2,height/2)),((-width/2,height/2),(-width/2,-height/2))]:
        content += f'(fp_line (start {start[0]} {start[1]}) (end {end[0]} {end[1]}) (layer F.Fab) (width 0.1))\n'
    for number,x,y,sx,sy,drill in pads:
        if drill:
            content += f'(pad {number} thru_hole circle (at {x} {y}) (size {sx} {sy}) (drill {drill}) (layers *.Cu *.Mask))\n'
        else:
            content += f'(pad {number} smd rect (at {x} {y}) (size {sx} {sy}) (layers F.Cu F.Paste F.Mask))\n'
    content += ')\n'
    (LIB/(name+'.kicad_mod')).write_text(content)

# PAW3395 staggered 1.78mm pin pitch, 10.70mm row spacing, 0.70mm drill.
# Optical center is footprint origin. Mechanical aperture is a separate draft.
sensor_pads = [(str(i+1),round(5.66-i*1.78,3),-5.35,1.3,1.3,0.7) for i in range(8)]
sensor_pads += [(str(9+i),round(-7.85+i*1.78,3),5.35,1.3,1.3,0.7) for i in range(8)]
footprint('PAW3395DM_T6QU',sensor_pads,22,12)
footprint('MouseSwitch_D2F_DRAFT',[(str(i+1),i*5.08,0,1.8,1.8,1.0) for i in range(3)],13,6)

module_text = (LIB/'RF_Module.lib').read_text()
module_section = module_text.split('DEF MDBT50Q-1MV2 ')[1].split('ENDDEF')[0]
module_names = {line.split()[2]:line.split()[1] for line in module_section.splitlines() if line.startswith('X ')}
assert len(module_names)==61

def create_part(ref,value,fp,x,y,nets,names=None,group='misc'):
    nets = {str(pin):net for pin,net in nets.items()}
    pads = [item for item in parse((LIB/(fp+'.kicad_mod')).read_text()) if isinstance(item,list) and item[0]=='pad']
    numbers = {atom(pad[1]) for pad in pads}
    assert set(nets) <= numbers,(ref,set(nets)-numbers)
    pins = {pin:{'name':(names or {}).get(pin,pin),'net':nets.get(pin)} for pin in sorted(numbers,key=lambda p:(not p.isdigit(),int(p) if p.isdigit() else p))}
    return {'ref':ref,'value':value,'footprint':fp,'x':x,'y':y,'pins':pins,'group':group}

def build_parts(receiver=False):
    parts = []
    def add(*args,**kwargs):
        value = create_part(*args,**kwargs)
        parts.append(value)
        return value
    mx,my = (10,36) if receiver else (32,84)
    gpio = {27:'SENSOR_IRQ',36:'SPI_SCLK',37:'SPI_MOSI',38:'SENSOR_NCS',39:'SPI_MISO',41:'SENSOR_RESET',43:'BUTTON_RIGHT',44:'BUTTON_LEFT',45:'BUTTON_MIDDLE',46:'BUTTON_BACK',48:'BUTTON_FORWARD',49:'ENCODER_A',19:'ENCODER_B',20:'BATTERY_ADC'}
    module_nets = {1:'GND',2:'GND',15:'GND',28:'VDD_3V0',30:'VDD_3V0',32:'USB_VBUS',33:'GND',34:'USB_DM',35:'USB_DP',40:'MCU_RESET',51:'SWDIO',53:'SWDCLK',55:'GND',16:'PAIR',17:'LF_XL1',18:'LF_XL2'}
    if not receiver:
        module_nets.update(gpio)
    add('U1','MDBT50Q-1MV2','Raytac_MDBT50Q',mx,my,module_nets,module_names,'controller')
    parts[-1]['rotation'] = 180
    ux,uy = (10,3.6) if receiver else (32,3.6)
    usb_nets = {'A1':'GND','B12':'GND','A12':'GND','B1':'GND','A4':'USB_VBUS','B9':'USB_VBUS','A9':'USB_VBUS','B4':'USB_VBUS','A5':'CC1','B5':'CC2','A6':'USB_DP','B6':'USB_DP','A7':'USB_DM','B7':'USB_DM','S1':'GND'}
    add('J1','USB-C HRO TYPE-C-31-M-12','USB_C',ux,uy,usb_nets,group='USB')
    add('U2','USBLC6-2SC6','SOT-23-6',ux+6,uy+4,{1:'USB_DP',6:'USB_DP',3:'USB_DM',4:'USB_DM',2:'GND',5:'USB_VBUS'},group='USB')
    for i,net in enumerate(('CC1','CC2')):
        add('R'+str(i+1),'5.1k 1%','R_0603_1608Metric',ux-6+i*3,uy+4,{1:net,2:'GND'},group='USB')
    # TLV700 DDC: 1 IN, 2 GND, 3 EN, 4 NC, 5 OUT.
    reg_x,reg_y = (5,13) if receiver else (13,61)
    regulator_in = 'USB_VBUS' if receiver else 'SYSTEM_ON'
    add('U3','TLV70030DDCR','SOT-23-5',reg_x,reg_y,{1:regulator_in,2:'GND',3:regulator_in,5:'VDD_3V0'},group='power')
    add('C1','1uF 10V X7R','C_0603_1608Metric',reg_x-2,reg_y+3,{1:regulator_in,2:'GND'},group='power')
    add('C2','4.7uF 6.3V X5R','C_0603_1608Metric',reg_x+2,reg_y+3,{1:'VDD_3V0',2:'GND'},group='power')
    for i,(dx,dy) in enumerate(((0,-9),(3,-9))):
        add('C'+str(3+i),'100nF 10V X7R','C_0603_1608Metric',mx+dx,my+dy,{1:'VDD_3V0',2:'GND'},group='controller')
    add('C5','1uF 10V X7R','C_0603_1608Metric',ux+3,uy+7,{1:'USB_VBUS',2:'GND'},group='USB')
    add('Y1','32.768kHz 12.5pF ABS07','Crystal_SMD_3215-2Pin_3.2x1.5mm',mx-2,my-11,{1:'LF_XL1',2:'LF_XL2'},group='controller')
    for i,net in enumerate(('LF_XL1','LF_XL2')):
        add('C'+str(6+i),'18pF C0G (tune)','C_0603_1608Metric',mx-4+i*4,my-13,{1:net,2:'GND'},group='controller')
    add('J2','SWD: VDD / SWDIO / SWDCLK / GND / RESET','PinHeader_1x05_P2.54mm_Vertical',2 if receiver else 57,23 if receiver else 67,{1:'VDD_3V0',2:'SWDIO',3:'SWDCLK',4:'GND',5:'MCU_RESET'},group='debug')
    add('SW1','PAIR TL3342','SW_SPST_TL3342',15 if receiver else 10,14 if receiver else 78,{1:'PAIR',2:'GND'},group='controls')
    add('SW2','RESET TL3342','SW_SPST_TL3342',15 if receiver else 10,19 if receiver else 84,{1:'MCU_RESET',2:'GND'},group='controls')
    add('R3','10k','R_0603_1608Metric',16 if receiver else 14,23 if receiver else 84,{1:'VDD_3V0',2:'MCU_RESET'},group='controller')
    if receiver:
        return parts
    sensor_names={str(k):v for k,v in enumerate(('NC','NC','GND','VDD','VDDREG','NC','VDDIO','GNDIO','MOTION','SCLK','MOSI','MISO','NCS','NRESET','LED_P','NC'),1)}
    add('U4','PAW3395DM-T6QU','PAW3395DM_T6QU',32,44,{3:'GND',4:'VDD_1V9',5:'SENSOR_VDDREG',7:'VDD_3V0',8:'GND',9:'SENSOR_IRQ',10:'SPI_SCLK',11:'SPI_MOSI',12:'SPI_MISO',13:'SENSOR_NCS',14:'SENSOR_RESET',15:'SENSOR_LED_P'},sensor_names,'sensor')
    add('U5','TLV70019DDCR','SOT-23-5',46,48,{1:'VDD_3V0',2:'GND',3:'VDD_3V0',5:'VDD_1V9'},group='sensor')
    for ref,value,fp,x,y,net in [('C8','1uF 10V X7R','C_0603_1608Metric',47,51,'VDD_3V0'),('C9','10uF 6.3V X5R','C_0805_2012Metric',45,44,'VDD_1V9'),('C10','100nF X7R','C_0603_1608Metric',43,41,'VDD_1V9'),('C11','4.7uF X5R','C_0603_1608Metric',25,35,'SENSOR_VDDREG'),('C12','100nF X7R','C_0603_1608Metric',28,35,'SENSOR_VDDREG'),('C13','10uF X5R','C_0805_2012Metric',17,45,'VDD_3V0'),('C14','100nF X7R','C_0603_1608Metric',18,48,'VDD_3V0'),('C15','33uF 6.3V X5R','C_0805_2012Metric',42,53,'VDD_1V9')]:
        add(ref,value,fp,x,y,{1:net,2:'GND'},group='sensor')
    add('R4','5.6R 1%','R_0603_1608Metric',40,52,{1:'VDD_1V9',2:'SENSOR_LED_P'},group='sensor')
    add('R5','10k','R_0603_1608Metric',50,42,{1:'VDD_3V0',2:'SPI_MISO'},group='sensor')
    # Integrated power path, hard-limited USB100 mode. Conservative prototype.
    charger_nets={1:'BATTERY_NTC',2:'BATTERY',3:'BATTERY',4:'GND',5:'GND',6:'GND',7:'POWER_GOOD',8:'GND',9:'CHARGING',10:'SYSTEM',11:'SYSTEM',12:'CHARGER_ILIM',13:'USB_VBUS',14:'CHARGER_TMR',15:'GND',16:'CHARGER_ISET',17:'GND'}
    charger_names={str(i):name for i,name in enumerate(('TS','BAT','BAT','CE','EN2','EN1','PGOOD','VSS','CHG','OUT','OUT','ILIM','IN','TMR','TD','ISET','EP'),1)}
    add('U6','BQ24072RGTR','VQFN-16-1EP_3x3mm_P0.5mm_EP1.45x1.45mm',16,14,charger_nets,charger_names,'battery')
    add('J3','Protected 1S 300mAh + 10k NTC (BAT/GND/NTC)','JST_PH_B3B-PH-K_1x03_P2.00mm_Vertical',6,53,{1:'BATTERY',2:'GND',3:'BATTERY_NTC'},group='battery')
    for ref,value,x,y,net in [('R6','5.90k 1%',11,18,'CHARGER_ISET'),('R7','3.09k 1%',14,18,'CHARGER_ILIM'),('R8','68k 1%',17,18,'CHARGER_TMR')]:
        add(ref,value,'R_0603_1608Metric',x,y,{1:net,2:'GND'},group='battery')
    for ref,value,x,y,net in [('C16','1uF 10V X7R',16,10,'USB_VBUS'),('C17','10uF 6.3V X5R',20,17,'SYSTEM'),('C18','10uF 6.3V X5R',11,12,'BATTERY')]:
        add(ref,value,'C_0805_2012Metric',x,y,{1:net,2:'GND'},group='battery')
    add('SW3','Power PCM12','SW_SPDT_PCM12',7,63,{1:'SYSTEM',2:'SYSTEM_ON'},group='battery')
    # One board-side resistor each; NTC must be thermally attached to cell.
    add('R9','100k 1%','R_0603_1608Metric',6,70,{1:'BATTERY',2:'BATTERY_ADC'},group='battery')
    add('R10','100k 1%','R_0603_1608Metric',9,70,{1:'BATTERY_ADC',2:'GND'},group='battery')
    add('C19','100nF X7R','C_0603_1608Metric',12,70,{1:'BATTERY_ADC',2:'GND'},group='battery')
    for ref,net,x in [('R11','POWER_GOOD',9),('R12','CHARGING',12)]:
        add(ref,'100k','R_0603_1608Metric',x,22,{1:'VDD_3V0',2:net},group='battery')
    add('J4','Charger status: GND / PGOOD / CHG','PinHeader_1x03_P2.54mm_Vertical',6,26,{1:'GND',2:'POWER_GOOD',3:'CHARGING'},group='battery')
    # External contacts allow the first prototype to fit a future shell.
    for i,(net,x,y) in enumerate([('BUTTON_LEFT',18,25),('BUTTON_RIGHT',44,25),('BUTTON_MIDDLE',30,20),('BUTTON_BACK',5,39),('BUTTON_FORWARD',5,44)]):
        add('J'+str(5+i),net+' contact','PinHeader_1x02_P2.54mm_Vertical',x,y,{1:net,2:'GND'},group='controls')
    add('J10','Encoder: A / GND / B','PinHeader_1x03_P2.54mm_Vertical',27,12,{1:'ENCODER_A',2:'GND',3:'ENCODER_B'},group='controls')
    return parts

def make_schematic(name,parts):
    symbols,instances = [],[]
    for index,part in enumerate(parts):
        ref = part['ref']
        pins = list(part['pins'].items())
        half = math.ceil(len(pins)/2)
        height = max(5.08,(half+1)*2.54)
        width = 28 if len(pins)>8 else 18
        libid = 'OpenMice:'+ref
        graphics = f'(symbol "{ref}_0_1" (rectangle (start {-width/2} {height/2}) (end {width/2} {-height/2}) (stroke (width 0.254) (type default)) (fill (type background))))'
        pinsexp,local = [],{}
        for i,(number,pin) in enumerate(pins):
            side = -1 if i<half else 1
            row = i if i<half else i-half
            x,y = side*(width/2+2.54),height/2-2.54-row*2.54
            angle = 0 if side<0 else 180
            local[number]=(x,y,side)
            pinsexp.append(f'(pin passive line (at {x} {y} {angle}) (length 2.54) (name {quote(pin["name"])} (effects (font (size 0.8 0.8)))) (number {quote(number)} (effects (font (size 0.8 0.8)))))')
        symbols.append(f'(symbol {quote(libid)} (pin_names (offset 0.5)) (in_bom yes) (on_board yes) (property "Reference" "{ref}" (at 0 {height/2+2} 0) (effects (font (size 1.27 1.27)))) (property "Value" {quote(part["value"])} (at 0 {-height/2-2} 0) (effects (font (size 1 1)))) {graphics} (symbol "{ref}_1_1" {" ".join(pinsexp)}))')
        # A1 canvas. Blocks share net labels, not long crossing wires.
        sx,sy = 55+(index%8)*102,55+(index//8)*75
        instance_id = uid(name+'/'+ref)
        properties = f'(property "Reference" "{ref}" (at {sx} {sy-height/2-4} 0) (effects (font (size 1.27 1.27)))) (property "Value" {quote(part["value"])} (at {sx} {sy+height/2+4} 0) (effects (font (size 1 1)))) (property "Footprint" "OpenMice:{part["footprint"]}" (at {sx} {sy} 0) (effects (font (size 1.27 1.27)) hide))'
        instances.append(f'(symbol (lib_id {quote(libid)}) (at {sx} {sy} 0) (unit 1) (in_bom yes) (on_board yes) (uuid {instance_id}) {properties} (instances (project "{name}" (path "/{uid(name)}" (reference "{ref}") (unit 1)))))')
        for number,pin in pins:
            lx,ly,side = local[number]
            ax,ay = round(sx+lx,5),round(sy-ly,5)
            if pin['net']:
                bx = round(ax+side*2.54,5)
                instances.append(f'(wire (pts (xy {ax} {ay}) (xy {bx} {ay})) (stroke (width 0) (type default)) (uuid {uid(name+ref+number+"wire")}))')
                instances.append(f'(label {quote(pin["net"])} (at {bx} {ay} {0 if side>0 else 180}) (effects (font (size 0.8 0.8)) (justify left bottom)) (uuid {uid(name+ref+number+"label")}))')
            else:
                instances.append(f'(no_connect (at {ax} {ay}) (uuid {uid(name+ref+number+"nc")}))')
    content = f'(kicad_sch (version 20231120) (generator "eeschema") (uuid {uid(name)}) (paper "A1") (title_block (title "{name} - electrical connectivity draft") (rev "A0") (comment 1 "Prototype: routing and ERC/DRC not released")) (lib_symbols {" ".join(symbols)}) {" ".join(instances)} (sheet_instances (path "/" (page "1"))))\n'
    parse(content)
    return content

def make_board(name,parts,width,height):
    nets = sorted({pin['net'] for part in parts for pin in part['pins'].values() if pin['net']})
    netids = {net:i+1 for i,net in enumerate(nets)}
    board = ['kicad_pcb',['version','20171130'],['host','pcbnew',quote('5.1')],['general',['thickness','1.6']],['page','A4'],['layers',['0','F.Cu','signal'],['1','In1.Cu','power'],['2','In2.Cu','signal'],['31','B.Cu','signal'],['32','B.Adhes','user'],['33','F.Adhes','user'],['34','B.Paste','user'],['35','F.Paste','user'],['36','B.SilkS','user'],['37','F.SilkS','user'],['38','B.Mask','user'],['39','F.Mask','user'],['40','Dwgs.User','user'],['41','Cmts.User','user'],['44','Edge.Cuts','user'],['46','B.CrtYd','user'],['47','F.CrtYd','user'],['48','B.Fab','user'],['49','F.Fab','user']],['setup',['pad_to_mask_clearance','0']],['net','0',quote('')]]
    for net,number in netids.items():
        board.append(['net',str(number),quote(net)])
    for part in parts:
        fp = parse((LIB/(part['footprint']+'.kicad_mod')).read_text())
        fp[1] = quote('OpenMice:'+part['footprint'])
        fp = [item for item in fp if not isinstance(item,list) or item[0] not in ('at','path','model')]
        rotation=part.get('rotation',0)
        fp.extend([['at',str(part['x']),str(part['y']),str(rotation)],['path',quote('/'+uid(name+'/'+part['ref']))]])
        for item in fp:
            if not isinstance(item,list):
                continue
            if item[0]=='fp_text':
                if item[1]=='reference':
                    item[2] = quote(part['ref'])
                elif item[1]=='value':
                    item[2] = quote(part['value'])
            elif item[0]=='pad':
                at=child(item,'at')
                old_angle=float(at[3]) if len(at)>3 else 0
                at[:]=['at',at[1],at[2],str((old_angle+rotation)%360)]
                number = atom(item[1])
                net = part['pins'][number]['net']
                if net:
                    item.append(['net',str(netids[net]),quote(net)])
        board.append(fp)
    def line(a,b,layer='Edge.Cuts'):
        board.append(['gr_line',['start',str(a[0]),str(a[1])],['end',str(b[0]),str(b[1])],['layer',layer],['width','0.05']])
    for a,b in [((0,0),(width,0)),((width,0),(width,height)),((width,height),(0,height)),((0,height),(0,0))]:
        line(a,b)
    if name=='mouse':
        # Mechanical CUTOUT is deliberately on drawing layer until lens confirmed.
        for a,b in [((23.2,39.7),(40.4,39.7)),((40.4,39.7),(40.4,48.3)),((40.4,48.3),(23.2,48.3)),((23.2,48.3),(23.2,39.7))]:
            line(a,b,'Dwgs.User')
        label='OPTICAL CUTOUT: VERIFY FIG.4 + LENS'
        tx,ty=32,44
    else:
        label='OPENMICE RECEIVER A0'
        tx,ty=10,18
    board.append(['gr_text',quote(label),['at',str(tx),str(ty)],['layer','Dwgs.User'],['effects',['font',['size','0.8','0.8'],['thickness','0.12']]]])
    board.append(['gr_text',quote('PLACEMENT DRAFT - NOT FOR FABRICATION'),['at',str(width/2),str(height-2)],['layer','Cmts.User'],['effects',['font',['size','0.8','0.8'],['thickness','0.12']]]])
    # Board-level antenna keep-out, all copper layers. Extend past module sides.
    module=parts[0]
    x,y=module['x'],module['y']
    polygon=[(x-7,y+3.95),(x+7,y+3.95),(x+7,y+9),(x-7,y+9)]
    zone=['zone',['net','0'],['net_name',quote('')],['layers','F.Cu','In1.Cu','In2.Cu','B.Cu'],['hatch','edge','0.5'],['connect_pads',['clearance','0']],['min_thickness','0.1'],['keepout',['tracks','not_allowed'],['vias','not_allowed'],['copperpour','not_allowed']],['polygon',['pts',*[['xy',str(px),str(py)] for px,py in polygon]]]]
    board.append(zone)
    return sexp(board)+'\n'

def svg(name,parts,width,height):
    scale=7
    out=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-10 -10 {width*scale+20} {height*scale+75}"><style>text{{font-family:Arial,sans-serif}} .r{{font-size:9px;fill:#e5f2df}} .n{{font-size:7px;fill:#b7c9b0}}</style><rect x="0" y="0" width="{width*scale}" height="{height*scale}" rx="9" fill="#1c493d" stroke="#bdd29c" stroke-width="2"/>']
    for part in parts:
        x,y=part['x']*scale,part['y']*scale
        if part['ref']=='U1':
            w,h=10.5*scale,15.5*scale
            out.append(f'<rect x="{x-7*scale}" y="{y+3.95*scale}" width="{14*scale}" height="{5.05*scale}" fill="#7c8548" opacity=".65"/><text x="{x}" y="{y+7.5*scale}" text-anchor="middle" class="n">RF KEEP-OUT</text>')
        elif part['ref']=='U4':
            w,h=22*scale,12*scale
        elif part['ref']=='J1':
            w,h=9*scale,7*scale
        elif part['ref'].startswith('J'):
            w,h=4*scale,6*scale
        elif part['ref'].startswith('U'):
            w,h=3*scale,3*scale
        elif part['ref'].startswith('SW'):
            w,h=4*scale,3*scale
        else:
            w,h=2*scale,1.2*scale
        out.append(f'<rect x="{x-w/2}" y="{y-h/2}" width="{w}" height="{h}" rx="2" fill="#29473d" stroke="#e2c983" stroke-width=".8"/><text x="{x}" y="{y+3}" text-anchor="middle" class="r">{part["ref"]}</text>')
    out.append(f'<text x="{width*scale/2}" y="{height*scale+25}" text-anchor="middle" fill="#23483c" font-size="13">{name.upper()} · {width} × {height} mm · component placement draft</text><text x="{width*scale/2}" y="{height*scale+44}" text-anchor="middle" fill="#65766a" font-size="10">Unrouted. Verify RF keep-out and optics before fabrication.</text></svg>')
    return ''.join(out)

for name,width,height in [('mouse',64,94),('receiver',20,44)]:
    out = HW/name
    out.mkdir(parents=True,exist_ok=True)
    parts = build_parts(name=='receiver')
    (out/(name+'.kicad_sch')).write_text(make_schematic(name,parts))
    (out/(name+'.kicad_pcb')).write_text(make_board(name,parts,width,height))
    (out/'connectivity.json').write_text(json.dumps({'name':name,'width_mm':width,'height_mm':height,'status':'unrouted placement draft','parts':parts},indent=2)+'\n')
    (out/'placement.svg').write_text(svg(name,parts,width,height))
    (out/'fp-lib-table').write_text('(fp_lib_table (lib (name "OpenMice") (type "KiCad") (uri "${KIPRJMOD}/../libraries/OpenMice.pretty") (options "") (descr "Vendored standard and prototype footprints")))\n')
    with (out/'bom.csv').open('w',newline='') as stream:
        writer=csv.writer(stream)
        writer.writerow(['Reference','Value / part','Footprint','X mm','Y mm','Block'])
        for part in parts:
            writer.writerow([part[key] for key in ('ref','value','footprint','x','y','group')])
    netlist = ['export',['version','D'],['components']]
    for part in parts:
        netlist[2].append(['comp',['ref',quote(part['ref'])],['value',quote(part['value'])],['footprint',quote('OpenMice:'+part['footprint'])]])
    nets = {}
    for part in parts:
        for number,pin in part['pins'].items():
            if pin['net']:
                nets.setdefault(pin['net'],[]).append((part['ref'],number))
    netblock=['nets']
    for i,(net,nodes) in enumerate(sorted(nets.items()),1):
        netblock.append(['net',['code',str(i)],['name',quote(net)],*[['node',['ref',quote(ref)],['pin',quote(number)]] for ref,number in nodes]])
    netlist.append(netblock)
    (out/(name+'.net')).write_text(sexp(netlist)+'\n')
    # Structural checks do not substitute for KiCad ERC/DRC.
    parsed_board = parse((out/(name+'.kicad_pcb')).read_text())
    assert len([x for x in parsed_board if isinstance(x,list) and x[0]=='module'])==len(parts)
    assert all(len(nodes)>=2 for net,nodes in nets.items()),[(net,nodes) for net,nodes in nets.items() if len(nodes)<2]
    print(name,len(parts),'components,',len(nets),'connected nets; structure checked')

(HW/'pin-map.json').write_text(json.dumps({'SCLK':'P0_14','MOSI':'P0_13','MISO':'P0_15','NCS':'P0_16','SENSOR_RESET':'P0_17','MOTION':'P0_11','BUTTONS':['P0_20','P0_21','P0_23','P0_22','P0_24'],'ENCODER':['P0_25','P0_26'],'PAIR':'P0_27','BATTERY_ADC':'P0_04','MCU_RESET':'P0_18'},indent=2)+'\n')
