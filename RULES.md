# Agent Gatekeeper - Rules for Punjab National Bank (PNB)

Enrolment number: PGD202563325

A customer's AI agent can ask for three things: view balance, pay a bill, transfer money.
The rules are checked in order 1 to 7. The first rule that matches decides.

| # | Rule | Decision |
|---|------|----------|
| 1 | A revoked agent is always blocked. | BLOCK |
| 2 | An agent the customer has not registered (unknown agent) is blocked. | BLOCK |
| 3 | An unknown action, or a money action with a missing or zero/negative amount, is blocked. | BLOCK |
| 4 | Viewing the balance (read-only) by a registered agent is allowed. | ALLOW |
| 5 | Paying a bill of Rs 5,000 or less by a registered agent is allowed. | ALLOW |
| 6 | Paying a bill above Rs 5,000 needs the customer's confirmation. | ASK CUSTOMER |
| 7 | Every transfer, of any amount, needs the customer's confirmation. | ASK CUSTOMER |

Every request, with its decision and rule number, is saved in the audit log with the date and time.
Revoking an agent saves the date and time of revocation, so the customer has proof.

**Why Rs 5,000:** [WRITE THIS LINE IN YOUR OWN WORDS. Suggested idea: NPCI's agent payment plan is aimed at small, routine payments, so larger amounts should get a human check.]
