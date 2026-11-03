#!/usr/bin/env python3
"""Tablero ArgOS para Turing Smart Screen 3.5" Rev A (480x320 horizontal)."""
import os, sys, json, time, shutil, subprocess, logging, datetime as dt
from zoneinfo import ZoneInfo
import psutil
from PIL import Image, ImageDraw, ImageFont, ImageChops

sys.path.insert(0, "/opt/turing-smart-screen")
from library.lcd.lcd_comm_rev_a import LcdCommRevA
from library.lcd.lcd_comm import Orientation

BASE = os.path.dirname(os.path.abspath(__file__))
W, H, S = 480, 320, 2
BRILLO = 25
FAST, SLOW = 5, 45
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("argos-screen")

BG = (10, 14, 24); C = (0, 220, 170); R = (255, 80, 80); G = (140, 150, 170)
WT = (230, 235, 245); Y = (255, 190, 70); OFF = (90, 100, 120)
_fc = {}
def F(sz, b=False):
    k = (sz, b)
    if k not in _fc:
        p = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono%s.ttf" % ("-Bold" if b else "")
        _fc[k] = ImageFont.truetype(p, sz * S)
    return _fc[k]

def sh(cmd, t=10):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=t)
        return r.returncode, r.stdout.strip()
    except Exception as e:
        return 1, str(e)

