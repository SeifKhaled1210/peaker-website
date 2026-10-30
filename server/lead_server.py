#!/usr/bin/env python3
"""Peaker lead endpoint.

Receives the website contact form (POST /api/lead, JSON) and creates a lead
in Odoo CRM over XML-RPC. Python standard library only: no pip installs.

Runs on 127.0.0.1:8081 behind nginx. Settings come from environment variables
(see /etc/peaker/lead.env in DEPLOY.md):

  ODOO_URL       https://erp.yourdomain.com
  ODOO_DB        database name
  ODOO_USER      login of the user that owns website leads
  ODOO_API_KEY   an API key for that user (Odoo: Preferences > Account Security)
  LEAD_TEAM_ID   optional, CRM sales team id
  BACKUP_CSV     optional, defaults to /var/lib/peaker/leads.csv

If Odoo is unreachable, the lead is still saved to the backup CSV, so nothing
is lost, and the visitor gets a normal confirmation.
"""
import csv, json, os, re, threading, time, xmlrpc.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HOST, PORT = "127.0.0.1", int(os.environ.get("PORT", "8081"))
ODOO_URL = os.environ.get("ODOO_URL", "").rstrip("/")
ODOO_DB = os.environ.get("ODOO_DB", "")
ODOO_USER = os.environ.get("ODOO_USER", "")
ODOO_KEY = os.environ.get("ODOO_API_KEY", "")
TEAM_ID = os.environ.get("LEAD_TEAM_ID")
BACKUP = Path(os.environ.get("BACKUP_CSV", "/var/lib/peaker/leads.csv"))

MAX_BODY = 16_000
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
LIMITS = {"name": 120, "company": 160, "email": 160, "phone": 40, "service": 80, "message": 4000, "lang": 2, "page": 120}
RATE_WINDOW, RATE_MAX = 600, 5          # max 5 submissions per IP per 10 minutes
_hits, _lock = {}, threading.Lock()


def rate_limited(ip):
    now = time.time()
    with _lock:
        recent = [t for t in _hits.get(ip, []) if now - t < RATE_WINDOW]
        recent.append(now)
        _hits[ip] = recent
        return len(recent) > RATE_MAX


def clean(data):
    out = {}
    for key, limit in LIMITS.items():
        val = data.get(key, "")
        out[key] = str(val).strip()[:limit] if val is not None else ""
    return out


def save_backup(lead, error=""):
    BACKUP.parent.mkdir(parents=True, exist_ok=True)
    new = not BACKUP.exists()
    with BACKUP.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["time", "name", "company", "email", "phone", "service", "message", "lang", "page", "odoo_error"])
        w.writerow([time.strftime("%Y-%m-%d %H:%M:%S"), lead["name"], lead["company"], lead["email"], lead["phone"],
                    lead["service"], lead["message"], lead["lang"], lead["page"], error])


def create_odoo_lead(lead):
    common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common", allow_none=True)
    uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_KEY, {})
    if not uid:
        raise RuntimeError("Odoo authentication failed")
    models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object", allow_none=True)
    title = f"Website: {lead['service'] or 'Enquiry'} - {lead['company'] or lead['name']}"
    description = (f"{lead['message']}\n\n---\nService: {lead['service']}\nLanguage: {lead['lang']}\n"
                   f"Page: {lead['page']}")
    vals = {
        "name": title[:250],
        "contact_name": lead["name"],
        "partner_name": lead["company"],
        "email_from": lead["email"],
        "phone": lead["phone"],
        "description": description,
        "type": "lead",
    }
    if TEAM_ID:
        vals["team_id"] = int(TEAM_ID)
    return models.execute_kw(ODOO_DB, uid, ODOO_KEY, "crm.lead", "create", [vals])


class Handler(BaseHTTPRequestHandler):
    server_version = "PeakerLead/1.0"

    def _reply(self, code, payload):
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path.rstrip("/") != "/api/lead":
            return self._reply(404, {"ok": False})
        ip = self.headers.get("X-Real-IP") or self.client_address[0]
        if rate_limited(ip):
            return self._reply(429, {"ok": False, "error": "too_many"})
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0 or length > MAX_BODY:
            return self._reply(400, {"ok": False})
        try:
            data = json.loads(self.rfile.read(length))
        except ValueError:
            return self._reply(400, {"ok": False})
        if data.get("website"):                      # honeypot: bots fill hidden fields
            return self._reply(200, {"ok": True})
        lead = clean(data)
        if not lead["name"] or not lead["message"] or not EMAIL_RE.match(lead["email"]):
            return self._reply(422, {"ok": False, "error": "invalid"})
        try:
            lead_id = create_odoo_lead(lead)
            save_backup(lead)
            self.log_message("lead %s created", lead_id)
        except Exception as exc:                     # never lose a lead: keep it in the CSV
            save_backup(lead, error=str(exc)[:200])
            self.log_message("odoo error, saved to backup: %s", exc)
        return self._reply(200, {"ok": True})

    def do_GET(self):
        if self.path == "/api/health":
            return self._reply(200, {"ok": True})
        return self._reply(404, {"ok": False})


if __name__ == "__main__":
    print(f"Peaker lead endpoint on http://{HOST}:{PORT}")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
