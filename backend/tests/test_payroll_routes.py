def _generate_july_payroll(client):
    return client.post('/api/payroll/runs', json={'period_start': '2026-07-01', 'period_end': '2026-07-31'})


def _payslip_for(payslips, employee_name):
    return next(p for p in payslips if p['employee_name'] == employee_name)


def test_generate_payroll_run_creates_one_payslip_per_active_employee(client):
    response = _generate_july_payroll(client)
    assert response.status_code == 201
    run = response.get_json()
    assert len(run['payslips']) == 9


def test_generate_payroll_run_pays_full_month_with_no_leave_in_full(client):
    run = _generate_july_payroll(client).get_json()
    asha = _payslip_for(run['payslips'], 'Asha Kumar')
    assert asha['gross_pay'] == 9000.0
    assert asha['tax_deduction'] == 900.0
    assert asha['social_security_deduction'] == 540.0
    assert asha['net_pay'] == 7560.0
    assert asha['unpaid_days'] == 0
    assert asha['notes'] is None


def test_generate_payroll_run_applies_approved_unpaid_leave(client):
    # Farid Hassan has 3 approved unpaid days in July in the seed data.
    run = _generate_july_payroll(client).get_json()
    farid = _payslip_for(run['payslips'], 'Farid Hassan')
    assert farid['unpaid_days'] == 3
    assert farid['gross_pay'] == 3432.26
    assert farid['net_pay'] == 2883.09


def test_generate_payroll_run_prorates_mid_month_joiner(client):
    # Ivy Chen started 2026-07-10, 22 of 31 days worked, no leave.
    run = _generate_july_payroll(client).get_json()
    ivy = _payslip_for(run['payslips'], 'Ivy Chen')
    assert ivy['gross_pay'] == 3193.55
    assert ivy['unpaid_days'] == 0


def test_generate_payroll_run_ignores_pending_unpaid_leave(client):
    # David Osei has a pending (not approved) unpaid request inside July, so it must not reduce pay.
    run = _generate_july_payroll(client).get_json()
    david = _payslip_for(run['payslips'], 'David Osei')
    assert david['unpaid_days'] == 0
    assert david['gross_pay'] == 4200.0


def test_generate_payroll_run_rejects_invalid_dates(client):
    response = client.post('/api/payroll/runs', json={'period_start': 'nope', 'period_end': '2026-07-31'})
    assert response.status_code == 400


def test_generate_payroll_run_rejects_end_before_start(client):
    response = client.post('/api/payroll/runs', json={'period_start': '2026-07-31', 'period_end': '2026-07-01'})
    assert response.status_code == 400


def test_generate_payroll_run_rejects_duplicate_period(client):
    _generate_july_payroll(client)
    response = _generate_july_payroll(client)
    assert response.status_code == 400


def test_get_payroll_run_includes_payslips(client):
    run_id = _generate_july_payroll(client).get_json()['id']
    response = client.get(f'/api/payroll/runs/{run_id}')
    assert response.status_code == 200
    assert len(response.get_json()['payslips']) == 9


def test_get_payroll_run_404_for_missing_id(client):
    response = client.get('/api/payroll/runs/9999')
    assert response.status_code == 404


def test_list_payroll_runs_returns_generated_runs(client):
    _generate_july_payroll(client)
    response = client.get('/api/payroll/runs')
    runs = response.get_json()
    assert len(runs) == 1
    assert runs[0]['period_start'] == '2026-07-01'
    assert runs[0]['period_end'] == '2026-07-31'


def test_zero_pay_note_for_a_full_unpaid_month(client):
    leave_response = client.post('/api/leave', json={
        'employee_id': 3, 'leave_type': 'unpaid', 'start_date': '2026-07-01', 'end_date': '2026-07-31',
    })
    leave_id = leave_response.get_json()['id']
    client.post(f'/api/leave/{leave_id}/approve', json={'decided_by': 1})

    run = _generate_july_payroll(client).get_json()
    chloe = _payslip_for(run['payslips'], 'Chloe Tan')
    assert chloe['gross_pay'] == 0.0
    assert chloe['net_pay'] == 0.0
    assert chloe['notes'] == 'entire period taken as unpaid leave'


def test_zero_pay_note_for_employee_not_yet_employed_during_period(client):
    create_response = client.post('/api/employees', json={
        'name': 'Future Hire', 'role': 'Engineer', 'team_id': 1,
        'start_date': '2026-09-01', 'salary': 5000, 'employment_type': 'full_time',
    })
    future_hire_id = create_response.get_json()['id']

    run = _generate_july_payroll(client).get_json()
    future_hire = next(p for p in run['payslips'] if p['employee_id'] == future_hire_id)
    assert future_hire['gross_pay'] == 0.0
    assert future_hire['notes'] == 'not yet employed during this period'