# ---------- datos ----------
class Datos:
    def __init__(self):
        self.slow = {}; self.t_slow = 0
        self.net_prev = None
        psutil.cpu_percent(None)

    def rapido(self):
        d = {}
        d["cpu"] = round(psutil.cpu_percent(None))
        d["ram"] = round(psutil.virtual_memory().percent)
        try:
            t = psutil.sensors_temperatures().get("coretemp", [])
            pk = [x.current for x in t if x.label.startswith("Package")] or [x.current for x in t]
            d["temp"] = round(max(pk)) if pk else None
        except Exception:
            d["temp"] = None
        du = shutil.disk_usage("/")
        d["disk_u"], d["disk_t"] = du.used / 2**30, du.total / 2**30
        d["disk_p"] = du.used / du.total * 100
        n = psutil.net_io_counters(pernic=True).get("eno1")
        now = time.time()
        if n and self.net_prev:
            dtm = now - self.net_prev[0]
            d["up"] = (n.bytes_sent - self.net_prev[1]) / dtm / 1e6
            d["down"] = (n.bytes_recv - self.net_prev[2]) / dtm / 1e6
        else:
            d["up"] = d["down"] = 0.0
        if n: self.net_prev = (now, n.bytes_sent, n.bytes_recv)
        d["uptime_d"] = int((time.time() - psutil.boot_time()) // 86400)
        d["load"] = os.getloadavg()[0]
        return d

    def lento(self):
        if time.time() - self.t_slow < SLOW and self.slow:
            return self.slow
        s = {}
        rc, o = sh(["docker", "inspect", "-f", "{{.State.Running}}", "argos-oracle"])
        s["oracle"] = (rc == 0 and o == "true")
        rc, o = sh(["docker", "inspect", "-f", "{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{end}}", "argos-kuma"])
        kuma_ok = rc == 0 and o.startswith("running") and "unhealthy" not in o
        s["kuma_ok"] = kuma_ok; s["kuma"] = "caído" if not kuma_ok else "activo"
        if kuma_ok:
            q = ("select count(*), coalesce(sum(h.status=1),0) from monitor m join heartbeat h on h.id="
                 "(select id from heartbeat where monitor_id=m.id order by id desc limit 1) where m.active=1;")
            rc, o = sh(["docker", "exec", "argos-kuma", "sqlite3", "-readonly", "/app/data/kuma.db", q])
            try:
                tot, up = [int(x) for x in o.split("|")]
                s["kuma"] = f"{up}/{tot} OK" if up == tot else f"{up}/{tot}"
                s["kuma_ok"] = up == tot; s["kuma_down"] = tot - up
            except Exception:
                pass
        rc, o = sh(["tailscale", "status", "--json"])
        try: s["ts"] = json.loads(o).get("BackendState") == "Running"
        except Exception: s["ts"] = False
        rc, o = sh(["ollama", "ps"])
        lines = [l for l in o.splitlines()[1:] if l.strip()] if rc == 0 else []
        s["ollama_ok"] = rc == 0
        s["ollama_carga"] = bool(lines)
        if lines: s["ollama"] = lines[0].split()[0]
        elif rc == 0:
            rc2, o2 = sh(["ollama", "list"])
            n = len([l for l in o2.splitlines()[1:] if l.strip()]) if rc2 == 0 else 0
            s["ollama"] = f"{n} modelo" + ("" if n == 1 else "s")
        else: s["ollama"] = "error"
        rc, o = sh(["systemctl", "is-active", "argos-obsidian.service"])
        s["obs"] = o == "active"
        rc, o = sh(["systemctl", "show", "argos-backup.service", "--timestamp=unix",
                    "-p", "Result,ExecMainStatus,ExecMainExitTimestamp,ActiveState"])
        p = dict(l.split("=", 1) for l in o.splitlines() if "=" in l)
        ts = p.get("ExecMainExitTimestamp", "").lstrip("@")
        s["bk_activo"] = p.get("ActiveState") == "activating"
        s["bk_ok"] = p.get("Result") == "success" and p.get("ExecMainStatus") == "0"
        s["bk_ts"] = float(ts) if ts.replace(".", "").isdigit() else None
        rc, o = sh(["systemctl", "show", "argos-backup.timer", "--timestamp=unix", "-p", "NextElapseUSecRealtime"])
        v = o.split("=", 1)[-1].lstrip("@")
        s["bk_next"] = float(v) if v.replace(".", "").isdigit() else None
        rc, o = sh(["ping", "-c1", "-W2", "1.1.1.1"], 5)
        s["ping"] = None
        if rc == 0 and "time=" in o:
            s["ping"] = float(o.split("time=")[1].split()[0])
        self.slow = s; self.t_slow = time.time()
        return s

def clases(now):
    try:
        cfg = json.load(open(os.path.join(BASE, "horario.json")))
    except Exception as e:
        log.warning("horario.json: %s", e); return None, None, None
    dur = dt.timedelta(minutes=cfg.get("duracion_min", 80))
    ev = []
    for wk in (0, 7):
        for c in cfg["clases"]:
            h, m = map(int, c["hora"].split(":"))
            day = now.date() + dt.timedelta(days=(c["dia"] - now.weekday()) % 7 + wk)
            st = dt.datetime(day.year, day.month, day.day, h, m, tzinfo=now.tzinfo)
            if c["dia"] == now.weekday() and wk == 0:
                st = dt.datetime(now.year, now.month, now.day, h, m, tzinfo=now.tzinfo)
            ev.append((st, c))
    ev = sorted(set((s, json.dumps(c, sort_keys=True)) for s, c in ev))
    ev = [(s, json.loads(c)) for s, c in ev if s + dur > now]
    if not ev: return None, None, None
    return ev[0], (ev[1] if len(ev) > 1 else None), dur

def alertas_manuales(hoy):
    out = []
    try:
        for l in open(os.path.join(BASE, "alertas.txt"), encoding="utf-8"):
            l = l.strip()
            if not l or l.startswith("#"): continue
            txt, _, extra = l.partition("|")
            extra = extra.strip()
            if extra.startswith("hasta"):
                try:
                    if hoy > dt.date.fromisoformat(extra.split()[1]): continue
                except Exception: pass
            out.append(txt.strip())
    except FileNotFoundError:
        pass
    return out

def hace(seg):
    seg = max(0, int(seg))
    if seg < 3600: return f"hace {seg//60} min"
    if seg < 86400 * 2: return f"hace {seg//3600} h"
    return f"hace {seg//86400} d"

# ---------- dibujo ----------
PANELES = [(0, 0, 480, 28), (8, 30, 232, 152), (240, 30, 474, 152), (8, 158, 232, 234),
           (240, 158, 474, 234), (6, 238, 474, 320)]

def render(d, s, now, tick):
    im = Image.new("RGB", (W * S, H * S), BG); g = ImageDraw.Draw(im)
    def box(x, y, w, h, t, col=C):
        g.rounded_rectangle([x*S, y*S, (x+w)*S, (y+h)*S], 8*S, outline=col, width=2*S, fill=(16, 22, 36))
        g.text(((x+8)*S, (y+5)*S), t, font=F(10, True), fill=col)
    def ring(cx, cy, r, p, lab):
        g.arc([(cx-r)*S, (cy-r)*S, (cx+r)*S, (cy+r)*S], 0, 360, fill=(40, 50, 70), width=6*S)
        col = R if p >= 90 else C
        if p > 0: g.arc([(cx-r)*S, (cy-r)*S, (cx+r)*S, (cy+r)*S], -90, -90 + 3.6*p, fill=col, width=6*S)
        g.text((cx*S, (cy-4)*S), f"{p}%", font=F(13, True), fill=WT, anchor="mm")
        g.text((cx*S, (cy+10)*S), lab, font=F(8), fill=G, anchor="mm")

    auto = []
    # header
    g.text((10*S, 6*S), "◆ ArgOS", font=F(16, True), fill=C)
    g.text((W*S - 10*S, 8*S), now.strftime("%d/%m  %H:%M"), font=F(12, True), fill=WT, anchor="ra")
    g.text((112*S, 11*S), f"● online · {d['uptime_d']}d up", font=F(9), fill=G)
    # hardware
    box(8, 30, 224, 120, "HARDWARE")
    ring(50, 92, 28, d["cpu"], "CPU"); ring(120, 92, 28, d["ram"], "RAM")
    tc = d["temp"]
    g.text((160*S, 62*S), f"{tc}°C" if tc is not None else "--°C", font=F(14, True), fill=R if (tc or 0) > 80 else WT)
    g.text((160*S, 84*S), "DISCO", font=F(8), fill=G)
    g.text((160*S, 95*S), f"{d['disk_u']:.0f}/{d['disk_t']:.0f}G", font=F(10, True), fill=R if d["disk_p"] > 85 else WT)
    g.text((160*S, 115*S), f"↑{d['up']:.1f} ↓{d['down']:.1f}", font=F(9), fill=G)
    g.text((160*S, 127*S), "MB/s eno1", font=F(8), fill=G)
    if tc and tc > 80: auto.append(f"CPU a {tc}°C")
    if d["disk_p"] > 85: auto.append(f"Disco / al {d['disk_p']:.0f}%")
    # servicios
    box(240, 30, 232, 120, "SERVICIOS")
    rows = [("Oracle DB", "ENCENDIDO" if s["oracle"] else "APAGADO", C if s["oracle"] else G),
            ("Uptime Kuma", s["kuma"], C if s["kuma_ok"] else R),
            ("Tailscale", "conectado" if s["ts"] else "desconect.", C if s["ts"] else R),
            ("Ollama", s["ollama"][:13], (C if s["ollama_carga"] else G) if s["ollama_ok"] else R),
            ("Obsidian sync", "OK" if s["obs"] else "detenido", C if s["obs"] else R)]
    for i, (a, b, c) in enumerate(rows):
        y = 50 + i * 19
        g.ellipse([248*S, (y+3)*S, 256*S, (y+11)*S], fill=c)
        g.text((262*S, y*S), a, font=F(10), fill=WT)
        g.text((464*S, y*S), b, font=F(10, True), fill=c, anchor="ra")
    if not s["kuma_ok"]:
        auto.append(f"Uptime Kuma: {s.get('kuma_down', '?')} monitor(es) caído(s)" if s.get("kuma_down") else "Uptime Kuma caído")
    if not s["ts"]: auto.append("Tailscale desconectado")
    if not s["obs"]: auto.append("Obsidian sync detenido")
    if not s["ollama_ok"]: auto.append("Ollama no responde")
    # respaldo
    if s["bk_activo"]:
        col, big = Y, "⟳ en curso"
    elif s["bk_ts"] is None:
        col, big = R, "✘ sin datos"; auto.append("Respaldo: sin registro de ejecución")
    else:
        age = time.time() - s["bk_ts"]
        if not s["bk_ok"]:
            col, big = R, f"✘ {hace(age)}"; auto.append("Respaldo restic FALLÓ")
        elif age > 36 * 3600:
            col, big = R, f"! {hace(age)}"; auto.append(f"Respaldo atrasado ({hace(age)})")
        else:
            col, big = C, f"✔ {hace(age)}"
    box(8, 158, 224, 74, "RESPALDO", C if col == C else col)
    g.text((18*S, 180*S), big, font=F(16, True), fill=col)
    sub = "restic"
    if s["bk_ts"]:
        sub += " · " + dt.datetime.fromtimestamp(s["bk_ts"], now.tzinfo).strftime("%H:%M")
    if s.get("bk_next"):
        sub += " · próx " + dt.datetime.fromtimestamp(s["bk_next"], now.tzinfo).strftime("%H:%M")
    g.text((18*S, 206*S), sub, font=F(9), fill=G)
    # próxima clase
    box(240, 158, 232, 74, "PRÓXIMA CLASE", Y)
    a, b, dur = clases(now)
    if a:
        st, c = a
        g.text((250*S, 178*S), f"{c['ramo']} · {c['hora']}", font=F(13, True), fill=WT)
        if st <= now:
            cuando = "ahora"
        else:
            m = int((st - now).total_seconds() // 60)
            dd, rem = divmod(m, 1440)
            cuando = (f"en {dd} d {rem//60} h" if dd else f"en {m//60} h {m%60} min" if m >= 60 else f"en {m} min")
        g.text((250*S, 200*S), f"{c['sala']} · {cuando}", font=F(10), fill=Y if cuando == "ahora" else G)
        if b:
            dias = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]
            pre = "" if b[0].date() == st.date() else dias[b[0].weekday()] + " "
            g.text((250*S, 214*S), f"luego {b[1]['ramo']} {pre}{b[1]['hora']}", font=F(9), fill=G)
    else:
        g.text((250*S, 180*S), "sin horario", font=F(12, True), fill=G)
    # alertas
    al = auto + alertas_manuales(now.date())
    if al:
        i = tick % len(al)
        g.rounded_rectangle([8*S, 240*S, 472*S, 282*S], 8*S, fill=(40, 20, 24), outline=R, width=2*S)
        g.text((18*S, 246*S), "! ALERTA" + (f"  {i+1}/{len(al)}" if len(al) > 1 else ""), font=F(10, True), fill=R)
        g.text((18*S, 262*S), al[i][:40], font=F(11, True), fill=WT)
    else:
        g.rounded_rectangle([8*S, 240*S, 472*S, 282*S], 8*S, fill=(14, 30, 30), outline=(0, 120, 95), width=2*S)
        g.text((240*S, 261*S), "✔ todo en orden", font=F(12, True), fill=C, anchor="mm")
    pg = f"ping {s['ping']:.0f} ms" if s.get("ping") is not None else "sin internet"
    g.text((240*S, 300*S), f"up {d['uptime_d']}d · carga {d['load']:.2f} · {pg}", font=F(9), fill=OFF, anchor="mm")
    return im.resize((W, H), Image.LANCZOS)

# ---------- pantalla ----------
def conectar():
    lcd = LcdCommRevA(com_port="AUTO", display_width=320, display_height=480)
    lcd.Reset(); lcd.InitializeComm(); lcd.SetBrightness(BRILLO)
    lcd.SetOrientation(Orientation.LANDSCAPE)
    return lcd

def main():
    datos = Datos(); tz = ZoneInfo("America/Santiago")
    lcd = None; prev = None; tick = 0; t_png = 0
    while True:
        try:
            if lcd is None:
                lcd = conectar(); prev = None; log.info("pantalla conectada")
            now = dt.datetime.now(tz)
            img = render(datos.rapido(), datos.lento(), now, tick)
            if prev is None:
                lcd.DisplayPILImage(img, 0, 0)
            else:
                diff = ImageChops.difference(img, prev)
                for (x0, y0, x1, y1) in PANELES:
                    bb = diff.crop((x0, y0, x1, y1)).getbbox()
                    if bb:
                        bx0, by0, bx1, by1 = x0 + bb[0], y0 + bb[1], x0 + bb[2], y0 + bb[3]
                        lcd.DisplayPILImage(img.crop((bx0, by0, bx1, by1)), bx0, by0)
            prev = img; tick += 1
            if time.time() - t_png > 60:
                img.save(os.path.join(BASE, "ultimo.png")); t_png = time.time()
        except Exception as e:
            log.warning("error (%s): %s; reintento en 5 s", type(e).__name__, e)
            try:
                if lcd: lcd.closeSerial()
            except Exception: pass
            lcd = None
        time.sleep(FAST)

if __name__ == "__main__":
    if "--png" in sys.argv:
        dd = Datos(); time.sleep(1)
        render(dd.rapido(), dd.lento(), dt.datetime.now(ZoneInfo("America/Santiago")), 0).save(os.path.join(BASE, "ultimo.png"))
    else:
        main()
