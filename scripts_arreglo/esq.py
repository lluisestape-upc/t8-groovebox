# -*- coding: utf-8 -*-
"""Esquematico: U3 pasa de la pantalla de cable plano (7 pines sin numerar) a
un modulo ST7789 de 2,4 pulgadas con tira de 8 pines."""
import io, re, uuid

PINES = [(1,"GND","GND"), (2,"VCC","3.3V"), (3,"SCL","DISP_SCK"), (4,"SDA","DISP_MOSI"),
         (5,"RES","RES"), (6,"DC","DC"), (7,"CS","TFT_CS"), (8,"BLK","3.3V")]
FP = "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical"
DESC = ("Modulo breakout ST7789 240x320 de 2,4 pulgadas, tira de 8 pines "
        "GND-VCC-SCL-SDA-RES-DC-CS-BLK. BLK (retroiluminacion) atado a 3,3 V.")

def cuerpo(nombre):
    t = '\t(symbol "%s"\n' % nombre
    t += ('\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n'
          '\t\t(in_pos_files yes)\n\t\t(duplicate_pin_numbers_are_jumpers no)\n')
    def prop(n, v, y, hide=False):
        h = "\n\t\t\t(hide yes)" if hide else ""
        return ('\t\t(property "%s" "%s"\n\t\t\t(at 0 %s 0)%s\n\t\t\t(show_name no)\n'
                '\t\t\t(do_not_autoplace no)\n\t\t\t(effects (font (size 1.27 1.27)))\n\t\t)\n'
                % (n, v, y, h))
    t += prop("Reference", "U", 12.7)
    t += prop("Value", "ST7789 2.4in modulo", -12.7)
    t += prop("Footprint", FP, 0, True)
    t += prop("Datasheet", "", 0, True)
    t += prop("Description", DESC, 0, True)
    base = nombre.split(":")[-1]
    t += ('\t\t(symbol "%s_0_1"\n\t\t\t(rectangle\n\t\t\t\t(start -6.35 10.16)\n'
          '\t\t\t\t(end 6.35 -10.16)\n\t\t\t\t(stroke (width 0) (type default))\n'
          '\t\t\t\t(fill (type none))\n\t\t\t)\n\t\t)\n' % base)
    t += '\t\t(symbol "%s_1_1"\n' % base
    for num, nom, _ in PINES:
        y = 8.89 - (num-1)*2.54
        t += ('\t\t\t(pin passive line\n\t\t\t\t(at -8.89 %s 0)\n\t\t\t\t(length 2.54)\n'
              '\t\t\t\t(name "%s" (effects (font (size 1.27 1.27))))\n'
              '\t\t\t\t(number "%d" (effects (font (size 1.27 1.27))))\n\t\t\t)\n'
              % (y, nom, num))
    t += '\t\t)\n\t)\n'
    return t

# --- 1. la libreria -----------------------------------------------------------
P = r"C:/Users/luigi/Documents/Lluis.kicad_sym"
s = io.open(P, encoding="utf-8").read()
if '(symbol "ST7789_Modulo"' not in s:
    k = s.rstrip().rfind(")")
    s = s.rstrip()[:k] + cuerpo("ST7789_Modulo") + ")\n"
    io.open(P, "w", encoding="utf-8").write(s)
    print("1) simbolo ST7789_Modulo anadido a Lluis.kicad_sym")

# --- 2. el esquematico --------------------------------------------------------
P2 = "T8Sequencer.kicad_sch"
t = io.open(P2, encoding="utf-8").read()

def bloques(src, op):
    out, i = [], 0
    while True:
        i = src.find(op, i)
        if i < 0: break
        d, j = 0, i
        while j < len(src):
            c = src[j]
            if c == '"':
                j += 1
                while j < len(src) and not (src[j] == '"' and src[j-1] != chr(92)): j += 1
            elif c == "(": d += 1
            elif c == ")":
                d -= 1
                if d == 0: out.append((i, j+1)); break
            j += 1
        i = j + 1
    return out

# 2a. cachear el simbolo
if 'Lluis:ST7789_Modulo' not in t:
    anc = t.find("\n", t.find("(lib_symbols"))
    t = t[:anc+1] + cuerpo("Lluis:ST7789_Modulo") + t[anc+1:]
    print("2) simbolo cacheado en lib_symbols")

# 2b. quitar las 7 etiquetas viejas
VIEJAS = {(93.98, y) for y in (57.15, 59.69, 62.23, 64.77, 67.31, 69.85, 72.39)}
rm = []
for a, b in bloques(t, '(label "'):
    m = re.search(r'\(at ([\d.-]+) ([\d.-]+)', t[a:b])
    if m and (round(float(m.group(1)), 2), round(float(m.group(2)), 2)) in VIEJAS:
        rm.append((a, b))
for a, b in sorted(rm, reverse=True): t = t[:a] + t[b:]
print("3) etiquetas viejas del display eliminadas:", len(rm))

# 2c. sustituir el bloque de U3
obj = None
for a, b in bloques(t, "(symbol (lib_id "):
    if re.search(r'\(reference "U3"', t[a:b]): obj = (a, b); break
OX, OY = 102.87, 64.77
def prop(n, v, x, y, hide=False):
    h = " (hide yes)" if hide else ""
    return ('(property "%s" "%s" (at %s %s 0)%s (show_name no) (do_not_autoplace no) '
            '(effects (font (size 1.27 1.27)))) ' % (n, v, x, y, h))
sym = ('(symbol (lib_id "Lluis:ST7789_Modulo") (at %s %s 0) (unit 1) (body_style 1) '
       '(exclude_from_sim no) (in_bom yes) (on_board yes) (in_pos_files yes) (dnp no) '
       '(uuid "%s") ' % (OX, OY, uuid.uuid4()))
sym += prop("Reference", "U3", OX, OY - 12.7)
sym += prop("Value", "ST7789 2.4in modulo", OX, OY + 12.7)
sym += prop("Footprint", FP, OX, OY, True)
sym += prop("Datasheet", "", OX, OY, True)
sym += prop("Description", DESC, OX, OY, True)
sym += " ".join('(pin "%d" (uuid "%s"))' % (n, uuid.uuid4()) for n, _, _ in PINES)
sym += ('(instances (project "T8Sequencer" (path "/70abb8ec-1cb2-48c9-a7e6-7037db462aac" '
        '(reference "U3") (unit 1)))))')
t = t[:obj[0]] + sym + t[obj[1]:]
print("4) U3 sustituido por el modulo de 8 pines")

# 2d. etiquetas nuevas
nuevas = ""
for num, nom, net in PINES:
    y = OY - (8.89 - (num-1)*2.54)
    nuevas += ('\n(label "%s" (at %s %s 0) (effects (font (size 1.27 1.27)) '
               '(justify right bottom)) (uuid "%s"))' % (net, OX - 8.89, round(y, 2), uuid.uuid4()))
    print("   pin %d %-4s -> %s en (%.2f, %.2f)" % (num, nom, net, OX - 8.89, y))
t = t.rstrip()
assert t.endswith(")")
t = t[:-1] + nuevas + "\n)\n"
io.open(P2, "w", encoding="utf-8").write(t)
print("esquematico guardado")
