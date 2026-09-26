# -*- coding: utf-8 -*-
"""Genera T8Sequencer.kicad_pcb desde el netlist.

No rutea: coloca los footprints con una distribucion de partida sensata para una
groovebox (fila de 16 pasos con su LED encima, pots arriba, botones de funcion
abajo, el resto en rejilla al fondo) y asigna todas las nets. A partir de aqui
el trabajo es colocacion fina + ruteo a mano en pcbnew.

Uso:  <venv>/python.exe build_pcb.py
"""
import xml.etree.ElementTree as ET
from pathlib import Path
import pcbnew

PROJ = Path(__file__).resolve().parent
PCB = str(PROJ / "T8Sequencer.kicad_pcb")
NET = str(PROJ / "T8Sequencer.xml")
FPBASE = Path(r"C:\Program Files\KiCad\10.0\share\kicad\footprints")

# medidas de la placa (H se recalcula al final segun lo que ocupe de verdad)
W = 290.0
STEP_PITCH = 16.0
STEP_X0 = 15.0

def V(x, y):
    return pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))

# ---------- netlist ----------
root = ET.parse(NET).getroot()
comps = {}
for comp in root.findall(".//comp"):
    comps[comp.get("ref")] = (comp.findtext("value") or "",
                              comp.findtext("footprint") or "")
nets = [(n.get("name"), [(x.get("ref"), x.get("pin")) for x in n.findall("node")])
        for n in root.findall(".//net")]
print("componentes: %d | nets: %d" % (len(comps), len(nets)))

board = pcbnew.CreateEmptyBoard()

def load(fp):
    """Carga un footprint mirando primero las libs del proyecto."""
    lib, name = fp.split(":", 1)
    for base in (PROJ, FPBASE):
        d = base / (lib + ".pretty")
        if not d.is_dir():
            continue
        try:
            f = pcbnew.FootprintLoad(str(d), name)
        except Exception:
            continue
        if f is not None:
            return f
    return None

# ---------- posiciones dirigidas ----------
# los 16 pasos: switch abajo, su LED justo encima
STEPS = ["SW%d" % i for i in range(1, 17)]
LEDS = ["D1", "D2", "D3", "D4", "D5", "D10", "D11", "D12",
        "D6", "D7", "D8", "D9", "D14", "D15", "D16", "D17"]  # orden real de la cadena
FUNC = ["SW17", "SW18", "SW19", "SW20", "SW21", "SW22", "SW23", "SW24"]
POTS = ["RV%d" % i for i in range(1, 11)]

fixed = {}
# franja de panel arriba: pots / LEDs / pasos / funcion
for i, r in enumerate(POTS):
    fixed[r] = (STEP_X0 + i * STEP_PITCH * 1.55, 20.0)
for i, r in enumerate(LEDS):
    fixed[r] = (STEP_X0 + i * STEP_PITCH, 45.0)
for i, r in enumerate(STEPS):
    fixed[r] = (STEP_X0 + i * STEP_PITCH, 62.0)
for i, r in enumerate(FUNC):
    fixed[r] = (STEP_X0 + i * STEP_PITCH, 82.0)

# ---------- colocar ----------
placed, missing, rest = {}, [], []
for ref, (val, fp) in comps.items():
    if not fp or ":" not in fp:
        continue
    foot = load(fp)
    if foot is None:
        missing.append((ref, fp))
        continue
    foot.SetReference(ref)
    foot.SetValue(val)
    board.Add(foot)
    placed[ref] = foot
    if ref not in fixed:
        rest.append(ref)

for ref, (x, y) in fixed.items():
    if ref in placed:
        placed[ref].SetPosition(V(x, y))

# el resto, en rejilla POR DEBAJO de la franja de panel (sin solaparse)
cols, dx, dy, x0, y0 = 11, 25.0, 21.0, 15.0, 105.0
for i, ref in enumerate(sorted(rest)):
    r, c = divmod(i, cols)
    placed[ref].SetPosition(V(x0 + c * dx, y0 + r * dy))
H = y0 + ((len(rest) - 1) // cols) * dy + 20.0
print("resto en rejilla: %d componentes -> altura de placa %.0f mm" % (len(rest), H))

# ---------- nets ----------
assigned = 0
for name, nodes in nets:
    ni = pcbnew.NETINFO_ITEM(board, name)
    board.Add(ni)
    for ref, pin in nodes:
        foot = placed.get(ref)
        if foot is None:
            continue
        pad = foot.FindPadByNumber(pin)
        if pad is not None:
            pad.SetNet(ni)
            assigned += 1

# ---------- contorno ----------
for a, b in (((0, 0), (W, 0)), ((W, 0), (W, H)), ((W, H), (0, H)), ((0, H), (0, 0))):
    seg = pcbnew.PCB_SHAPE(board)
    seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
    seg.SetStart(V(*a)); seg.SetEnd(V(*b))
    seg.SetLayer(pcbnew.Edge_Cuts)
    seg.SetWidth(pcbnew.FromMM(0.1))
    board.Add(seg)

board.Save(PCB)
print("footprints colocados: %d | pads con net: %d" % (len(placed), assigned))
if missing:
    print("SIN FOOTPRINT CARGABLE:")
    for ref, fp in missing:
        print("   %-6s %s" % (ref, fp))
print("guardado en", PCB)
