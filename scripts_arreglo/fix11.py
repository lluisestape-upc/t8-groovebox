# -*- coding: utf-8 -*-
"""Anade 6 agujeros M3 en sitios donde no estorban."""
import pcbnew
B = pcbnew.LoadBoard("T8Sequencer.kicad_pcb")
FM, TM = pcbnew.FromMM, pcbnew.ToMM
LIB = r"C:/Program Files/KiCad/10.0/share/kicad/footprints/MountingHole.pretty"

copper = []
for f in B.GetFootprints():
    for p in f.Pads(): copper.append((TM(p.GetPosition().x), TM(p.GetPosition().y)))
for t in B.GetTracks():
    if t.GetClass() == "PCB_VIA":
        copper.append((TM(t.GetPosition().x), TM(t.GetPosition().y)))
    else:
        copper.append((TM(t.GetStart().x), TM(t.GetStart().y)))
        copper.append((TM(t.GetEnd().x), TM(t.GetEnd().y)))

MARGEN = 4.0   # mm libres alrededor del centro del agujero
def libre(x, y):
    return all((cx-x)**2 + (cy-y)**2 > MARGEN**2 for cx, cy in copper)

OBJETIVO = [(6.0,203.0),(145.0,203.0),(284.0,203.0),(6.0,12.0),(145.0,12.0),(284.0,12.0)]
n = 0
for k, (ox, oy) in enumerate(OBJETIVO, 1):
    mejor = None
    for dx in range(0, 61):
        for sx in (1, -1):
            for dy in range(0, 61):
                for sy in (1, -1):
                    x, y = ox + sx*dx*0.5, oy + sy*dy*0.5
                    if not (5.0 < x < 285.0 and 5.0 < y < 205.0): continue
                    if libre(x, y):
                        mejor = (x, y); break
                if mejor: break
            if mejor: break
        if mejor: break
    if not mejor:
        print("  H%d: no hay sitio cerca de (%.0f,%.0f)" % (k, ox, oy)); continue
    fp = pcbnew.FootprintLoad(LIB, "MountingHole_3.2mm_M3")
    fp.SetPosition(pcbnew.VECTOR2I(FM(mejor[0]), FM(mejor[1])))
    fp.SetReference("H%d" % k)
    B.Add(fp); n += 1
    print("  H%d en (%.1f, %.1f)%s" % (k, mejor[0], mejor[1],
          "" if (abs(mejor[0]-ox)<0.01 and abs(mejor[1]-oy)<0.01) else "  (movido del sitio ideal)"))
print("agujeros M3 anadidos:", n)
pcbnew.ZONE_FILLER(B).Fill(B.Zones())
B.Save("T8Sequencer.kicad_pcb")
print("guardado")
