# -*- coding: utf-8 -*-
import pcbnew, collections
B = pcbnew.LoadBoard("T8Sequencer.kicad_pcb")
FM, TM = pcbnew.FromMM, pcbnew.ToMM
def V(x,y): return pcbnew.VECTOR2I(FM(x), FM(y))
def near(p,x,y,tol=0.02): return abs(TM(p.x)-x)<tol and abs(TM(p.y)-y)<tol

# --- 1. quitar los dos tramos GND que chocan con USB_D- (el plano ya une) ----
DEL=[((31.750,10.000),(33.700,10.350)),((33.700,10.350),(34.320,8.300))]
rm=[t for t in B.GetTracks() if t.GetClass()!="PCB_VIA" and t.GetNetname()=="/GND"
    and any((near(t.GetStart(),*a) and near(t.GetEnd(),*b)) or
            (near(t.GetStart(),*b) and near(t.GetEnd(),*a)) for a,b in DEL)]
for t in rm: B.Remove(t)
print("1) tramos GND que cruzaban USB_D- eliminados:", len(rm))

# --- 2. separar el retorno de +5V de la bajada de CC1 -------------------------
n=0
for t in B.GetTracks():
    if t.GetNetname()!="/+5V": continue
    if t.GetClass()=="PCB_VIA":
        p=t.GetPosition()
        if near(p,100.0,5.0): t.SetPosition(V(100.35,5.0)); n+=1
        continue
    for setter,getter in ((t.SetStart,t.GetStart),(t.SetEnd,t.GetEnd)):
        p=getter()
        if abs(TM(p.x)-100.0)<0.02 and 3.0<TM(p.y)<15.0:
            setter(V(100.35,TM(p.y))); n+=1
print("2) retorno de +5V separado:", n, "extremos")

# --- 3. el puente de SW4 pasa a la cara inferior (cruzaba una pista de GND) --
n=0
for t in B.GetTracks():
    if t.GetClass()=="PCB_VIA" or t.GetNetname()!="/SEQ_4": continue
    if abs(TM(t.GetLength())-6.5)<0.01 and t.GetLayer()==pcbnew.F_Cu:
        t.SetLayer(pcbnew.B_Cu); n+=1
print("3) puente de SW4 movido a B.Cu:", n)

# --- 4. puente del tab de U5 (pin 2 duplicado en el SOT-223) ----------------
n=0
for f in B.GetFootprints():
    if f.GetReference().startswith("SW"): continue
    byn=collections.defaultdict(list)
    for p in f.Pads(): byn[p.GetNumber()].append(p)
    for num, ps in byn.items():
        if len(ps)!=2 or not num: continue
        a,b=ps[0].GetPosition(), ps[1].GetPosition()
        d=((TM(a.x)-TM(b.x))**2+(TM(a.y)-TM(b.y))**2)**0.5
        if d>8: continue
        t=pcbnew.PCB_TRACK(B); t.SetStart(a); t.SetEnd(b)
        t.SetLayer(pcbnew.F_Cu); t.SetWidth(FM(0.4)); t.SetNet(ps[0].GetNet())
        B.Add(t); n+=1
        print("   puente %s pad %s (%.2f,%.2f)-(%.2f,%.2f)"%(f.GetReference(),num,
              TM(a.x),TM(a.y),TM(b.x),TM(b.y)))
print("4) puentes de pads gemelos fuera de los pulsadores:", n)

# --- 5. A8/B8: conexion maciza al plano (son pads estrechos) ----------------
j1=B.FindFootprintByReference("J1"); n=0
for p in j1.Pads():
    if p.GetNumber() in ("A8","B8"):
        p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL); n+=1
print("5) pads A8/B8 con conexion maciza al plano:", n)

filler = pcbnew.ZONE_FILLER(B); filler.Fill(B.Zones())
B.Save("T8Sequencer.kicad_pcb")
print("guardado")
