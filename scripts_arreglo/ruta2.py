# -*- coding: utf-8 -*-
import pcbnew
B = pcbnew.LoadBoard("T8Sequencer.kicad_pcb")
FM, TM = pcbnew.FromMM, pcbnew.ToMM
def V(x,y): return pcbnew.VECTOR2I(FM(x), FM(y))
F, Bo = pcbnew.F_Cu, pcbnew.B_Cu
def cerca(p,x,y,tol=0.03): return abs(TM(p.x)-x)<tol and abs(TM(p.y)-y)<tol

# --- borrar el intento anterior y los ramales muertos del display -----------
BORRA = [("/DISP_SCK",191.35,109.50,215.50,94.08),
         ("/DISP_MOSI",184.50,98.80,191.00,105.30),
         ("/DISP_MOSI",191.00,105.30,191.00,109.00),
         ("/DISP_SCK",191.60,104.67,184.93,98.00),
         ("/DISP_SCK",191.60,109.50,191.60,104.67)]
fuera=[]
for t in B.GetTracks():
    if t.GetClass()=="PCB_VIA":
        if t.GetNetname()=="/DISP_SCK" and cerca(t.GetPosition(),191.35,109.50): fuera.append(t)
        continue
    for n,x1,y1,x2,y2 in BORRA:
        if t.GetNetname()!=n: continue
        a,b=t.GetStart(),t.GetEnd()
        if (cerca(a,x1,y1) and cerca(b,x2,y2)) or (cerca(a,x2,y2) and cerca(b,x1,y1)):
            fuera.append(t); break
print("elementos retirados (intento previo + ramales muertos):", len(fuera))
for t in fuera: B.Remove(t)

# --- rutado definitivo --------------------------------------------------------
def trk(x1,y1,x2,y2,layer,net,w=0.2):
    t=pcbnew.PCB_TRACK(B); t.SetStart(V(x1,y1)); t.SetEnd(V(x2,y2))
    t.SetLayer(layer); t.SetWidth(FM(w)); t.SetNet(B.FindNet(net)); B.Add(t)
def via(x,y,net):
    v=pcbnew.PCB_VIA(B); v.SetPosition(V(x,y)); v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetLayerPair(F,Bo); v.SetDrill(FM(0.3))
    try: v.SetWidth(FM(0.6))
    except TypeError: v.SetWidth(F,FM(0.6))
    v.SetNet(B.FindNet(net)); B.Add(v)

# RES y DC: recta por la cara inferior, no se cruzan con nadie
trk(180.10, 99.50, 215.50, 99.16, Bo, "/RES");   print("  /RES      -> pin 5, recta por B.Cu")
trk(180.10,101.50, 215.50,101.70, Bo, "/DC");    print("  /DC       -> pin 6, recta por B.Cu")

# CS: salta por arriba a la cara superior para pasar por debajo de DC
trk(180.84,101.18, 182.50,103.00, F,  "/TFT_CS"); via(182.50,103.00,"/TFT_CS")
trk(182.50,103.00, 215.50,104.24, Bo, "/TFT_CS"); print("  /TFT_CS   -> pin 7, esquiva a DC")

# MOSI: sale del bus de y=109, cruza por B.Cu y sube por F.Cu en x=213
trk(191.00,109.00, 193.00,107.00, F,  "/DISP_MOSI"); via(193.00,107.00,"/DISP_MOSI")
trk(193.00,107.00, 213.00,107.00, Bo, "/DISP_MOSI"); via(213.00,107.00,"/DISP_MOSI")
trk(213.00,107.00, 213.00, 96.62, F,  "/DISP_MOSI"); via(213.00, 96.62,"/DISP_MOSI")
trk(213.00, 96.62, 215.50, 96.62, Bo, "/DISP_MOSI"); print("  /DISP_MOSI-> pin 4, sube por x=213")

# SCK: igual pero subiendo por x=211
trk(191.60,109.50, 194.50,109.50, F,  "/DISP_SCK"); via(194.50,109.50,"/DISP_SCK")
trk(194.50,109.50, 211.00,109.50, Bo, "/DISP_SCK"); via(211.00,109.50,"/DISP_SCK")
trk(211.00,109.50, 211.00, 94.08, F,  "/DISP_SCK"); via(211.00, 94.08,"/DISP_SCK")
trk(211.00, 94.08, 215.50, 94.08, Bo, "/DISP_SCK"); print("  /DISP_SCK -> pin 3, sube por x=211")

pcbnew.ZONE_FILLER(B).Fill(B.Zones())
B.Save("T8Sequencer.kicad_pcb")
print("guardado")
