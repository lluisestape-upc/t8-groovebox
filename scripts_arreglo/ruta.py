# -*- coding: utf-8 -*-
import math, pcbnew
B = pcbnew.LoadBoard("T8Sequencer.kicad_pcb")
FM, TM = pcbnew.FromMM, pcbnew.ToMM
def V(x,y): return pcbnew.VECTOR2I(FM(x), FM(y))
F, Bo = pcbnew.F_Cu, pcbnew.B_Cu
CLR = 0.2

def d2seg(px,py,ax,ay,bx,by):
    dx,dy = bx-ax, by-ay
    if dx==0 and dy==0: return math.hypot(px-ax,py-ay)
    t = max(0.0, min(1.0, ((px-ax)*dx+(py-ay)*dy)/(dx*dx+dy*dy)))
    return math.hypot(px-(ax+t*dx), py-(ay+t*dy))
def seg2seg(a,b,c,d):
    (ax,ay),(bx,by),(cx,cy),(dx_,dy_) = a,b,c,d
    d1=(dx_-cx)*(ay-cy)-(dy_-cy)*(ax-cx); d2=(dx_-cx)*(by-cy)-(dy_-cy)*(bx-cx)
    d3=(bx-ax)*(cy-ay)-(by-ay)*(cx-ax);  d4=(bx-ax)*(dy_-ay)-(by-ay)*(dx_-ax)
    if ((d1>0)!=(d2>0)) and ((d3>0)!=(d4>0)): return 0.0
    return min(d2seg(ax,ay,cx,cy,dx_,dy_), d2seg(bx,by,cx,cy,dx_,dy_),
               d2seg(cx,cy,ax,ay,bx,by), d2seg(dx_,dy_,ax,ay,bx,by))

def obstaculos(layer, net):
    o=[]
    for t in B.GetTracks():
        if t.GetNetname()==net: continue
        if t.GetClass()=="PCB_VIA":
            p=t.GetPosition(); o.append(((TM(p.x),TM(p.y)),(TM(p.x),TM(p.y)),0.3))
        elif t.GetLayer()==layer:
            a,b=t.GetStart(),t.GetEnd()
            o.append(((TM(a.x),TM(a.y)),(TM(b.x),TM(b.y)),TM(t.GetWidth())/2.0))
    for f in B.GetFootprints():
        for p in f.Pads():
            if p.GetNetname()==net: continue
            if not (p.IsOnLayer(layer) or p.GetDrillSizeX()>0): continue
            pp=p.GetPosition(); s=p.GetSize()
            r=max(TM(s.x),TM(s.y))/2.0
            o.append(((TM(pp.x),TM(pp.y)),(TM(pp.x),TM(pp.y)),r))
    return o

def ok_seg(a,b,obs,half):
    for (c,d,r) in obs:
        if seg2seg(a,b,c,d) < half + r + CLR: return False
    return True

def ok_via(x,y,obs,huecos):
    for (c,d,r) in obs:
        if d2seg(x,y,c[0],c[1],d[0],d[1]) < 0.3 + r + CLR: return False
    for hx,hy in huecos:
        if math.hypot(x-hx,y-hy) < 0.85: return False
    return True

huecos=[]
for t in B.GetTracks():
    if t.GetClass()=="PCB_VIA":
        p=t.GetPosition(); huecos.append((TM(p.x),TM(p.y)))
for f in B.GetFootprints():
    for p in f.Pads():
        if p.GetDrillSizeX()>0:
            pp=p.GetPosition(); huecos.append((TM(pp.x),TM(pp.y)))

def add_trk(a,b,layer,net,w=0.2):
    t=pcbnew.PCB_TRACK(B); t.SetStart(V(*a)); t.SetEnd(V(*b))
    t.SetLayer(layer); t.SetWidth(FM(w)); t.SetNet(B.FindNet(net)); B.Add(t)
def add_via(x,y,net):
    v=pcbnew.PCB_VIA(B); v.SetPosition(V(x,y)); v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetLayerPair(F,Bo); v.SetDrill(FM(0.3))
    try: v.SetWidth(FM(0.6))
    except TypeError: v.SetWidth(F,FM(0.6))
    v.SetNet(B.FindNet(net)); B.Add(v)

U3 = [f for f in B.GetFootprints() if f.GetReference()=="U3"][0]
PAD = {p.GetNumber(): (TM(p.GetPosition().x), TM(p.GetPosition().y)) for p in U3.Pads()}
TAREA = [("2","/3.3V"),("3","/DISP_SCK"),("4","/DISP_MOSI"),
         ("5","/RES"),("6","/DC"),("7","/TFT_CS")]

nuevos = []
for pin, net in TAREA:
    destino = PAD[pin]
    obsF = obstaculos(F, net); obsB = obstaculos(Bo, net)
    cand = []
    for t in B.GetTracks():
        if t.GetNetname()!=net or t.GetClass()=="PCB_VIA": continue
        a,b = t.GetStart(), t.GetEnd()
        ax,ay,bx,by = TM(a.x),TM(a.y),TM(b.x),TM(b.y)
        L = math.hypot(bx-ax,by-ay)
        if L==0: continue
        n = max(2,int(L/0.25))
        for i in range(n+1):
            s=i/float(n); x,y = ax+s*(bx-ax), ay+s*(by-ay)
            if 175 < x < 196 and 85 < y < 112:
                cand.append((math.hypot(x-destino[0],y-destino[1]), x, y))
    cand.sort()
    puesto=False
    for _,x,y in cand:
        if not ok_via(x,y,obsF,huecos): continue
        if not ok_via(x,y,obsB,[]): continue
        if not ok_seg((x,y),destino,obsB,0.1): continue
        if any(seg2seg((x,y),destino,p,q)<0.4 for p,q in nuevos): continue
        add_via(x,y,net); add_trk((x,y),destino,Bo,net)
        huecos.append((x,y)); nuevos.append(((x,y),destino))
        print("  %-12s via en (%.2f, %.2f) -> pin %s  (%.1f mm por B.Cu)"%(
              net,x,y,pin,math.hypot(x-destino[0],y-destino[1])))
        puesto=True; break
    if not puesto: print("  %-12s SIN RUTA"%net)

# BLK (pin 8) al mismo 3.3V, rodeando la tira por la derecha
p8, p2 = PAD["8"], PAD["2"]
via_blk = [(219.0,p8[1]),(219.0,p2[1])]
obsB = obstaculos(Bo,"/3.3V")
camino=[p8]+via_blk+[p2]
if all(ok_seg(camino[i],camino[i+1],obsB,0.1) for i in range(len(camino)-1)):
    for i in range(len(camino)-1): add_trk(camino[i],camino[i+1],Bo,"/3.3V")
    print("  /3.3V        BLK (pin 8) unido a VCC (pin 2) por B.Cu rodeando la tira")
else:
    print("  BLK SIN RUTA")

pcbnew.ZONE_FILLER(B).Fill(B.Zones())
B.Save("T8Sequencer.kicad_pcb")
print("guardado")
