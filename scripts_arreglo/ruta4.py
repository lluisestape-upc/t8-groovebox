# -*- coding: utf-8 -*-
import pcbnew
B = pcbnew.LoadBoard("T8Sequencer.kicad_pcb")
FM, TM = pcbnew.FromMM, pcbnew.ToMM
def V(x,y): return pcbnew.VECTOR2I(FM(x), FM(y))
F, Bo = pcbnew.F_Cu, pcbnew.B_Cu
def cerca(p,x,y,tol=0.03): return abs(TM(p.x)-x)<tol and abs(TM(p.y)-y)<tol

VIAS_FUERA = [("/DISP_SCK",180.10,109.50), ("/DISP_MOSI",180.10,108.50),
              ("/RES",180.10,99.50), ("/DC",180.10,101.50)]
fuera=[]
for t in B.GetTracks():
    if t.GetClass()=="PCB_VIA":
        if any(t.GetNetname()==n and cerca(t.GetPosition(),x,y) for n,x,y in VIAS_FUERA):
            fuera.append(t)
        continue
    a,b=t.GetStart(),t.GetEnd()
    if t.GetNetname()=="/DC" and t.GetLayer()==Bo and \
       ((cerca(a,180.10,101.50) and cerca(b,215.50,101.70)) or
        (cerca(b,180.10,101.50) and cerca(a,215.50,101.70))):
        fuera.append(t)
print("vias redundantes y tramo de DC retirados:", len(fuera))
for t in fuera: B.Remove(t)

def trk(x1,y1,x2,y2,layer,net,w=0.2):
    t=pcbnew.PCB_TRACK(B); t.SetStart(V(x1,y1)); t.SetEnd(V(x2,y2))
    t.SetLayer(layer); t.SetWidth(FM(w)); t.SetNet(B.FindNet(net)); B.Add(t)
trk(180.10,101.50, 180.60,102.30, Bo, "/DC")
trk(180.60,102.30, 215.50,101.70, Bo, "/DC")
print("  /DC rodea la via de CS")
pcbnew.ZONE_FILLER(B).Fill(B.Zones())
B.Save("T8Sequencer.kicad_pcb")
print("guardado")
