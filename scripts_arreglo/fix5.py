# -*- coding: utf-8 -*-
"""Arreglo 5: unir los pads que comparten numero dentro de cada pulsador y
anadir plano de masa en las dos caras."""
import pcbnew, collections
B = pcbnew.LoadBoard("T8Sequencer.kicad_pcb")
FM, TM = pcbnew.FromMM, pcbnew.ToMM
def V(x,y): return pcbnew.VECTOR2I(FM(x), FM(y))

# --- 1. puentes dentro de los pulsadores -------------------------------------
n=0
for f in B.GetFootprints():
    if not f.GetReference().startswith("SW"): continue
    byn=collections.defaultdict(list)
    for p in f.Pads(): byn[p.GetNumber()].append(p)
    for num, ps in byn.items():
        if len(ps)!=2: continue
        a,b=ps[0].GetPosition(), ps[1].GetPosition()
        t=pcbnew.PCB_TRACK(B); t.SetStart(a); t.SetEnd(b)
        t.SetLayer(pcbnew.F_Cu); t.SetWidth(FM(0.4)); t.SetNet(ps[0].GetNet())
        B.Add(t); n+=1
print("1) puentes entre pads gemelos:", n)

# --- 2. plano de masa ---------------------------------------------------------
gnd = B.FindNet("/GND")
z = pcbnew.ZONE(B)
ls = pcbnew.LSET()
ls.AddLayer(pcbnew.F_Cu); ls.AddLayer(pcbnew.B_Cu)
z.SetLayerSet(ls)
z.SetNet(gnd)
z.SetAssignedPriority(0)
z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
z.SetLocalClearance(FM(0.25))
z.SetMinThickness(FM(0.25))
z.SetThermalReliefGap(FM(0.35))
z.SetThermalReliefSpokeWidth(FM(0.6))
o = z.Outline(); o.NewOutline()
for x,y in ((-2,-2),(292,-2),(292,212),(-2,212)):
    o.Append(FM(x), FM(y))
B.Add(z)
print("2) zona GND creada en F.Cu + B.Cu")

filler = pcbnew.ZONE_FILLER(B)
ok = filler.Fill(B.Zones())
print("   relleno:", ok, " area rellenada F.Cu:",
      round(TM(TM(z.GetFilledArea())),1), "mm2 aprox")

B.Save("T8Sequencer.kicad_pcb")
print("guardado")
