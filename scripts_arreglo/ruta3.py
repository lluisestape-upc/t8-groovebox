# -*- coding: utf-8 -*-
import pcbnew
B = pcbnew.LoadBoard("T8Sequencer.kicad_pcb")
FM, TM = pcbnew.FromMM, pcbnew.ToMM
def V(x,y): return pcbnew.VECTOR2I(FM(x), FM(y))
F, Bo = pcbnew.F_Cu, pcbnew.B_Cu
def cerca(p,x,y,tol=0.03): return abs(TM(p.x)-x)<tol and abs(TM(p.y)-y)<tol

BORRA = [("/DISP_MOSI",191.00,109.00,180.60,109.00),
         ("/DISP_MOSI",180.60,109.00,180.10,108.50),
         ("/DISP_MOSI",191.00,109.00,193.00,107.00),
         ("/DISP_MOSI",193.00,107.00,213.00,107.00),
         ("/DISP_SCK",180.10,109.50,191.60,109.50),
         ("/DISP_SCK",191.60,109.50,194.50,109.50),
         ("/DISP_SCK",194.50,109.50,211.00,109.50),
         ("/TFT_CS",180.84,101.18,182.50,103.00),
         ("/TFT_CS",182.50,103.00,215.50,104.24),
         ("/RES",181.00,99.50,181.10,99.60),
         ("/RES",180.10,99.50,181.00,99.50),
         ("/DC",180.10,101.50,180.10,101.07),
         ("/DC",180.10,101.07,180.77,100.40)]
VIAS = [("/DISP_MOSI",193.00,107.00), ("/DISP_SCK",194.50,109.50), ("/TFT_CS",182.50,103.00)]
fuera=[]
for t in B.GetTracks():
    if t.GetClass()=="PCB_VIA":
        if any(t.GetNetname()==n and cerca(t.GetPosition(),x,y) for n,x,y in VIAS): fuera.append(t)
        continue
    a,b=t.GetStart(),t.GetEnd()
    for n,x1,y1,x2,y2 in BORRA:
        if t.GetNetname()!=n: continue
        if (cerca(a,x1,y1) and cerca(b,x2,y2)) or (cerca(a,x2,y2) and cerca(b,x1,y1)):
            fuera.append(t); break
print("retirados:", len(fuera))
for t in fuera: B.Remove(t)

def trk(x1,y1,x2,y2,layer,net,w=0.2):
    t=pcbnew.PCB_TRACK(B); t.SetStart(V(x1,y1)); t.SetEnd(V(x2,y2))
    t.SetLayer(layer); t.SetWidth(FM(w)); t.SetNet(B.FindNet(net)); B.Add(t)
def via(x,y,net):
    v=pcbnew.PCB_VIA(B); v.SetPosition(V(x,y)); v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetLayerPair(F,Bo); v.SetDrill(FM(0.3))
    try: v.SetWidth(FM(0.6))
    except TypeError: v.SetWidth(F,FM(0.6))
    v.SetNet(B.FindNet(net)); B.Add(v)

trk(189.80,97.20, 184.70,97.20, F, "/3.3V")
print("  /3.3V     reconectada la rama que quedo suelta")
trk(180.84,101.18, 183.00,103.50, F, "/TFT_CS"); via(183.00,103.50,"/TFT_CS")
trk(183.00,103.50, 215.50,104.24, Bo, "/TFT_CS")
print("  /TFT_CS   -> pin 7")
trk(180.10,108.50, 213.00,107.00, Bo, "/DISP_MOSI")
print("  /DISP_MOSI-> pin 4 (arranca de la via que ya habia)")
trk(180.10,109.50, 211.00,109.50, Bo, "/DISP_SCK")
print("  /DISP_SCK -> pin 3 (arranca de la via que ya habia)")

pcbnew.ZONE_FILLER(B).Fill(B.Zones())
B.Save("T8Sequencer.kicad_pcb")
print("guardado")
