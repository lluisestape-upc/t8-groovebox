# -*- coding: utf-8 -*-
"""Arreglo 1: redes en pads duplicados, redes en pistas huerfanas, contorno cerrado,
regla de taladro minimo."""
import pcbnew, collections
B = pcbnew.LoadBoard("T8Sequencer.kicad_pcb")
TM, FM = pcbnew.ToMM, pcbnew.FromMM

# --- A. propagar la red a los pads que comparten numero ----------------------
fix = 0
for f in B.GetFootprints():
    byn = collections.defaultdict(list)
    for p in f.Pads():
        byn[p.GetNumber()].append(p)
    for num, ps in byn.items():
        nets = {p.GetNetCode() for p in ps if p.GetNetCode() != 0}
        if len(nets) == 1 and any(p.GetNetCode() == 0 for p in ps):
            nc = nets.pop()
            net = B.FindNet(nc)
            for p in ps:
                if p.GetNetCode() == 0:
                    p.SetNet(net); fix += 1
print("A) pads sin red corregidos:", fix)

# --- B. propagar la red a pistas/vias sin red --------------------------------
B.BuildConnectivity()
pads = [(f.GetReference(), p) for f in B.GetFootprints() for p in f.Pads()]

def key(pt): return (pt.x, pt.y)
par = {}
def find(a):
    par.setdefault(a, a)
    while par[a] != a:
        par[a] = par[par[a]]; a = par[a]
    return a
def uni(a, b):
    ra, rb = find(a), find(b)
    if ra != rb: par[ra] = rb

orph = [t for t in B.GetTracks() if t.GetNetCode() == 0]
for t in orph: uni(key(t.GetStart()), key(t.GetEnd()))
groups = collections.defaultdict(list)
for t in orph: groups[find(key(t.GetStart()))].append(t)

asign = 0; sueltas = []
for g, ts in groups.items():
    nets = set()
    for t in ts:
        lay = t.GetLayer() if t.GetClass() != "PCB_VIA" else pcbnew.F_Cu
        for pt in (t.GetStart(), t.GetEnd()):
            for ref, p in pads:
                if p.GetNetCode() and p.IsOnLayer(lay) and p.HitTest(pt):
                    nets.add(p.GetNetCode())
    if len(nets) == 1:
        net = B.FindNet(nets.pop())
        for t in ts: t.SetNet(net); asign += 1
        print("   cadena de %2d items -> %s" % (len(ts), net.GetNetname()))
    else:
        sueltas.append((len(ts), sorted(B.FindNet(n).GetNetname() for n in nets)))
print("B) items de cobre con red asignada:", asign, " cadenas ambiguas/sueltas:", len(sueltas))
for s in sueltas: print("   sin resolver:", s)

# --- C. cerrar el contorno ----------------------------------------------------
def seg(x1, y1, x2, y2):
    s = pcbnew.PCB_SHAPE(B)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetLayer(pcbnew.Edge_Cuts)
    s.SetStart(pcbnew.VECTOR2I(FM(x1), FM(y1)))
    s.SetEnd(pcbnew.VECTOR2I(FM(x2), FM(y2)))
    s.SetWidth(FM(0.1))
    B.Add(s)
seg(55.5, 0.0, 55.5, 7.0)
seg(98.5, 0.0, 98.5, 7.0)
print("C) contorno cerrado con 2 tramos verticales (rebaje de 7 mm para los jacks)")

# --- D. taladro minimo a 0.2 mm (vias termicas del ESP32) ---------------------
ds = B.GetDesignSettings()
ds.m_MinThroughDrill = FM(0.2)
print("D) taladro minimo 0.3 -> 0.2 mm")

B.Save("T8Sequencer.kicad_pcb")
print("guardado")
