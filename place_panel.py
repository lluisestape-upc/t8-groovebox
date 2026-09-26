# -*- coding: utf-8 -*-
"""Coloca el T8Sequencer con criterio de panel de usuario.

Mitad inferior = lo que toca el musico. De arriba abajo:
    botones de funcion + pantalla + encoder
    potenciometros
    LEDs
    pads
Mitad superior = electronica, con los conectores pegados al borde trasero.

No rutea: deja la placa lista para tirar pistas a mano en pcbnew.
Uso:  <venv>/python.exe place_panel.py
"""
import pcbnew

PCB = "T8Sequencer.kicad_pcb"
MM = pcbnew.FromMM
TM = lambda v: v / 1e6

# ------------------------------------------------------------------ geometria
W, H = 290.0, 210.0
MARGIN = 12.0

PAD_X0, PAD_PITCH = 25.0, 16.0          # 16 pads a 16 mm, jugable con el dedo
PAD_Y, LED_Y, POT_Y = 190.0, 172.0, 148.0
FUNC_Y = 126.0                          # fila de PLAY/REC/SHIFT/...
POT_PITCH = 26.0

TOP_STRIP = 30.0                        # franja reservada a conectores
ELEC_BOT = 92.0                         # hasta donde puede bajar la electronica
CLEAR = 1.6

board = pcbnew.LoadBoard(PCB)
fps = {f.GetReference(): f for f in board.GetFootprints()}
occupied = []


def size_of(f):
    bb = f.GetBoundingBox(False, False)
    p = f.GetPosition()
    return (TM(bb.GetWidth()), TM(bb.GetHeight()),
            TM(bb.GetCenter().x - p.x), TM(bb.GetCenter().y - p.y))


def put(ref, cx, cy, rot=0):
    f = fps.get(ref)
    if f is None:
        return
    f.SetOrientationDegrees(rot)        # girar primero
    w, h, ox, oy = size_of(f)           # medir despues
    f.SetPosition(pcbnew.VECTOR2I(MM(cx - ox), MM(cy - oy)))
    occupied.append((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2))


def put_origin(ref, ox_, oy_, rot=0):
    """Coloca por ORIGEN del footprint, no por centro.

    Hace falta para los jacks: su perfil de Edge.Cuts esta referido al origen,
    y ese perfil tiene que caer exactamente sobre el borde de la placa.
    """
    f = fps.get(ref)
    if f is None:
        return
    f.SetOrientationDegrees(rot)
    f.SetPosition(pcbnew.VECTOR2I(MM(ox_), MM(oy_)))
    w, h, dx, dy = size_of(f)
    cx, cy = ox_ + dx, oy_ + dy
    occupied.append((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2))


def free(x0, y0, x1, y1):
    for a, b, c, d in occupied:
        if x0 < c + CLEAR and a < x1 + CLEAR and y0 < d + CLEAR and b < y1 + CLEAR:
            return False
    return True


# ------------------------------------------- 1. panel: pads, LEDs, pots, func
LED_ORDER = ["D1", "D2", "D3", "D4", "D5", "D10", "D11", "D12",
             "D6", "D7", "D8", "D9", "D14", "D15", "D16", "D17"]
FUNC = ["SW17", "SW18", "SW19", "SW20", "SW21", "SW22", "SW23", "SW24"]

for i in range(16):
    x = PAD_X0 + i * PAD_PITCH
    put("SW%d" % (i + 1), x, PAD_Y)
    put(LED_ORDER[i], x, LED_Y)

mid = PAD_X0 + 7.5 * PAD_PITCH
for i in range(10):
    put("RV%d" % (i + 1), mid + (i - 4.5) * POT_PITCH, POT_Y)

for i, ref in enumerate(FUNC):                 # transporte, a la izquierda
    put(ref, PAD_X0 + i * PAD_PITCH, FUNC_Y)

put("U3", 230, 112)                            # pantalla, a la derecha
put("RE1", 175, 126)                           # encoder, junto a la pantalla

# ------------------------------------------------ 2. electronica: anclas fijas
# los jacks de 3,5 mm traen su propio recorte en Edge.Cuts: ese recorte ES el
# canto de la placa, asi que van girados 180 y con el origen en JACK_Y para que
# su perfil caiga justo sobre el borde superior (y=0).
JACK_Y = 4.5
JACK_HALF = 6.5                 # media anchura del recorte
JACKS_X = [62.0, 92.0]          # J2 = MIDI IN, J3 = MIDI OUT

