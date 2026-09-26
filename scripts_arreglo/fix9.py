# -*- coding: utf-8 -*-
"""Cose las islas de masa de la cara superior que se quedaron sueltas."""
import math, pcbnew
B = pcbnew.LoadBoard("T8Sequencer.kicad_pcb")
FM, TM = pcbnew.FromMM, pcbnew.ToMM
def V(x,y): return pcbnew.VECTOR2I(FM(x), FM(y))
z = list(B.Zones())[0]
fills = {l: z.GetFilledPolysList(l) for l in (pcbnew.F_Cu, pcbnew.B_Cu)}
vias=[t.GetPosition() for t in B.GetTracks() if t.GetClass()=="PCB_VIA" and t.GetNetname()=="/GND"]
tht=[p.GetPosition() for f in B.GetFootprints() for p in f.Pads()
     if p.GetNetname()=="/GND" and p.GetDrillSizeX()>0]
gnd = B.FindNet("/GND")

def libre(ps, x, y, R, idx=-1):
    pts=[(x,y)]+[(x+R*math.cos(a*math.pi/8), y+R*math.sin(a*math.pi/8)) for a in range(16)]
    for px,py in pts:
        if idx>=0:
            if not ps.Contains(V(px,py), idx): return False
        else:
            if not ps.Contains(V(px,py)): return False
    return True

fps = fills[pcbnew.F_Cu]; bps = fills[pcbnew.B_Cu]
puestas=0
for i in range(fps.OutlineCount()):
    if any(fps.Contains(p,i) for p in vias) or any(fps.Contains(p,i) for p in tht):
        continue
    o=fps.Outline(i); bb=o.BBox()
    x0,x1=TM(bb.GetLeft()),TM(bb.GetRight()); y0,y1=TM(bb.GetTop()),TM(bb.GetBottom())
    hecho=False
    for R in (0.60,0.50,0.45,0.40):
        yy=y0
        while yy<=y1 and not hecho:
            xx=x0
            while xx<=x1:
                if libre(fps,xx,yy,R,i) and libre(bps,xx,yy,R):
                    v=pcbnew.PCB_VIA(B); v.SetPosition(V(xx,yy))
                    v.SetViaType(pcbnew.VIATYPE_THROUGH)
                    v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu); v.SetDrill(FM(0.3))
                    try: v.SetWidth(FM(0.6))
                    except TypeError: v.SetWidth(pcbnew.F_Cu,FM(0.6))
                    v.SetNet(gnd); B.Add(v); puestas+=1; hecho=True
                    print("   isla %2d (%.1f x %.1f mm2) cosida en (%.2f, %.2f) con holgura %.2f"%(
                        i,x1-x0,y1-y0,xx,yy,R))
                    break
                xx+=0.25
            yy+=0.25
        if hecho: break
    if not hecho:
        print("   isla %2d x %.1f..%.1f y %.1f..%.1f NO cabe via"%(i,x0,x1,y0,y1))
print("vias anadidas:", puestas)
pcbnew.ZONE_FILLER(B).Fill(B.Zones())
B.Save("T8Sequencer.kicad_pcb")
print("guardado")
