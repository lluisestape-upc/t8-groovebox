# -*- coding: utf-8 -*-
"""Cambia el display: de pads de cable plano a tira de 8 pines (modulo ST7789
2,4'' con orden GND-VCC-SCL-SDA-RES-DC-CS-BLK)."""
import math, pcbnew
B = pcbnew.LoadBoard("T8Sequencer.kicad_pcb")
FM, TM = pcbnew.FromMM, pcbnew.ToMM
def V(x, y): return pcbnew.VECTOR2I(FM(x), FM(y))
F, Bo = pcbnew.F_Cu, pcbnew.B_Cu
CLR, VIA_D, TRK_W = 0.22, 0.6, 0.2

X0, Y0 = 215.5, 89.0
PINES = [(1,"GND","/GND"), (2,"VCC","/3.3V"), (3,"SCL","/DISP_SCK"),
         (4,"SDA","/DISP_MOSI"), (5,"RES","/RES"), (6,"DC","/DC"),
         (7,"CS","/TFT_CS"), (8,"BLK","/3.3V")]
PY = {n: Y0 + (n-1)*2.54 for n,_,_ in PINES}

# --- quitar el footprint viejo y sus muñones ---------------------------------
STUB = [("/3.3V",189.80,97.20,183.00,97.20), ("/3.3V",184.70,97.20,183.00,97.20),
        ("/GND",183.00,96.40,184.70,96.40), ("/GND",180.60,96.40,183.00,96.40),
        ("/TFT_CS",180.85,101.20,183.00,101.20), ("/DC",180.77,100.40,183.00,100.40),
        ("/RES",181.10,99.60,183.00,99.60), ("/DISP_MOSI",183.00,98.80,184.50,98.80),
        ("/DISP_SCK",184.93,98.00,183.00,98.00)]
def es_stub(t):
    if t.GetClass()=="PCB_VIA": return False
    a,b=t.GetStart(),t.GetEnd()
    for n,x1,y1,x2,y2 in STUB:
        if t.GetNetname()!=n: continue
        for p,q,r,s in ((x1,y1,x2,y2),(x2,y2,x1,y1)):
            if abs(TM(a.x)-p)<.02 and abs(TM(a.y)-q)<.02 and abs(TM(b.x)-r)<.02 and abs(TM(b.y)-s)<.02:
                return True
    return False
for t in [t for t in B.GetTracks() if es_stub(t)]: B.Remove(t)
u3 = [f for f in B.GetFootprints() if f.GetReference()=="U3"][0]
B.Remove(u3)
print("footprint viejo del display y sus 9 munones: fuera")

# --- quitar las vias de cosido del pasillo -----------------------------------
n=0
for t in list(B.GetTracks()):
    if t.GetClass()=="PCB_VIA" and t.GetNetname()=="/GND":
        p=t.GetPosition()
        if 191.0 < TM(p.x) < 221.0 and 85.0 < TM(p.y) < 110.0:
            B.Remove(t); n+=1
print("vias de cosido retiradas del pasillo:", n)

# --- la tira de 8 pines -------------------------------------------------------
fp = pcbnew.FootprintLoad(r"C:/Program Files/KiCad/10.0/share/kicad/footprints/Connector_PinHeader_2.54mm.pretty",
                          "PinHeader_1x08_P2.54mm_Vertical")
fp.SetPosition(V(X0, Y0)); fp.SetReference("U3"); fp.SetValue("ST7789 2.4 (modulo)")
fp.SetOrientationDegrees(-90)
B.Add(fp)
pads = {p.GetNumber(): p for p in fp.Pads()}
for num, nom, net in PINES:
    pads[str(num)].SetNet(B.FindNet(net))
for num,_,_ in PINES:
    p=pads[str(num)].GetPosition()
    print("   pin %d en (%.2f, %.2f)"%(num, TM(p.x), TM(p.y)))
B.Save("T8Sequencer.kicad_pcb")
print("guardado (sin rutar todavia)")
