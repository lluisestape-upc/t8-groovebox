# -*- coding: utf-8 -*-
"""Arreglo 4: separar los retornos de +5V/CC2 y rehacer la esquina GND de J1."""
import pcbnew
B = pcbnew.LoadBoard("T8Sequencer.kicad_pcb")
FM, TM = pcbnew.FromMM, pcbnew.ToMM
def V(x,y): return pcbnew.VECTOR2I(FM(x), FM(y))
def near(p,x,y,tol=0.02): return abs(TM(p.x)-x)<tol and abs(TM(p.y)-y)<tol
def trk(x1,y1,x2,y2,layer,n,w=0.2):
    t=pcbnew.PCB_TRACK(B); t.SetStart(V(x1,y1)); t.SetEnd(V(x2,y2))
    t.SetLayer(layer); t.SetWidth(FM(w)); t.SetNet(n); B.Add(t)

F, Bo = pcbnew.F_Cu, pcbnew.B_Cu

# --- 1. separar los retornos: +5V a x=100.0, CC2 a x=101.15 ------------------
MOVE = {"/+5V": (100.5, 100.0), "Net-(J1-CC2)": (101.0, 101.15)}
n=0
for t in B.GetTracks():
    nn=t.GetNetname()
    if nn not in MOVE: continue
    old,new=MOVE[nn]
    if t.GetClass()=="PCB_VIA":
        p=t.GetPosition()
        if abs(TM(p.x)-old)<0.02 and TM(p.y)<8: t.SetPosition(V(new,TM(p.y))); n+=1
        continue
    for setter,getter in ((t.SetStart,t.GetStart),(t.SetEnd,t.GetEnd)):
        p=getter()
        if abs(TM(p.x)-old)<0.02 and 3.0<TM(p.y)<15.0:
            setter(V(new,TM(p.y))); n+=1
print("1) retornos separados:", n, "extremos")

# --- 2. esquina GND de J1 -----------------------------------------------------
DEL = [((32.850,9.200),(32.850,9.200)),
       ((32.850,9.200),(34.320,7.430)),
       ((31.250,7.272),(32.850,9.200)),
       ((31.750,10.000),(32.850,9.200)),
       ((31.250,6.515),(31.250,7.272))]
rm=[]
for t in B.GetTracks():
    if t.GetClass()=="PCB_VIA" or t.GetNetname()!="/GND": continue
    a,b=t.GetStart(),t.GetEnd()
    for (x1,y1),(x2,y2) in DEL:
        if (near(a,x1,y1) and near(b,x2,y2)) or (near(a,x2,y2) and near(b,x1,y1)):
            rm.append(t); break
for t in rm: B.Remove(t)
print("2) tramos GND conflictivos eliminados:", len(rm))

gnd = B.FindNet("/GND")
trk(31.75, 10.00, 33.70, 10.35, F, gnd)   # rodea la via de USB_D- por abajo
trk(33.70, 10.35, 34.32,  8.30, F, gnd)   # entra al pad de blindaje
trk(34.32,  5.50, 34.32,  7.00, F, gnd)   # y lo ata tambien por arriba
print("   3 tramos nuevos: el blindaje entra por abajo y por arriba")

B.Save("T8Sequencer.kicad_pcb")
print("guardado")
