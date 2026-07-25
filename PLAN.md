# HR & Payroll System — My Project Plan

This is my planning document for the assignment, written before/during
development to keep my approach consistent and to record my reasoning on
scope, schema, formulas, and edge cases.

## Stack
- Backend: Flask (Python)
- Frontend: HTML/CSS/vanilla JS (no framework)
- Database: SQLite

## Scope decision (documented reasoning — also goes in README)
The brief explicitly says it's fine to do 1-2 modules well rather than all
three shallowly. Priority order:
1. **Employee Records** — foundational, everything depends on it. Full build.
2. **Payroll** — the core business logic the brief cares most about
   (pro-rating, tax brackets, edge cases). Full build + thorough tests.
3. **Leave Management** — functional workflow with a smaller, well-reasoned
   set of safeguards (not exhaustive edge-case coverage), feeding into payroll.

Stretch goals are not a priority until core is done and tested.

## Project structure
```
hr-payroll-system/
├── backend/
│   ├── app.py                  # Flask app factory, /health route
│   ├── database.py              # init DB from schema.sql, seed from seed.sql
│   ├── models.py
│   ├── routes/
│   │   ├── employees.py
│   │   ├── leave.py
│   │   └── payroll.py
│   ├── services/
│   │   ├── payroll_calculator.py  # PURE functions, no Flask/DB deps
│   │   └── leave_rules.py
│   ├── tests/
│   │   ├── test_payroll.py
│   │   └── test_leave.py
│   ├── database.db              # gitignored, generated locally
│   ├── schema.sql
│   ├── seed.sql
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── css/style.css
│   └── js/
│       ├── dashboard.js
│       ├── employees.js
│       ├── leave.js
│       └── payroll.js
├── README.md
├── CLAUDE.md                    # this file
└── .gitignore
```

## Database schema
- `teams` (id, name)
- `employees` (id, name, role, team_id FK, manager_id FK→employees.id nullable
  self-reference, start_date, salary, employment_type, is_active, created_at)
  — **never hard-deleted**. Deactivate via `is_active=false`. No cascading
  delete on payslips — payroll history must persist.
- `leave_requests` (id, employee_id FK, leave_type, start_date, end_date,
  status [pending/approved/rejected], requested_at, decided_at, decided_by,
  reason)
- `payroll_runs` (id, period_start, period_end, generated_at)
- `payslips` (id, payroll_run_id FK, employee_id FK, gross_pay, tax_deduction,
  social_security_deduction, net_pay, unpaid_days, notes)

## Payroll formula (documented assumptions)
- **Gross pay**: `monthly_salary / days_in_month * days_worked_this_period`
  — accounts for both mid-month joiners AND unpaid leave days in the same
  calculation (days_worked = days_in_month - unpaid_days - days_before_start).
- **Tax**: progressive/marginal bracket system (NOT flat on whole amount):
  - 0 – 15,000: 10%
  - 15,001 – 40,000: 20%
  - 40,000+: 30%
- **Social security**: flat 6%, capped at a defined max contribution.
- **Net pay** = gross − tax − social security.
- **Edge cases to explicitly test**:
  - Mid-month joiner (prorate by days employed, not just leave)
  - Full unpaid month → gross = 0 → deductions = 0, not negative
  - Salary exactly on a bracket boundary
  - Employment type differences if relevant (e.g. contract vs full-time)

## Leave management rules (documented reasoning)
Real leave systems fail in ways spreadsheets don't catch. Rules built in:
1. **Notice period flag** — requests submitted with less than 3 days notice
   are flagged (not blocked) so managers see they need urgent attention.
2. **Team coverage check** — warns if approving a request would leave more
   than 50% of a team out simultaneously over overlapping dates.
3. **Stale request escalation** — any pending request older than 5 days is
   flagged "needs attention" on the dashboard.

Leave integrates with payroll: approved `unpaid` leave days within a payroll
period reduce gross pay via the prorating formula above.

## Build order (sessions)
1. Schema + seed data + Employee CRUD + org view
2. Payroll calculator as pure functions + full test suite (highest scrutiny area)
3. Leave request/approval workflow + the 3 rules above + tests
4. Wire leave into payroll generation
5. Frontend dashboard (pending approvals, who's out, leave balances, payslips)
   + empty/loading states
6. SQL dump + README + final review against actual code behavior

## README must include
- How to run locally
- What was prioritized and why (see Scope decision above)
- Payroll formula/brackets and assumptions
- Leave rules and reasoning
- What would be improved with more time
- Any stretch goals added and why

## Non-negotiables
- README claims must match actual code behavior — this will be checked.
- Core logic (payroll math, leave rules) needs real test coverage more than
  broad coverage elsewhere.
- Deactivate, never delete, employees.
