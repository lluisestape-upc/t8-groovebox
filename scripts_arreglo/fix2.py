# -*- coding: utf-8 -*-
"""Arreglo 2: desviar +5V, CC1 y CC2 fuera del rebaje de los jacks.
Bajan por vias al lado B, cruzan por y=13..14 entre las dos filas de pines de
los jacks, y vuelven a subir pasado x=98.5."""
import pcbnew
B = pcbnew.LoadBoard("T8Sequencer.kicad_pcb")
FM, TM = pcbnew.FromMM, pcbnew.ToMM
V = lambda x, y: pcbnew.VECTOR2I(FM(x), FM(y))

def net(n): 
    nn = B.FindNet(n); assert nn, n; return nn

def trk(x1, y1, x2, y2, layer, n, w=0.2):
    t = pcbnew.PCB_TRACK(B)
    t.SetStart(V(x1, y1)); t.SetEnd(V(x2, y2))
    t.SetLayer(layer); t.SetWidth(FM(w)); t.SetNet(n)
    B.Add(t); return t

def via(x, y, n):
    v = pcbnew.PCB_VIA(B)
    v.SetPosition(V(x, y))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetDrill(FM(0.3))
    try: v.SetWidth(FM(0.6))
    except TypeError: v.SetWidth(pcbnew.F_Cu, FM(0.6))
    v.SetNet(n); B.Add(v); return v

def path(pts, layer, n):
    for i in range(len(pts) - 1):
        trk(pts[i][0], pts[i][1], pts[i+1][0], pts[i+1][1], layer, n)

# --- 1. recortar las tres pistas originales ----------------------------------
# (net, y original, x donde se corta por la izquierda, x por la derecha)
CUT = {
    "Net-(J1-CC1)": (2.0, 50.0, 101.1),
    "/+5V":         (2.5, 45.5, 102.2),
    "Net-(J1-CC2)": (2.9, 41.0, 103.0),
}
F = pcbnew.F_Cu; Bo = pcbnew.B_Cu
for t in list(B.GetTracks()):
    if t.GetClass() == "PCB_VIA": continue
    nn = t.GetNetname()
    if nn not in CUT or t.GetLayer() != F: continue
    y0, xl, xr = CUT[nn]
    a, b = t.GetStart(), t.GetEnd()
    if abs(TM(a.y) - y0) > 0.01 or abs(TM(b.y) - y0) > 0.01: continue
    x1, x2 = sorted((TM(a.x), TM(b.x)))
    if x2 < xl or x1 > xr: continue
    B.Remove(t)
    if x1 < xl: trk(x1, y0, xl, y0, F, net(nn))
    if x2 > xr: trk(xr, y0, x2, y0, F, net(nn))
    print("recortada %-14s y=%.1f  %.2f..%.2f -> extremos %.2f / %.2f" % (nn, y0, x1, x2, xl, xr))

# --- 2. el desvio -------------------------------------------------------------
# net: (bajada izq, carril B.Cu, subida der)
DET = {
    "Net-(J1-CC1)": dict(y0=2.0, lx=50.0, lvia=(52.5, 4.2), lane=13.0,
                         rvia=(99.5, 3.6), rx=101.1,
                         lin=[(50.0,2.0),(51.5,4.2),(52.5,4.2)],
                         rout=[(99.5,3.6),(101.1,2.0)]),
    "/+5V":         dict(y0=2.5, lx=45.5, lvia=(48.5, 5.2), lane=13.5,
                         rvia=(100.5, 5.0), rx=102.2,
                         lin=[(45.5,2.5),(47.5,5.2),(48.5,5.2)],
                         rout=[(100.5,5.0),(102.2,2.5)]),
    "Net-(J1-CC2)": dict(y0=2.9, lx=41.0, lvia=(44.0, 6.2), lane=14.0,
                         rvia=(101.5, 6.4), rx=103.0,
                         lin=[(41.0,2.9),(43.0,6.2),(44.0,6.2)],
                         rout=[(101.5,6.4),(103.0,2.9)]),
}
for nn, d in DET.items():
    n = net(nn)
    path(d["lin"], F, n)                                   # bajada en cara sup.
    via(d["lvia"][0], d["lvia"][1], n)
    trk(d["lvia"][0], d["lvia"][1], d["lvia"][0], d["lane"], Bo, n)   # vertical izq
    trk(d["lvia"][0], d["lane"], d["rvia"][0], d["lane"], Bo, n)      # carril
    trk(d["rvia"][0], d["lane"], d["rvia"][0], d["rvia"][1], Bo, n)   # vertical der
    via(d["rvia"][0], d["rvia"][1], n)
    path(d["rout"], F, n)
    print("desviada %-14s carril B.Cu y=%.1f  x %.1f -> %.1f"
          % (nn, d["lane"], d["lvia"][0], d["rvia"][0]))

B.Save("T8Sequencer.kicad_pcb")
print("guardado")
