import database


def test_list_leave_requests_returns_all_seeded_requests(client):
    response = client.get('/api/leave')
    assert response.status_code == 200
    assert len(response.get_json()) == 5


def test_list_leave_requests_filters_by_status(client):
    response = client.get('/api/leave?status=pending')
    statuses = {r['status'] for r in response.get_json()}
    assert statuses == {'pending'}


def test_list_leave_requests_filters_by_employee_id(client):
    response = client.get('/api/leave?employee_id=6')
    requests = response.get_json()
    assert len(requests) == 1
    assert requests[0]['employee_name'] == 'Farid Hassan'


def test_get_leave_request_404_for_missing_id(client):
    response = client.get('/api/leave/9999')
    assert response.status_code == 404


def test_short_notice_flag_true_for_request_with_less_than_three_days_notice(client):
    # Ivy Chen's seeded sick leave: requested 2026-07-25, starts 2026-07-26 (1 day notice).
    response = client.get('/api/leave/4')
    assert response.get_json()['is_short_notice'] is True


def test_short_notice_flag_false_for_request_with_ample_notice(client):
    # Chloe Tan's seeded paid leave: requested 2026-06-20, starts 2026-07-03 (13 days notice).
    response = client.get('/api/leave/1')
    assert response.get_json()['is_short_notice'] is False


def test_freshly_submitted_pending_request_is_not_flagged_stale(client):
    response = client.post('/api/leave', json={
        'employee_id': 3, 'leave_type': 'paid', 'start_date': '2026-09-01', 'end_date': '2026-09-02',
    })
    request_id = response.get_json()['id']

    response = client.get(f'/api/leave/{request_id}')
    assert response.get_json()['is_stale'] is False


def test_pending_request_flagged_stale_after_five_days(client):
    response = client.post('/api/leave', json={
        'employee_id': 3, 'leave_type': 'paid', 'start_date': '2026-09-01', 'end_date': '2026-09-02',
    })
    request_id = response.get_json()['id']

    conn = database.get_connection()
    conn.execute(
        "UPDATE leave_requests SET requested_at = datetime('now', '-10 days') WHERE id = ?",
        (request_id,),
    )
    conn.commit()
    conn.close()

    response = client.get(f'/api/leave/{request_id}')
    assert response.get_json()['is_stale'] is True


def test_create_leave_request_with_valid_payload_returns_201(client):
    response = client.post('/api/leave', json={
        'employee_id': 4, 'leave_type': 'unpaid', 'start_date': '2026-08-01', 'end_date': '2026-08-03',
        'reason': 'Trip',
    })
    assert response.status_code == 201
    leave_request = response.get_json()
    assert leave_request['status'] == 'pending'
    assert leave_request['employee_name'] == 'David Osei'


def test_create_leave_request_with_invalid_leave_type_returns_400(client):
    response = client.post('/api/leave', json={
        'employee_id': 4, 'leave_type': 'vacation', 'start_date': '2026-08-01', 'end_date': '2026-08-03',
    })
    assert response.status_code == 400


def test_create_leave_request_with_end_before_start_returns_400(client):
    response = client.post('/api/leave', json={
        'employee_id': 4, 'leave_type': 'paid', 'start_date': '2026-08-05', 'end_date': '2026-08-01',
    })
    assert response.status_code == 400


def test_approve_requires_decided_by(client):
    response = client.post('/api/leave/3/approve', json={})
    assert response.status_code == 400


def test_approve_rejects_inactive_or_missing_decider(client):
    response = client.post('/api/leave/3/approve', json={'decided_by': 9999})
    assert response.status_code == 400


def test_approve_transitions_pending_request_to_approved(client):
    response = client.post('/api/leave/3/approve', json={'decided_by': 2})
    assert response.status_code == 200
    assert response.get_json()['status'] == 'approved'
    assert response.get_json()['decided_by'] == 2


def test_reject_transitions_pending_request_to_rejected(client):
    response = client.post('/api/leave/4/reject', json={'decided_by': 2})
    assert response.status_code == 200
    assert response.get_json()['status'] == 'rejected'


def test_deciding_an_already_decided_request_returns_400(client):
    response = client.post('/api/leave/1/approve', json={'decided_by': 2})
    assert response.status_code == 400


def test_decide_404_for_missing_request(client):
    response = client.post('/api/leave/9999/approve', json={'decided_by': 2})
    assert response.status_code == 404


def _submit_and_approve(client, employee_id, start, end):
    response = client.post('/api/leave', json={
        'employee_id': employee_id, 'leave_type': 'paid', 'start_date': start, 'end_date': end,
    })
    request_id = response.get_json()['id']
    return client.post(f'/api/leave/{request_id}/approve', json={'decided_by': 1})


def test_approve_has_no_coverage_warning_below_fifty_percent_of_team(client):
    # Engineering (team 1) has 5 active members. Approving 2 out of 5 is 40%.
    _submit_and_approve(client, 3, '2026-09-01', '2026-09-05')
    response = _submit_and_approve(client, 4, '2026-09-02', '2026-09-04')
    assert 'coverage_warning' not in response.get_json()


def test_approve_has_coverage_warning_above_fifty_percent_of_team(client):
    # Engineering (team 1) has 5 active members. Approving a 3rd overlapping request is 60%.
    _submit_and_approve(client, 3, '2026-09-01', '2026-09-05')
    _submit_and_approve(client, 4, '2026-09-02', '2026-09-04')
    response = _submit_and_approve(client, 9, '2026-09-03', '2026-09-03')
    assert 'coverage_warning' in response.get_json()
    assert '3 of 5' in response.get_json()['coverage_warning']


def test_approve_coverage_check_ignores_non_overlapping_dates(client):
    # Same team, but the third request doesn't overlap the first two, so no warning.
    _submit_and_approve(client, 3, '2026-09-01', '2026-09-05')
    _submit_and_approve(client, 4, '2026-09-02', '2026-09-04')
    response = _submit_and_approve(client, 9, '2026-10-01', '2026-10-03')
    assert 'coverage_warning' not in response.get_json()
