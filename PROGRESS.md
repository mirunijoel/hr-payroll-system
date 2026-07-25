# Project Tracker

Last updated: 26 July 2026 (leave management and payroll wiring done, README rewritten)

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

## In progress
- [ ] Nothing currently in progress

## Not started
- [ ] Frontend: dashboard (pending approvals, who's out, leave balances,
      payslips for selected period)
- [ ] Frontend: employee page (list, org view, add/deactivate)
- [ ] Frontend: leave page (submit, approve/reject)
- [ ] Frontend: payroll page (generate, view payslips)
- [ ] Frontend: empty/loading states
- [ ] Frontend: favicon, simple logo/wordmark, restrained color palette
- [ ] Route-level automated tests for employees, leave, and payroll HTTP
      routes (currently only manually verified against the running app;
      payroll_calculator.py and leave_rules.py have full pytest coverage)
- [ ] Authentication/authorization (any caller can currently approve or
      reject any leave request via any decided_by employee id)
- [ ] Leave balance tracking (an annual allowance to check requests
      against, not just notice/coverage rules)
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
