# Project Tracker

Last updated: 26 July 2026 (frontend test setup automated with a reset script)

Submission 2 deadline: 29 July 2026, 09:00 EAT

## Overall status: on track

## Done
- [x] Repo created, Submission 1 (repo link) submitted
- [x] Project structure scaffolded, database schema created
- [x] Employee CRUD (create, list, get, update, deactivate)
- [x] Org chart endpoint (nested manager/reports view)
- [x] models.py data-access layer for employees
- [x] Payroll calculator (pure functions): prorating, marginal tax brackets,
      flat social security, net pay
- [x] Payroll calculator test suite (30 scenario-named tests, all passing):
      mid-month joiner, full unpaid month, bracket boundaries, social
      security cap, employment type equivalence
- [x] cPanel Python App deployment working end-to-end (verified via /health)
- [x] GitHub Actions auto-deploy on push to main (tar-based copy, no
      deletion of runtime files like database.db)
- [x] DEPLOYMENT.md documenting the real deployment setup
- [x] Leave management: services/leave_rules.py (short notice, team
      coverage, stale pending request, all as flags/warnings, not blocks)
- [x] Leave management: tests/test_leave.py (16 scenario-named tests, all
      passing)
- [x] Leave management: models.py data-access layer (CRUD, team coverage
      query helpers, approved-unpaid-days summing)
- [x] Leave management: routes/leave.py (submit/approve/reject endpoints,
      responses annotated with is_short_notice and is_stale)
- [x] Wire approved unpaid leave into payroll generation (only
      leave_type=unpaid and status=approved reduces gross pay; paid and
      sick leave are treated as fully paid)
- [x] routes/payroll.py (generate a run for all active employees over a
      period, fetch a run with its payslips, duplicate-period guard,
      zero-pay payslips annotated with why)
- [x] README.md full rewrite, verified against actual code and against
      the live deployment (checked /health, /api/employees, /api/leave
      on the hosted instance, all current)
- [x] SQL dump (database/dump.sql): full schema plus seed teams,
      employees across all three teams, leave requests in all three
      statuses, and one generated payroll period with real prorated
      payslips. Verified it re-imports cleanly into a fresh database.
- [x] Backend: GET /api/teams lookup, Flask now serves frontend/ as
      static files with index.html at the root
- [x] Frontend shell: tab nav, CSS (status badges, tables, forms, light
      and dark), shared api.js (fetch wrappers, HTML escaping, loading/
      empty/error state helpers)
- [x] Frontend: employees view (table with deactivate, add-employee
      form, org chart as a nested tree)
- [x] Frontend: leave view (status filter, "Acting as" decider selector,
      submit form, approve/reject with coverage-warning display)
- [x] Frontend: payroll view (generate form, runs list, payslips table)
- [x] Frontend: dashboard view (pending approvals, who's out now/next 14
      days, leave taken this year by type labeled as usage not balance,
      recent payroll runs)
- [x] Frontend empty/loading/error states across all four views
- [x] Verified all four tabs end to end in a real browser (Playwright-
      driven headless Chromium): employee table and org chart render
      correctly, leave badges/flags match seed data, payroll generation
      produces correct prorated payslips through the actual UI, and the
      duplicate-run guard surfaces in the form
- [x] Sync frontend/ in the deploy workflow: copied via tar into a
      sibling directory of the cPanel application root (derived from
      DEPLOY_TARGET_PATH, no new secret needed), same no-deletion
      behavior as the backend copy. Live demo now serves the dashboard,
      not just the JSON API
- [x] database.py: get_connection/init_db resolve DB_PATH at call time
      instead of as a bound default, so tests can isolate against a
      throwaway database by reassigning database.DB_PATH
- [x] tests/conftest.py: client fixture, fresh seeded throwaway SQLite
      database per test, never touches the real backend/database.db
- [x] Route-level tests for employees (16), leave (20), and payroll (13),
      95 tests total across the whole suite. Covers CRUD validation,
      org chart nesting/exclusion, short-notice and staleness flags
      (staleness tested by backdating a row so it's time-independent),
      approve/reject transitions, the team coverage warning at and
      above the 50% threshold, exact payslip figures against seeded
      data (unpaid leave, mid-month joiner, pending leave correctly
      ignored), duplicate-period rejection, and both zero-pay notes
- [x] Frontend end-to-end tests (Playwright, 16 tests across 4 spec
      files): dashboard reads seeded data, employees create/deactivate
      with throwaway data, leave submit/approve plus the missing-decider
      error path, payroll generate with exact figures checked against
      seed data plus the duplicate-period guard. Confirmed the suite
      passes twice in a row against a freshly reset database, and
      documented (README) that it requires a reset between runs since
      it shares one server/database for the whole run, unlike the
      backend's per-test isolation
- [x] Automated the frontend test setup: scripts/reset-and-start-backend.js
      deletes database.db and starts Flask via the app factory (no debug
      reloader, so there's no orphaned second process), wired in through
      Playwright's webServer config with reuseExistingServer always
      false. `npx playwright test` alone now resets, starts, runs, and
      tears down, no manual terminal steps. Verified twice in a row.
      README and this file updated accordingly
- [x] Favicon: frontend/favicon.svg, a rounded brand-blue square with an
      "HP" monogram, linked from index.html and confirmed served
      correctly by Flask's static route

## In progress
- [ ] Nothing currently in progress

## Not started
- [ ] Authentication/authorization (any caller can currently approve or
      reject any leave request via any decided_by employee id, or via
      the frontend's "Acting as" selector)
- [ ] Leave allowance/accrual tracking (dashboard shows usage, not a
      balance, since no allowance concept exists in the backend)
- [ ] Overlap prevention for a single employee's leave requests
- [ ] Final review pass: clone fresh, run locally, click through edge cases
- [ ] Submission 2: repo link + SQL dump + optional hosted link

## Decisions made along the way (for reference)
- Scope priority: Employee Records + Payroll as full/robust core, Leave
  Management functional with 3 documented safeguards rather than exhaustive
  coverage
- Hosting: cPanel subdomain (Render/Railway free tiers exhausted), Python
  App via Passenger, deployed via GitHub Actions over SSH
- Deploy strategy: tar-copy from cloned repo into the real Passenger-served
  backend folder, no symlink (caused path resolution issues), no deletion
  of existing files on deploy (protects database.db)
- Deploy secrets: venv path and the real backend path are both stored as
  secrets (VENV_PATH, DEPLOY_TARGET_PATH) rather than hardcoded in the
  workflow file, so the cPanel username and domain never appear in a
  committed file
- Writing rules: no em-dashes, plain and professional tone throughout,
  small logical commits per chunk, plain commit messages, docstrings on
  every public function in service modules, scenario-named tests
- PROGRESS.md is updated alongside each relevant commit rather than as a
  separate one
