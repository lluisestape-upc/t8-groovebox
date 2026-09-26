# -*- coding: utf-8 -*-
"""Cose las dos caras del plano de masa con vias, alli donde hay cobre de GND
arriba y abajo y cabe la via con holgura."""
import math, pcbnew
B = pcbnew.LoadBoard("T8Sequencer.kicad_pcb")
FM, TM = pcbnew.FromMM, pcbnew.ToMM
def V(x,y): return pcbnew.VECTOR2I(FM(x), FM(y))

z = list(B.Zones())[0]
fills = {l: z.GetFilledPolysList(l) for l in (pcbnew.F_Cu, pcbnew.B_Cu)}
R = 0.60          # radio libre que exigimos alrededor de la via
gnd = B.FindNet("/GND")

def cabe(x, y):
    pts = [(x, y)] + [(x + R*math.cos(a*math.pi/6), y + R*math.sin(a*math.pi/6))
                      for a in range(12)]
    for ps in fills.values():
        for px, py in pts:
            if not ps.Contains(V(px, py)): return False
    return True

paso = 9.0
n = 0
y = 6.0
while y < 208.0:
    x = 4.0
    while x < 288.0:
        if cabe(x, y):
            v = pcbnew.PCB_VIA(B)
            v.SetPosition(V(x, y)); v.SetViaType(pcbnew.VIATYPE_THROUGH)
            v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            v.SetDrill(FM(0.3))
            try: v.SetWidth(FM(0.6))
            except TypeError: v.SetWidth(pcbnew.F_Cu, FM(0.6))
            v.SetNet(gnd); B.Add(v); n += 1
        x += paso
    y += paso
print("vias de cosido anadidas:", n)
pcbnew.ZONE_FILLER(B).Fill(B.Zones())
B.Save("T8Sequencer.kicad_pcb")
print("guardado")
