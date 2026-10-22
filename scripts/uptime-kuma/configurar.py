#!/usr/bin/env python3
"""Configura Uptime Kuma de ArgOS (idempotente en lo posible). Lee secretos de /etc/argos, no los imprime."""
import secrets, os, sys
from uptime_kuma_api import UptimeKumaApi, MonitorType, NotificationType
cfg = dict(l.strip().split("=",1) for l in open("/etc/argos/uptime-kuma-admin") if "=" in l)
TOPIC = open("/etc/argos/ntfy-topic").read().strip()
PUSHENV = "/etc/argos/uptime-kuma-push.env"
import uptime_kuma_api.api as _A
def _call(self, event, data=None):
    r = self.sio.call(event, data, timeout=self.timeout) if data is not None else self.sio.call(event, timeout=self.timeout)
    if isinstance(r, dict) and "ok" in r and not r["ok"]:
        raise _A.UptimeKumaException(r.get("msg"))
    return r
_A.UptimeKumaApi._call = _call
_orig_build = _A.UptimeKumaApi._build_monitor_data
def _build(self, *a, **k):
    pt = k.pop("pushToken", None)
    d = _orig_build(self, *a, **k)
    if pt: d["pushToken"] = pt
    d["conditions"] = []; d.setdefault("kafkaProducerBrokers", []); d.setdefault("kafkaProducerSaslOptions", {}); d.setdefault("rabbitmqNodes", []); return d
_A.UptimeKumaApi._build_monitor_data = _build
api = UptimeKumaApi("http://<IP_LAN>:3001", timeout=60, wait_events=1)
if api.need_setup():
    api.setup(cfg["usuario"], cfg["password"]); print("admin creado")
api.login(cfg["usuario"], cfg["password"])

s = api.get_settings()
s.update(keepDataPeriodDays=90, primaryBaseURL="http://<IP_TAILSCALE>:3001", searchEngineIndex=False,
         entryPage="dashboard", trustProxy=False, tlsExpiryNotifyDays=[30,14,7], nscd=True, chromeExecutable="")
s["timezone"] = "America/Santiago"
r = api.sio.call("setSettings", (s, cfg["password"]), timeout=60); print("settings:", r.get("ok"), r.get("msg",""))

notifs = {n["name"]: n for n in api.get_notifications()}
if "ntfy ArgOS" not in notifs:
    nid = api.add_notification(name="ntfy ArgOS", type=NotificationType.NTFY, isDefault=True, applyExisting=True,
        ntfyserverurl="https://ntfy.sh", ntfytopic=TOPIC, ntfyPriority=5, ntfyIcon="",
        ntfyAuthenticationMethod="none")["id"]
else: nid = notifs["ntfy ArgOS"]["id"]

tags = {t["name"]: t["id"] for t in api.get_tags()}
for name, color in [("Sistema","#2563EB"),("Servicios","#059669"),("Tareas","#D97706"),("Red","#7C3AED"),("Docker","#0891B2"),("A demanda","#6B7280")]:
    if name not in tags: tags[name] = api.add_tag(name=name, color=color)["id"]

dh = {d["name"]: d["id"] for d in api.get_docker_hosts()}
if "ArgOS" not in dh: dh["ArgOS"] = api.add_docker_host(name="ArgOS", dockerType="socket", dockerDaemon="/var/run/docker.sock")["id"]

push = {}
if os.path.exists(PUSHENV):
    push = dict(l.strip().split("=",1) for l in open(PUSHENV) if "=" in l and not l.startswith("#"))
def tok(key):
    if key not in push: push[key] = secrets.token_urlsafe(24).replace("-","x").replace("_","y")[:32]
    return push[key]

