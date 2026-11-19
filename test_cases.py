"""Runs the 6 test cases and prints expected vs actual.

Run it with:   python test_cases.py
Uses its own database file (test_gatekeeper.db) so it never touches your demo data.
Roll number: PGD202563325
"""
import os

import gatekeeper

gatekeeper.DB_FILE = "test_gatekeeper.db"
if os.path.exists(gatekeeper.DB_FILE):
    os.remove(gatekeeper.DB_FILE)  # start clean every time
gatekeeper.init_db()

# Set-up: two agents for customer Asha. OldBot is registered and then revoked.
gatekeeper.register_agent("Asha", "ShopBot")
gatekeeper.register_agent("Asha", "OldBot")
gatekeeper.revoke_agent("Asha", "OldBot")

# (name, customer, agent, action, amount, expected decision, expected rule)
TESTS = [
    ("1. Known agent, read-only", "Asha", "ShopBot", "view_balance", "", "ALLOW", 4),
    ("2. Unknown agent", "Asha", "RandomAI", "view_balance", "", "BLOCK", 2),
    ("3. Bill above limit (Rs 8,000)", "Asha", "ShopBot", "pay_bill", "8000", "ASK CUSTOMER", 6),
    ("4. Bill below limit (Rs 2,000)", "Asha", "ShopBot", "pay_bill", "2000", "ALLOW", 5),
    ("5. Revoked agent tries to pay", "Asha", "OldBot", "pay_bill", "100", "BLOCK", 1),
    ("6. Own case: small transfer (Rs 500)", "Asha", "ShopBot", "transfer_money", "500", "ASK CUSTOMER", 7),
]

print(f"Agent Gatekeeper tests - {gatekeeper.COMPANY} - Enrolment number: {gatekeeper.ROLL_NUMBER}")
print(f"Limit: Rs {gatekeeper.LIMIT}\n")
print(f"{'Test':<40}{'Expected':<22}{'Actual':<22}Result")
print("-" * 90)

passed = 0
for name, customer, agent, action, amount, exp_decision, exp_rule in TESTS:
    result = gatekeeper.handle_request(customer, agent, action, amount)
    expected = f"{exp_decision} (R{exp_rule})"
    actual = f"{result['decision']} (R{result['rule']})"
    ok = result["decision"] == exp_decision and result["rule"] == exp_rule
    passed += ok
    print(f"{name:<40}{expected:<22}{actual:<22}{'PASS' if ok else 'FAIL'}")

print("-" * 90)
print(f"{passed} of {len(TESTS)} tests passed.")