put_origin("J2", JACKS_X[0], JACK_Y, 180)       # MIDI IN,  al canto
put_origin("J3", JACKS_X[1], JACK_Y, 180)       # MIDI OUT, al canto

ANCHORS = [
    ("J1", 30, 10, 0),          # USB-C, pegado al borde trasero
    ("U8", 124, 22, 90),    # 6N138, pegado al MIDI IN
    ("U1", 52, 66, 0),      # ESP32
    ("U7", 142, 52, 90),    # MCP23017 0x20 -> los 16 pads
    ("U10", 142, 70, 90),   # MCP23017 0x21 -> los 8 de funcion
    ("U4", 190, 60, 0),     # mux de los 10 pots
    ("U6", 100, 80, 0),     # CH340C, cerca del USB
    ("U5", 22, 84, 0),      # AMS1117
    ("U2", 218, 62, 0),     # cabecera PCM5102
    ("U9", 232, 62, 0),     # cabecera MAX98357A
    ("U11", 250, 45, 0),    # level shifter de los LEDs
]
for ref, x, y, rot in ANCHORS:
    put(ref, x, y, rot)

# ------------------- 2b. cada condensador, pegado a su integrado -------------
# (destino, red por la que se le busca la patilla de alimentacion)
DESACOPLO = {
    "C1":  ("U6",  "Net-(U6-V3)"),   # red propia del CH340C, obligatoria
    "C20": ("U1",  "/ESP_EN"),       # el de arranque del ESP32
    "C21": ("U1",  "/3.3V"),
    "C22": ("U7",  "/3.3V"),
    "C23": ("U10", "/3.3V"),
    "C29": ("U4",  "/3.3V"),
    "C25": ("U5",  "/3.3V"),         # bulk a la salida del regulador
    "C26": ("U5",  "/+5V"),          # bulk a la entrada
    "C2":  ("J1",  "/+5V"),          # electrolitico de entrada, junto al USB
    "C24": ("U8",  "/+5V"),
    "C27": ("U9",  "/+5V"),
    "C28": ("U9",  "/+5V"),          # bulk del amplificador
    "C30": ("U11", "/+5V"),
}

import math


def pad_xy(ref, net):
    """Posicion de la patilla de `ref` que cuelga de `net`."""
    f = fps.get(ref)
    if f is None:
        return None
    for p in f.Pads():
        if p.GetNetname() == net:
            q = p.GetPosition()
            return TM(q.x), TM(q.y)
    return None


MAX_TOP = 8.0          # mas lejos que esto, un desacoplo ya no desacopla
bottom = []            # ocupacion de la cara inferior


def es_smd(f):
    """True si el componente no tiene ninguna patilla pasante."""
    return all(p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD for p in f.Pads())


# Las patillas pasantes atraviesan la placa, asi que estorban tambien abajo.
# Se miran PAD A PAD, no por contorno: el ESP32 tiene vias pasantes en su pad
# termico, y bloquear sus 48x41 mm enteros dejaria la cara inferior inservible.
pasantes = []
for f in board.GetFootprints():
    for p in f.Pads():
        if p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
            bb = p.GetBoundingBox()
            pasantes.append((TM(bb.GetLeft()), TM(bb.GetTop()),
                             TM(bb.GetRight()), TM(bb.GetBottom())))
print("patillas pasantes que estorban en la cara inferior: %d" % len(pasantes))


def _libre(x0, y0, x1, y1, listas):
    for lst in listas:
        for a, b, c, d in lst:
            if x0 < c + CLEAR and a < x1 + CLEAR and y0 < d + CLEAR and b < y1 + CLEAR:
                return False
    return True


def _anillos(desde, hasta):
    for radio in [r * 0.5 for r in range(desde, hasta)]:
        for k in range(16):
            a = 2 * math.pi * k / 16
            yield radio, math.cos(a), math.sin(a)


