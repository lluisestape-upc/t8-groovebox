# -*- coding: utf-8 -*-
"""Arreglo 3: separar CC2 de la via de RTS, apartar GND de los agujeros de J1,
poner A8/B8 de J1 a GND y quitar los restos colgantes."""
import pcbnew
B = pcbnew.LoadBoard("T8Sequencer.kicad_pcb")
FM, TM = pcbnew.FromMM, pcbnew.ToMM
def V(x,y): return pcbnew.VECTOR2I(FM(x), FM(y))
def near(p, x, y, tol=0.02): return abs(TM(p.x)-x)<tol and abs(TM(p.y)-y)<tol

# --- 1. CC2: bajar el retorno de x=101.5 a x=101.0 ---------------------------
n=0
for t in B.GetTracks():
    if t.GetNetname()!="Net-(J1-CC2)": continue
    for setter, getter in ((t.SetStart, t.GetStart), (t.SetEnd, t.GetEnd)):
        p=getter()
        if near(p,101.5,14.0) or near(p,101.5,6.4):
            setter(V(101.0, TM(p.y))); n+=1
    if t.GetClass()=="PCB_VIA" and near(t.GetPosition(),101.5,6.4):
        t.SetPosition(V(101.0,6.4)); n+=1
print("1) CC2 apartada de la via de /RTS:", n, "extremos movidos")

# --- 2. GND lejos del agujero NPTH de J1 -------------------------------------
n=0
for t in B.GetTracks():
    if t.GetClass()=="PCB_VIA" or t.GetNetname()!="/GND": continue
    for setter, getter in ((t.SetStart,t.GetStart),(t.SetEnd,t.GetEnd)):
        p=getter()
        if (near(p,32.88,8.88,0.05) or near(p,32.85,8.88,0.05)):
            setter(V(32.85, 9.20)); n+=1
print("2) vertice GND alejado del taladro de J1:", n)

# --- 3. A8/B8 de J1 a GND (SBU1/SBU2 sin uso en USB 2.0) ---------------------
gnd = B.FindNet("/GND")
j1 = B.FindFootprintByReference("J1")
n=0
for p in j1.Pads():
    if p.GetNumber() in ("A8","B8") and p.GetNetCode()==0:
        p.SetNet(gnd); n+=1
print("3) pads J1 A8/B8 conectados a /GND:", n)

# --- 4. restos colgantes ------------------------------------------------------
DEAD = [(146.390733,59.500518),(78.45,42.95),(166.848529,49.5),(194.65,67.0375)]
rm=[]
for t in B.GetTracks():
    if t.GetClass()=="PCB_VIA":
        if any(near(t.GetPosition(),x,y,0.01) for x,y in DEAD): rm.append(t)
    else:
        if TM(t.GetLength())<0.4 and any(near(t.GetStart(),x,y,0.01) or near(t.GetEnd(),x,y,0.01) for x,y in DEAD):
            rm.append(t)
for t in rm:
    print("   fuera:", t.GetClass(), t.GetNetname(), round(TM(t.GetPosition().x),3), round(TM(t.GetPosition().y),3))
    B.Remove(t)
print("4) restos colgantes eliminados:", len(rm))

B.Save("T8Sequencer.kicad_pcb")
print("guardado")
