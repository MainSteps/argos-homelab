import sys
sys.argv=["x"]
exec(open("/opt/argos-data/uptime-kuma/configurar.py").read().split("api = UptimeKumaApi(")[0])
from uptime_kuma_api import UptimeKumaApi
cfg = dict(l.strip().split("=",1) for l in open("/etc/argos/uptime-kuma-admin") if "=" in l)
api = UptimeKumaApi("http://<IP_LAN>:3001", timeout=60, wait_events=1); api.login(cfg["usuario"], cfg["password"])
print("tz:", api.get_settings().get("timezone"), "retención:", api.get_settings().get("keepDataPeriodDays"))
hb = api.get_heartbeats()
for m in sorted(api.get_monitors(), key=lambda m:(m["parent"] or 0, m["id"])):
    b = hb.get(m["id"]) or []
    last = b[-1] if b else {}
    st = {0:"DOWN",1:"UP",2:"PENDING",3:"MANT"}.get(last.get("status"), "sin datos")
    print(f'{m["id"]:>2} {m["name"]:<38} {str(m["type"]):<22} {"activo" if m["active"] else "PAUSADO"} {st} {str(last.get("msg",""))[:50]}')
if "--notif" in sys.argv[0:] or True:
    n=[x for x in api.get_notifications() if x["name"]=="ntfy ArgOS"][0]
    import json; cfgn=json.loads(n["config"]) if isinstance(n.get("config"),str) else n
    r = api.sio.call("testNotification", cfgn, timeout=30); print("test ntfy:", r.get("ok"), r.get("msg"))
api.disconnect()