def place_near(ref, ax, ay):
    """Lo mas cerca posible de (ax, ay). Si por arriba no cabe cerca y el
    componente es SMD, se pasa a la cara inferior, justo bajo la patilla."""
    f = fps.get(ref)
    w, h, _, _ = size_of(f)

    def dentro(cx, cy):
        return MARGIN < cx < W - MARGIN and 3.0 < cy < ELEC_BOT

    for radio, ca, sa in _anillos(6, int(MAX_TOP * 2) + 1):
        cx, cy = ax + radio * ca, ay + radio * sa
        if dentro(cx, cy) and free(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2):
            put(ref, cx, cy)
            return round(radio, 1), "arriba"

    if es_smd(f):        # solo lo SMD puede irse abajo
        for radio, ca, sa in _anillos(4, 30):
            cx, cy = ax + radio * ca, ay + radio * sa
            if dentro(cx, cy) and _libre(cx - w / 2, cy - h / 2,
                                         cx + w / 2, cy + h / 2,
                                         (bottom, pasantes)):
                f.SetPosition(pcbnew.VECTOR2I(MM(cx), MM(cy)))
                f.Flip(f.GetPosition(), False)
                f.SetPosition(pcbnew.VECTOR2I(MM(cx), MM(cy)))
                bottom.append((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2))
                return round(radio, 1), "ABAJO"

    for radio, ca, sa in _anillos(int(MAX_TOP * 2) + 1, 90):   # pasante: arriba y lejos
        cx, cy = ax + radio * ca, ay + radio * sa
        if dentro(cx, cy) and free(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2):
            put(ref, cx, cy)
            return round(radio, 1), "arriba"
    return None, None


emparejados = []
for cap, (ic, net) in DESACOPLO.items():
    a = pad_xy(ic, net)
    if a is None:
        print("   OJO: no encuentro la patilla %s de %s" % (net, ic))
        continue
    d, cara = place_near(cap, *a)
    emparejados.append((cap, ic, d, cara))
print("condensadores agrupados: %d" % len(emparejados))
for cap, ic, d, cara in sorted(emparejados):
    print("   %-5s -> %-4s  a %4s mm de su patilla  (%s)" % (cap, ic, d, cara))

# a partir de aqui la franja de conectores queda vetada
occupied.append((0, 0, W, TOP_STRIP))

# ------------------- 3. resistencias y sueltos, en los huecos que queden -----
done = {r for r, *_ in ANCHORS} | {"U3", "RE1", "J2", "J3"} | set(FUNC) \
    | set(LED_ORDER) | set(DESACOPLO) \
    | {"SW%d" % i for i in range(1, 17)} | {"RV%d" % i for i in range(1, 11)}
rest = sorted((f for r, f in fps.items() if r not in done),
              key=lambda f: -(size_of(f)[0] * size_of(f)[1]))

# rejilla holgada, para que no queden pegados unos a otros
CELL_W, CELL_H = 16.0, 12.0
cells = []
y = TOP_STRIP + CELL_H / 2
while y + CELL_H / 2 <= ELEC_BOT:
    x = MARGIN + CELL_W / 2
    while x + CELL_W / 2 <= W - MARGIN:
        cells.append((x, y))
        x += CELL_W
    y += CELL_H

pending = []
for f in rest:
    w, h, _, _ = size_of(f)
    for i, (cx, cy) in enumerate(cells):
        if free(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2):
            put(f.GetReference(), cx, cy)
            cells.pop(i)
            break
    else:
        pending.append(f.GetReference())

# ------------------------------------------------------------ 4. contorno
for d in list(board.GetDrawings()):
    if d.GetLayer() == pcbnew.Edge_Cuts:
        board.Remove(d)

# el borde superior se interrumpe en cada jack: ese tramo lo pone el footprint
gaps = sorted((jx - JACK_HALF, jx + JACK_HALF) for jx in JACKS_X)
top = []
cur = 0.0
for a, b in gaps:
    if a > cur:
        top.append((cur, 0, a, 0))
    cur = b
top.append((cur, 0, W, 0))

for x0, y0, x1, y1 in top + [(W, 0, W, H), (W, H, 0, H), (0, H, 0, 0)]:
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(pcbnew.VECTOR2I(MM(x0), MM(y0)))
    s.SetEnd(pcbnew.VECTOR2I(MM(x1), MM(y1)))
    s.SetLayer(pcbnew.Edge_Cuts)
    s.SetWidth(MM(0.1))
    board.Add(s)
print("borde superior en %d tramos, con hueco para %d jacks" % (len(top), len(JACKS_X)))

board.Save(PCB)
print("placa %.0f x %.0f mm" % (W, H))
print("panel:  func y=%.0f | pots y=%.0f | leds y=%.0f | pads y=%.0f"
      % (FUNC_Y, POT_Y, LED_Y, PAD_Y))
print("sin sitio: %s" % (pending if pending else "ninguno"))
