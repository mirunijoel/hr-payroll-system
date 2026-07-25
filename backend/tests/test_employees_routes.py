def test_list_employees_returns_seeded_active_employees(client):
    response = client.get('/api/employees')
    assert response.status_code == 200
    employees = response.get_json()
    assert len(employees) == 9
    assert all(employee['is_active'] for employee in employees)


def test_list_employees_excludes_deactivated_by_default(client):
    client.post('/api/employees/9/deactivate')

    response = client.get('/api/employees')
    ids = [employee['id'] for employee in response.get_json()]
    assert 9 not in ids


def test_list_employees_include_inactive_returns_deactivated_too(client):
    client.post('/api/employees/9/deactivate')

    response = client.get('/api/employees?include_inactive=true')
    ids = [employee['id'] for employee in response.get_json()]
    assert 9 in ids
    assert len(response.get_json()) == 9


def test_get_employee_includes_team_and_manager_names(client):
    response = client.get('/api/employees/2')
    assert response.status_code == 200
    employee = response.get_json()
    assert employee['name'] == 'Ben Ortiz'
    assert employee['team_name'] == 'Engineering'
    assert employee['manager_name'] == 'Asha Kumar'


def test_get_employee_404_for_missing_id(client):
    response = client.get('/api/employees/9999')
    assert response.status_code == 404


def test_org_chart_nests_reports_under_their_manager(client):
    response = client.get('/api/employees/org-chart')
    assert response.status_code == 200
    roots = response.get_json()

    root_names = {node['name'] for node in roots}
    assert root_names == {'Asha Kumar', 'Elena Petrova', 'Grace Lin'}

    asha = next(node for node in roots if node['name'] == 'Asha Kumar')
    ben = next(node for node in asha['reports'] if node['name'] == 'Ben Ortiz')
    report_names = {node['name'] for node in ben['reports']}
    assert report_names == {'Chloe Tan', 'David Osei', 'Ivy Chen'}


def test_org_chart_excludes_deactivated_employees(client):
    client.post('/api/employees/9/deactivate')

    response = client.get('/api/employees/org-chart')
    roots = response.get_json()
    asha = next(node for node in roots if node['name'] == 'Asha Kumar')
    ben = next(node for node in asha['reports'] if node['name'] == 'Ben Ortiz')
    report_names = {node['name'] for node in ben['reports']}
    assert 'Ivy Chen' not in report_names


def test_create_employee_with_valid_payload_returns_201(client):
    response = client.post('/api/employees', json={
        'name': 'New Hire',
        'role': 'Analyst',
        'team_id': 3,
        'manager_id': 7,
        'start_date': '2026-08-01',
        'salary': 4000,
        'employment_type': 'full_time',
    })
    assert response.status_code == 201
    employee = response.get_json()
    assert employee['name'] == 'New Hire'
    assert employee['is_active'] == 1


def test_create_employee_missing_required_fields_returns_400(client):
    response = client.post('/api/employees', json={'name': 'Incomplete'})
    assert response.status_code == 400
    assert 'errors' in response.get_json()


def test_create_employee_with_nonexistent_team_returns_400(client):
    response = client.post('/api/employees', json={
        'name': 'New Hire',
        'role': 'Analyst',
        'team_id': 999,
        'start_date': '2026-08-01',
        'salary': 4000,
        'employment_type': 'full_time',
    })
    assert response.status_code == 400


def test_update_employee_partial_update_changes_only_given_fields(client):
    response = client.put('/api/employees/3', json={'salary': 5500})
    assert response.status_code == 200
    employee = response.get_json()
    assert employee['salary'] == 5500
    assert employee['name'] == 'Chloe Tan'
    assert employee['role'] == 'Software Engineer'


def test_update_employee_cannot_set_self_as_manager(client):
    response = client.put('/api/employees/2', json={'manager_id': 2})
    assert response.status_code == 400


def test_update_employee_404_for_missing_id(client):
    response = client.put('/api/employees/9999', json={'salary': 5000})
    assert response.status_code == 404


def test_deactivate_employee_keeps_the_record_but_marks_inactive(client):
    response = client.post('/api/employees/9/deactivate')
    assert response.status_code == 200
    employee = response.get_json()
    assert employee['is_active'] == 0
    assert employee['name'] == 'Ivy Chen'


def test_deactivate_employee_404_for_missing_id(client):
    response = client.post('/api/employees/9999/deactivate')
    assert response.status_code == 404


def test_teams_endpoint_returns_seeded_teams(client):
    response = client.get('/api/teams')
    assert response.status_code == 200
    names = {team['name'] for team in response.get_json()}
    assert names == {'Engineering', 'Sales', 'People Ops'}
