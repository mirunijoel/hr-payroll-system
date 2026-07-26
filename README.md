# HR & Payroll System

A small internal tool for managing employee records, leave requests, and
monthly payroll, built to replace the spreadsheet-and-WhatsApp approach
growing teams tend to fall back on. The backend is a Flask JSON API backed
by SQLite, covering employee records with an org hierarchy, a leave
request/approval workflow with a few real-world safeguards, and a payroll
engine that prorates salary for mid-month joiners and unpaid leave,
applies progressive tax brackets, and produces a payslip per employee per
period. A vanilla HTML/CSS/JS dashboard on top covers pending approvals,
who's out, leave taken, org chart, and payroll generation, served
directly by Flask, no build step, no framework.

## Live demo

Hosted at [hr-payroll-system.pbcbiblestudy.org](https://hr-payroll-system.pbcbiblestudy.org)
on personal cPanel hosting (Render and Railway free tiers were both
exhausted at the time). See `DEPLOYMENT.md` for how that's set up. Every
push to `main` deploys both `backend/` and `frontend/`, so the dashboard
is live there too, not just the JSON API.

## Running locally

Requires Python 3.10 or newer (developed and deployed on 3.13).

```
cd backend
python -m venv venv
source venv/Scripts/activate    # venv\Scripts\activate on Windows cmd, or source venv/bin/activate on macOS/Linux
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000` in a browser for the dashboard. On first run
it creates `backend/database.db` from `schema.sql` and seeds it from
`seed.sql` automatically (subsequent runs leave an existing database
alone). A `GET /health` request should return `{"status": "ok"}`.

To run the test suite:

```
cd backend
python -m pytest
```

Route-level tests each get their own fresh, seeded, throwaway SQLite
database (see `tests/conftest.py`), never the real `database.db`, so
running the suite repeatedly is always safe.

### Frontend tests

The frontend has a Playwright end-to-end suite (`frontend/tests/`)
that drives a real browser against a running instance of the app. It
does not spin up its own server or database like the backend suite
does, it needs both running first:

```
# terminal 1: reset and start a fresh backend
cd backend
rm -f database.db
source venv/Scripts/activate
python app.py

# terminal 2: run the frontend tests
cd frontend
npm install
npx playwright test
```

**This suite shares one server and one SQLite database across the
whole run**, unlike the backend's per-test throwaway databases, so
`rm -f database.db` before starting the server is not optional: running
the suite twice against the same accumulated data causes real failures
(a payroll run that already exists, duplicate throwaway employees, and
so on). Tests are written to use freshly created data with distinctive
names rather than mutating the seeded rows, and the three payroll tests
deliberately depend on running in file order (empty state, then
generate, then reject the duplicate), which Playwright preserves within
a single file.

### API endpoints

- `GET /api/teams` - lookup list, used by the employee form's team dropdown

Employees:
- `GET /api/employees` - active employees (`?include_inactive=true` to include deactivated ones)
- `GET /api/employees/org-chart` - nested reporting tree, active employees only
- `GET /api/employees/<id>`
- `POST /api/employees`
- `PUT /api/employees/<id>` - partial updates supported
- `POST /api/employees/<id>/deactivate` - soft delete, no hard delete exists

Leave:
- `GET /api/leave` - filterable with `?status=` and `?employee_id=`
- `GET /api/leave/<id>`
- `POST /api/leave`
- `POST /api/leave/<id>/approve` - body: `{"decided_by": <employee_id>}`
- `POST /api/leave/<id>/reject` - same body

Payroll:
- `GET /api/payroll/runs`
- `GET /api/payroll/runs/<id>` - includes the generated payslips
- `POST /api/payroll/runs` - body: `{"period_start": "YYYY-MM-DD", "period_end": "YYYY-MM-DD"}`

## What I prioritized, and why

The brief is explicit that one or two modules done properly beats all
three done shallowly, so I built in this order: Employee Records first,
since everything else depends on having employees and teams to work
with, then Payroll, since it's the module with real, checkable business
logic (proration, tax brackets, boundary behavior) and the one most
likely to be wrong if rushed, then Leave Management, scoped to a
functional workflow with three specific safeguards rather than every
edge case a full leave system might need. The pure business logic
(`payroll_calculator.py`, `leave_rules.py`), the Flask routes for
employees, leave, and payroll, and the frontend all have automated test
coverage: 95 backend tests (pytest) plus 16 end-to-end tests
(Playwright) driving a real browser against the four dashboard views.

## Payroll formula

Implemented in `backend/services/payroll_calculator.py`, pure functions
with no Flask or database dependency, so the math is unit-testable in
isolation.

- **Gross pay**: `monthly_salary / days_in_period * days_worked`, where
  `days_in_period` is the payroll period's length inclusive of both
  ends. `days_worked` starts from the days in the period the employee
  was actually employed (accounting for a mid-month start date), then
  subtracts unpaid leave days from that same pool, clamped so it never
  goes below zero. This means a mid-month joiner and unpaid leave in the
  same period interact correctly instead of being subtracted
  independently and risking a negative result.
- **Tax**: progressive marginal brackets, only the slice of gross pay
  inside each bracket is taxed at that bracket's rate:
  - 0 to 15,000: 10%
  - 15,000 to 40,000: 20%
  - above 40,000: 30%

  A salary landing exactly on a boundary (15,000 or 40,000) falls
  entirely in the lower bracket for that dollar, it doesn't spill into
  the next rate.
- **Social security**: flat 6% of gross pay, capped at 2,400. That cap
  is an arbitrary assumption (6% of the top tax bracket threshold), not
  based on any real scheme, just a way to keep the brief's "simple
  scheme" bounded for high earners.
- **Net pay** = gross pay − tax − social security.
- **Employment type** (full_time / part_time / contract) does not
  change any of the above. Every employee is paid the same way,
  prorated monthly salary against the same tax brackets and social
  security rate. This is a documented simplification, not an oversight.
- **Zero-deduction cases**: a full unpaid month, or an employee whose
  start date falls after the period ends, both produce 0 days worked,
  and therefore 0 gross pay, 0 tax, 0 social security, and 0 net pay,
  never a negative number. The generated payslip's `notes` field records
  which of the two happened.

## Leave management rules

Implemented in `backend/services/leave_rules.py`. All three are flags
surfaced to whoever is deciding, not hard blocks, real leave systems
tend to fail from requests silently sitting unanswered or coverage gaps
going unnoticed, not from the software being too permissive about a
single request:

1. **Short notice flag**: a request giving less than 3 days between
   submission and the leave's start date is flagged `is_short_notice` on
   the API response. It doesn't block submission, a manager may have a
   good reason to approve a last-minute request.
2. **Team coverage warning**: approving a request is flagged with a
   `coverage_warning` message if it would put more than half of the
   employee's active team on approved leave at the same time, checked
   against any already-approved leave overlapping the same dates. Still
   goes through, it's a warning attached to the approval response, not a
   block.
3. **Stale pending request escalation**: a request still pending more
   than 5 days after submission is flagged `is_stale` so it surfaces
   instead of quietly sitting unanswered. Recomputed against the current
   time whenever the request is fetched, so it doesn't need a background
   job to stay accurate.

**Leave and payroll interaction**: generating a payroll run sums each
employee's *approved* leave requests with `leave_type = unpaid` that
overlap the period (clipped to the period's boundaries) and passes that
count into the payroll calculator as unpaid days. Pending or rejected
leave never affects pay. Paid and sick leave are both treated as fully
paid, only `unpaid` leave reduces gross pay, that's a deliberate scope
decision rather than a real sick-leave policy.

A payroll run also refuses to generate twice for the exact same
`period_start`/`period_end` pair, to avoid accidentally double-running
payroll for a period. It only catches an exact duplicate date range, not
an overlapping-but-different one.

## Frontend

Vanilla HTML/CSS/JS, no framework, no build step, served directly by
Flask (`frontend/` is mounted as the app's static folder). Four tabs:

- **Dashboard**: pending approvals, who's out (today and in the next 14
  days), leave taken this year by type, and recent payroll runs.
- **Employees**: the employee table (with a toggle to include
  deactivated employees), an add-employee form, and the org chart as a
  nested tree.
- **Leave**: status-filterable request list with short-notice/stale
  badges, a submit form, and approve/reject actions. Since there's no
  authentication, an "Acting as" selector stands in for whoever is
  deciding, and gets sent as `decided_by`.
- **Payroll**: a generate-payroll form, the list of past runs, and the
  selected run's payslips.

Every view fetches its own data on load and shows a loading state, an
empty state with a specific message ("No pending approvals." rather
than a blank table), or an error state if the request fails, there's no
silent blank screen for any of the three. Verified all four tabs and
their forms directly in a browser (Playwright-driven Chromium) against
the seeded data before committing.

## What's not built yet, and what I'd improve with more time

- **Authorization**: any caller can approve or reject any leave request
  as any employee via the "Acting as" selector, there's no real
  authentication, and no check that the decider is actually that
  employee's manager.
- **Leave allowance/accrual**: the dashboard shows leave *taken* this
  year by type, not a *balance*, because there's no concept anywhere in
  the backend of an annual allowance or accrual policy to check a
  request against. Adding one (accrual rate, carryover rules, a real
  remaining-balance figure) would be a natural next step.
- **Overlap prevention**: nothing stops one employee from submitting two
  overlapping leave requests.
- **Postgres**: SQLite is fine for this exercise, but a real multi-user
  deployment would want a database that handles concurrent writes better.
- **Frontend test setup**: the Playwright suite requires manually
  starting a freshly reset backend first, rather than managing its own
  server and database per run. Worth automating (a setup script that
  resets the database and starts/stops Flask around the test run)
  before wiring this into CI.

## Stretch goals

None added this round. Given the scope note in the brief, I put the
available time into getting the three core modules right and tested
rather than adding features on top, the frontend dashboard above is
the natural next step before any stretch work would make sense.