base = dict(notificationIDList=[nid], maxretries=2, retryInterval=60, resendInterval=0)
M = [
 # (grupo, tags, kwargs)
 ("Red", ["Red"], dict(type=MonitorType.PING, name="Router (puerta de enlace)", hostname="<IP_ROUTER>", interval=60, description="Ping al router <IP_ROUTER>. Si este cae, el problema es la red de la casa.")),
 ("Red", ["Red"], dict(type=MonitorType.PING, name="Internet (1.1.1.1)", hostname="1.1.1.1", interval=60, maxretries=3, description="Ping a Cloudflare. Si el router está OK y esto cae, se cortó internet.")),
 ("Red", ["Red"], dict(type=MonitorType.DNS, name="DNS (resuelve google.com)", hostname="google.com", dns_resolve_server="1.1.1.1", port=53, dns_resolve_type="A", interval=120, maxretries=3, description="Resolución DNS vía 1.1.1.1.")),
 ("Red", ["Red"], dict(type=MonitorType.KEYWORD, name="ntfy.sh (canal de alertas)", url="https://ntfy.sh/v1/health", keyword="healthy", interval=300, maxretries=3, expiryNotification=True, description="Servidor público que entrega las alertas al iPhone. Vigila también su certificado TLS.")),
 ("Red", ["Red"], dict(type=MonitorType.PUSH, name="Tailscale conectado", pushToken=tok("TAILSCALE"), interval=180, maxretries=1, description="La sonda local confirma cada minuto que Tailscale está en estado Running.")),
 ("Sistema", ["Sistema"], dict(type=MonitorType.PORT, name="SSH (puerto 22)", hostname="<IP_LAN>", port=22, interval=60, description="Acceso remoto a ArgOS.")),
 ("Sistema", ["Sistema"], dict(type=MonitorType.PUSH, name="Recursos (disco, temperatura, RAM)", pushToken=tok("RECURSOS"), interval=180, maxretries=1, description="Sonda local cada minuto. Cae si el disco llega a 90 %, la CPU a 90 °C o la RAM libre baja de 5 %. El tiempo de respuesta muestra la temperatura en °C.")),
 ("Sistema", ["Sistema"], dict(type=MonitorType.PUSH, name="Revisión argos-alerta", pushToken=tok("ALERTA"), interval=3900, maxretries=0, description="argos-alerta corre cada 30 min; avisa si deja de correr.")),
 ("Servicios", ["Servicios"], dict(type=MonitorType.PUSH, name="Ollama (IA local)", pushToken=tok("OLLAMA"), interval=180, maxretries=1, description="Sonda local a 127.0.0.1:11434/api/version (Ollama solo escucha en localhost).")),
 ("Servicios", ["Servicios"], dict(type=MonitorType.PUSH, name="Obsidian Sync (bóveda)", pushToken=tok("OBSIDIAN"), interval=180, maxretries=1, description="argos-obsidian.service activo, sincronizando <BOVEDA>.")),
 ("Servicios", ["Servicios","Docker"], dict(type=MonitorType.DOCKER, name="Docker: Uptime Kuma", docker_container="argos-kuma", docker_host=dh["ArgOS"], interval=300, description="El propio panel (sirve para validar el acceso al socket Docker).")),
 ("Servicios", ["Servicios","Docker","A demanda"], dict(type=MonitorType.DOCKER, name="Oracle (argos-db, a demanda)", docker_container="argos-oracle", docker_host=dh["ArgOS"], interval=300, notificationIDList=[], description="Base de datos que se enciende solo cuando se usa (argos-db). Pausado: apagado NO es falla. Reanúdalo si quieres vigilarlo mientras estudias.")),
 ("Tareas programadas", ["Tareas"], dict(type=MonitorType.PUSH, name="Respaldo restic a Drive (03:30)", pushToken=tok("BACKUP"), interval=93600, maxretries=0, description="Avisa si pasan 26 h sin un respaldo exitoso.")),
 ("Tareas programadas", ["Tareas"], dict(type=MonitorType.PUSH, name="Transcripción nocturna (00:30)", pushToken=tok("TRANSCRIBIR"), interval=93600, maxretries=0, description="Avisa si pasan 26 h sin una transcripción terminada bien.")),
 ("Tareas programadas", ["Tareas"], dict(type=MonitorType.PUSH, name="Puente Drive → ArgOS (30 min)", pushToken=tok("PUENTE"), interval=3900, maxretries=0, description="Copia de Drive a ArgOS. Avisa tras ~1 h sin una corrida exitosa.")),
 ("Tareas programadas", ["Tareas"], dict(type=MonitorType.PUSH, name="Bandeja (30 min)", pushToken=tok("BANDEJA"), interval=3900, maxretries=0, description="Procesa la bandeja de entrada. Avisa tras ~1 h sin éxito.")),
 ("Tareas programadas", ["Tareas"], dict(type=MonitorType.PUSH, name="Estudio (cada hora)", pushToken=tok("ESTUDIO"), interval=7500, maxretries=0, description="Genera apuntes de estudio. Avisa tras ~2 h sin éxito.")),
 ("Tareas programadas", ["Tareas"], dict(type=MonitorType.PUSH, name="Índice de búsqueda (cada hora)", pushToken=tok("BUSQUEDA"), interval=7500, maxretries=0, description="Reindexa la bóveda para argos-buscar. Avisa tras ~2 h sin éxito.")),
]
with open(PUSHENV+".tmp","w") as f:
    f.write("# Tokens push de Uptime Kuma (secretos menores). URL: http://<IP_LAN>:3001/api/push/<token>\n")
    for k,v in sorted(push.items()): f.write(f"{k}={v}\n")
