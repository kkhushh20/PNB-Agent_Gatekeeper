# PNB Agent Gatekeeper

Enrolment number: PGD202563325

A small prototype that decides ALLOW, ASK CUSTOMER or BLOCK when a customer's AI agent
asks Punjab National Bank to view a balance, pay a bill or transfer money.

## Files
- `gatekeeper.py` - the rules, the agent register (register and revoke) and the audit log
- `app.py` - the web page
- `test_cases.py` - runs the 6 test cases and prints expected vs actual
- `RULES.md` - the 7 rules
- `PROMPTS.md` - the instructions given to the coding agent

## How to run
You need Python 3. Nothing else needs to be installed.

Web page:

    python app.py

Then open http://localhost:8000 in your browser.

Tests:

    python test_cases.py

On some computers the command is `python3` instead of `python`.

Data is saved in `gatekeeper.db` (created automatically). Delete that file to start fresh.
