"""PNB Agent Gatekeeper - the web page.

Run it with:   python app.py
Then open:     http://localhost:8000

Uses only Python's built-in web server, so nothing needs to be installed.
Roll number: PGD202563325
"""
import html
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, quote, urlparse

import gatekeeper

PORT = 8000

STYLE = """
body { font-family: Arial, sans-serif; max-width: 980px; margin: 24px auto; padding: 0 16px; color: #222; }
h1 { margin-bottom: 0; }
.roll { color: #a4123f; font-weight: bold; font-size: 18px; margin-top: 4px; }
.box { border: 1px solid #ccc; border-radius: 8px; padding: 12px 16px; margin: 16px 0; }
label { display: inline-block; min-width: 90px; margin: 4px 0; }
input, select { padding: 4px; margin: 2px 6px 2px 0; }
button { padding: 6px 14px; cursor: pointer; }
table { border-collapse: collapse; width: 100%; font-size: 14px; }
th, td { border: 1px solid #ccc; padding: 6px; text-align: left; }
th { background: #f2f2f2; }
.msg { padding: 10px 14px; border-radius: 6px; font-weight: bold; }
.ALLOW { background: #d9f2d9; }
.ASK { background: #fff1c2; }
.BLOCK { background: #f8d4d4; }
.INFO { background: #e6eefc; }
"""


def esc(value):
    return html.escape("" if value is None else str(value))


def action_options():
    labels = {
        gatekeeper.VIEW_BALANCE: "View balance",
        gatekeeper.PAY_BILL: "Pay a bill",
        gatekeeper.TRANSFER: "Transfer money",
    }
    return "".join(f'<option value="{a}">{labels[a]}</option>' for a in gatekeeper.ACTIONS)


def build_page(msg="", kind="INFO"):
    agent_rows = ""
    for a in gatekeeper.list_agents():
        agent_rows += (
            f"<tr><td>{esc(a['customer'])}</td><td>{esc(a['agent'])}</td>"
            f"<td>{esc(a['status'])}</td><td>{esc(a['registered_at'])}</td>"
            f"<td>{esc(a['revoked_at'] or '-')}</td></tr>"
        )
    if not agent_rows:
        agent_rows = '<tr><td colspan="5">No agents registered yet.</td></tr>'

    log_rows = ""
    for r in gatekeeper.list_log():
        amount = "-" if r["amount"] is None else f"{r['amount']:,.2f}"
        log_rows += (
            f"<tr><td>{esc(r['logged_at'])}</td><td>{esc(r['customer'])}</td>"
            f"<td>{esc(r['agent'])}</td><td>{esc(r['action'])}</td><td>{amount}</td>"
            f"<td><b>{esc(r['decision'])}</b></td><td>{esc(r['rule'])}</td>"
            f"<td>{esc(r['reason'])}</td></tr>"
        )
    if not log_rows:
        log_rows = '<tr><td colspan="8">No requests yet.</td></tr>'

    message_html = f'<div class="msg {esc(kind)}">{esc(msg)}</div>' if msg else ""

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Agent Gatekeeper - PNB</title><style>{STYLE}</style></head>
<body>
<h1>Agent Gatekeeper - {esc(gatekeeper.COMPANY)}</h1>
<div class="roll">Enrolment number: {esc(gatekeeper.ROLL_NUMBER)}</div>
<p>Decides ALLOW, ASK CUSTOMER or BLOCK for requests made by a customer's AI agent.
Spending limit: Rs {gatekeeper.LIMIT:,}.</p>

{message_html}

<div class="box"><h3>1. Register an agent</h3>
<form method="post" action="/register">
<label>Customer</label><input name="customer" required>
<label>Agent name</label><input name="agent" required>
<button type="submit">Register</button></form></div>

<div class="box"><h3>2. Send a request from an agent</h3>
<form method="post" action="/request">
<label>Customer</label><input name="customer" required>
<label>Agent name</label><input name="agent" required><br>
<label>Action</label><select name="action">{action_options()}</select>
<label>Amount (Rs)</label><input name="amount" placeholder="blank for balance">
<button type="submit">Send request</button></form></div>

<div class="box"><h3>3. Revoke an agent (the date and time are saved)</h3>
<form method="post" action="/revoke">
<label>Customer</label><input name="customer" required>
<label>Agent name</label><input name="agent" required>
<button type="submit">Revoke</button></form></div>

<h3>Registered agents</h3>
<table><tr><th>Customer</th><th>Agent</th><th>Status</th><th>Registered at</th><th>Revoked at</th></tr>
{agent_rows}</table>

<h3>Audit log (newest first)</h3>
<table><tr><th>Date and time</th><th>Customer</th><th>Agent</th><th>Action</th><th>Amount</th>
<th>Decision</th><th>Rule</th><th>Reason</th></tr>
{log_rows}</table>
</body></html>"""


class Handler(BaseHTTPRequestHandler):
    def send_page(self, text):
        data = text.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def redirect(self, msg, kind):
        self.send_response(303)
        self.send_header("Location", f"/?msg={quote(msg)}&kind={quote(kind)}")
        self.end_headers()

    def do_GET(self):
        params = parse_qs(urlparse(self.path).query)
        msg = params.get("msg", [""])[0]
        kind = params.get("kind", ["INFO"])[0]
        if kind not in ("ALLOW", "ASK", "BLOCK", "INFO"):
            kind = "INFO"
        self.send_page(build_page(msg, kind))

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        form = parse_qs(self.rfile.read(length).decode("utf-8"))
        get = lambda name: form.get(name, [""])[0]
        path = urlparse(self.path).path

        if path == "/register":
            ok, message = gatekeeper.register_agent(get("customer"), get("agent"))
            self.redirect(message, "INFO" if ok else "BLOCK")
        elif path == "/revoke":
            ok, message = gatekeeper.revoke_agent(get("customer"), get("agent"))
            self.redirect(message, "INFO" if ok else "BLOCK")
        elif path == "/request":
            result = gatekeeper.handle_request(
                get("customer"), get("agent"), get("action"), get("amount")
            )
            kind = result["decision"].split()[0]  # ALLOW, ASK or BLOCK
            self.redirect(
                f"{result['decision']} (Rule {result['rule']}): {result['reason']}", kind
            )
        else:
            self.send_error(404)

    def log_message(self, format, *args):
        pass  # keep the terminal quiet


if __name__ == "__main__":
    gatekeeper.init_db()
    print(f"Agent Gatekeeper - {gatekeeper.COMPANY}")
    print(f"Enrolment number: {gatekeeper.ROLL_NUMBER}")
    print(f"Open http://localhost:{PORT} in your browser. Press Ctrl+C to stop.")
    HTTPServer(("localhost", PORT), Handler).serve_forever()