os.chmod(PUSHENV+".tmp",0o600); os.replace(PUSHENV+".tmp",PUSHENV)

exist = {m["name"]: m for m in api.get_monitors()}
groups = {}
for g in ["Sistema","Servicios","Tareas programadas","Red"]:
    if g not in exist: exist[g] = {"id": api.add_monitor(type=MonitorType.GROUP, name=g, notificationIDList=[nid])["monitorID"]}
    groups[g] = exist[g]["id"]
ids = {}
for g, tg, kw in M:
    d = dict(base); d.update(kw); d["parent"] = groups[g]
    if d["name"] in exist:
        mid = exist[d["name"]]["id"]; api.edit_monitor(mid, **d)
    else:
        mid = api.add_monitor(**d)["monitorID"]
        for t in tg: api.add_monitor_tag(tag_id=tags[t], monitor_id=mid, value="")
    ids[d["name"]] = mid
api.pause_monitor(ids["Oracle (argos-db, a demanda)"])

slugs = [p["slug"] for p in api.get_status_pages()]
if "argos" not in slugs: api.add_status_page("argos", "ArgOS")
cfgsp = dict(slug="argos", title="ArgOS", description="Estado del servidor ArgOS de Diego: sistema, servicios, tareas programadas y red. Se actualiza cada minuto.",
    footerText="ArgOS · Uptime Kuma · hora de Chile (America/Santiago)", showTags=True, showPoweredBy=False, showCertificateExpiry=True,
    theme="auto", autoRefreshInterval=60, icon="/icon.svg", customCSS="", googleAnalyticsId=None, domainNameList=[], analyticsType=None, analyticsId=None, analyticsScriptUrl=None)
pgl = [{"name": g, "monitorList": [{"id": ids[kw["name"]]} for gg,_,kw in M if gg==g]} for g in ["Sistema","Servicios","Tareas programadas","Red"]]
r = api.sio.call("saveStatusPage", ("argos", cfgsp, "/icon.svg", pgl), timeout=60)
print("status page:", r.get("ok"), r.get("msg",""))

if not any(m["title"].startswith("Respaldo nocturno") for m in api.get_maintenances()):
    from uptime_kuma_api import MaintenanceStrategy
    r = api.add_maintenance(title="Respaldo nocturno (red)", description="Durante el respaldo a Drive el enlace de subida va saturado; se silencian solo los monitores de internet.",
        strategy=MaintenanceStrategy.RECURRING_INTERVAL, active=True, intervalDay=1, dateRange=["2026-10-22 00:00:00"],
        timeRange=[{"hours":3,"minutes":25},{"hours":4,"minutes":30}], weekdays=[], daysOfMonth=[], timezoneOption="America/Santiago")
    api.add_monitor_maintenance(r["maintenanceID"], [{"id": ids["Internet (1.1.1.1)"]},{"id": ids["DNS (resuelve google.com)"]},{"id": ids["ntfy.sh (canal de alertas)"]}])
import subprocess  # edit_monitor de uptime-kuma-api 1.2 guarda conditions como texto; Kuma 2.x necesita una lista JSON
subprocess.run(["docker","exec","argos-kuma","sqlite3","/app/data/kuma.db","update monitor set conditions='[]' where conditions!='[]';"], check=False)
print("OK monitores:", len(ids))
api.disconnect()
