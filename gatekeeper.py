"""PNB Agent Gatekeeper - the rules, the agent register and the audit log.

Roll number: PGD202563325

This file has no web code. It only answers one question:
"A customer's AI agent asked for X. Should the bank ALLOW, ASK CUSTOMER or BLOCK?"
Data is stored in a small SQLite database file (gatekeeper.db) that comes with Python.
"""
import math
import sqlite3
from datetime import datetime

ROLL_NUMBER = "PGD202563325"
COMPANY = "Punjab National Bank (PNB)"

# Spending limit in rupees. Payments above this need the customer's confirmation.
LIMIT = 5000

DB_FILE = "gatekeeper.db"

# The three actions a bank agent may ask for
VIEW_BALANCE = "view_balance"
PAY_BILL = "pay_bill"
TRANSFER = "transfer_money"
ACTIONS = (VIEW_BALANCE, PAY_BILL, TRANSFER)


def now():
    """Current date and time as text, e.g. 2026-11-19 14:05:33"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def query(sql, params=()):
    """Run one SQL command on the database and return the rows (if any)."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(sql, params).fetchall()
        conn.commit()
        return rows
    finally:
        conn.close()


def init_db():
    """Create the two tables if they do not exist yet."""
    query(
        """CREATE TABLE IF NOT EXISTS agents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer TEXT NOT NULL COLLATE NOCASE,
            agent TEXT NOT NULL COLLATE NOCASE,
            status TEXT NOT NULL,
            registered_at TEXT NOT NULL,
            revoked_at TEXT,
            UNIQUE(customer, agent))"""
    )
    query(
        """CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            logged_at TEXT NOT NULL,
            customer TEXT,
            agent TEXT,
            action TEXT,
            amount REAL,
            decision TEXT NOT NULL,
            rule INTEGER NOT NULL,
            reason TEXT NOT NULL)"""
    )


# ---------------------------------------------------------------- agent register

def get_agent(customer, agent):
    """Find the agent record for this customer. Returns None if never registered."""
    rows = query("SELECT * FROM agents WHERE customer = ? AND agent = ?", (customer, agent))
    return rows[0] if rows else None


def register_agent(customer, agent):
    """Register an agent for a customer. Returns (True/False, message)."""
    customer, agent = customer.strip(), agent.strip()
    if not customer or not agent:
        return False, "Customer and agent name are both required."
    existing = get_agent(customer, agent)
    if existing is not None:
        if existing["status"] == "revoked":
            return False, (
                f"{agent} was revoked on {existing['revoked_at']} and cannot be "
                "registered again (a revoked agent is always blocked)."
            )
        return False, f"{agent} is already registered for {customer}."
    query(
        "INSERT INTO agents (customer, agent, status, registered_at) VALUES (?, ?, 'active', ?)",
        (customer, agent, now()),
    )
    return True, f"Registered {agent} for {customer}."


def revoke_agent(customer, agent):
    """Revoke an agent and save the date and time. Returns (True/False, message)."""
    customer, agent = customer.strip(), agent.strip()
    existing = get_agent(customer, agent)
    if existing is None:
        return False, f"No agent called {agent} is registered for {customer}."
    if existing["status"] == "revoked":
        return False, f"{agent} was already revoked on {existing['revoked_at']}."
    revoked_time = now()
    query(
        "UPDATE agents SET status = 'revoked', revoked_at = ? WHERE id = ?",
        (revoked_time, existing["id"]),
    )
    return True, f"Revoked {agent} for {customer} at {revoked_time}. Proof saved."


def list_agents():
    return query("SELECT * FROM agents ORDER BY id")


# ---------------------------------------------------------------- the rules

def decide(agent_status, action, amount):
    """Apply the rules in order. The FIRST rule that matches decides.

    agent_status: None (never registered), "active" or "revoked"
    Returns (decision, rule_number, reason)
    """
    # Rule 1: a revoked agent is always blocked
    if agent_status == "revoked":
        return "BLOCK", 1, "Agent was revoked by the customer."

    # Rule 2: an unknown agent is blocked
    if agent_status is None:
        return "BLOCK", 2, "Unknown agent: not registered by this customer."

    # Rule 3: unknown action, or a money action with a missing/invalid amount
    if action not in ACTIONS:
        return "BLOCK", 3, "Unknown action. Only view balance, pay bill and transfer are supported."
    if action != VIEW_BALANCE and (amount is None or amount <= 0):
        return "BLOCK", 3, "Money action needs an amount greater than zero."

    # Rule 4: read-only action is allowed
    if action == VIEW_BALANCE:
        return "ALLOW", 4, "Read-only action by a registered agent."

    # Rule 7: every transfer needs the customer to confirm
    if action == TRANSFER:
        return "ASK CUSTOMER", 7, "Transfers always need the customer's confirmation."

    # Rules 5 and 6: bill payments depend on the limit
    if amount <= LIMIT:
        return "ALLOW", 5, f"Bill payment within the Rs {LIMIT} limit."
    return "ASK CUSTOMER", 6, f"Bill payment above the Rs {LIMIT} limit."


def parse_amount(text):
    """Turn typed text into a number. Returns None if empty or not a valid number."""
    if text is None:
        return None
    text = str(text).strip().replace(",", "")
    if text == "":
        return None
    try:
        value = float(text)
    except ValueError:
        return None
    return value if math.isfinite(value) else None


def handle_request(customer, agent, action, amount_text):
    """Take one request from an AI agent, decide, write the audit log, return the result."""
    customer, agent, action = customer.strip(), agent.strip(), action.strip()
    amount = parse_amount(amount_text)

    record = get_agent(customer, agent)
    status = record["status"] if record is not None else None

    decision, rule, reason = decide(status, action, amount)

    query(
        """INSERT INTO audit_log (logged_at, customer, agent, action, amount, decision, rule, reason)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (now(), customer, agent, action, amount, decision, rule, reason),
    )
    return {"decision": decision, "rule": rule, "reason": reason}


def list_log():
    return query("SELECT * FROM audit_log ORDER BY id DESC")
