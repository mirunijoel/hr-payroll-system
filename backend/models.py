from datetime import date, datetime

from database import get_connection

EMPLOYMENT_TYPES = ("full_time", "part_time", "contract")
UPDATABLE_FIELDS = ("name", "role", "team_id", "manager_id", "start_date", "salary", "employment_type")
LEAVE_TYPES = ("paid", "unpaid", "sick")
LEAVE_STATUSES = ("pending", "approved", "rejected")


def _row_to_dict(row):
    return dict(row) if row is not None else None


def _is_valid_date(value):
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except (TypeError, ValueError):
        return False


def list_teams():
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM teams ORDER BY name").fetchall()
        return [_row_to_dict(row) for row in rows]
    finally:
        conn.close()


def team_exists(team_id):
    conn = get_connection()
    try:
        return conn.execute("SELECT 1 FROM teams WHERE id = ?", (team_id,)).fetchone() is not None
    finally:
        conn.close()


def active_employee_exists(employee_id):
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT 1 FROM employees WHERE id = ? AND is_active = 1", (employee_id,)
        ).fetchone()
        return row is not None
    finally:
        conn.close()


def validate_employee_payload(data, employee_id=None, partial=False):
    errors = []

    if not partial:
        missing = [field for field in UPDATABLE_FIELDS if field != "manager_id" and data.get(field) in (None, "")]
        if missing:
            errors.append("missing required fields: " + ", ".join(missing))

    if "name" in data and not str(data["name"]).strip():
        errors.append("name cannot be empty")

    if "role" in data and not str(data["role"]).strip():
        errors.append("role cannot be empty")

    if "team_id" in data and data["team_id"] is not None and not team_exists(data["team_id"]):
        errors.append(f"team_id {data['team_id']} does not exist")

    if "manager_id" in data and data["manager_id"] is not None:
        manager_id = data["manager_id"]
        if manager_id == employee_id:
            errors.append("an employee cannot be their own manager")
        elif not active_employee_exists(manager_id):
            errors.append(f"manager_id {manager_id} does not reference an active employee")

    if "start_date" in data and not _is_valid_date(data["start_date"]):
        errors.append("start_date must be a valid YYYY-MM-DD date")

    if "salary" in data:
        try:
            if float(data["salary"]) <= 0:
                errors.append("salary must be greater than 0")
        except (TypeError, ValueError):
            errors.append("salary must be a number")

    if "employment_type" in data and data["employment_type"] not in EMPLOYMENT_TYPES:
        errors.append("employment_type must be one of " + ", ".join(EMPLOYMENT_TYPES))

    return errors


def validate_leave_request_payload(data):
    errors = []

    employee_id = data.get("employee_id")
    if employee_id is None:
        errors.append("employee_id is required")
    elif not active_employee_exists(employee_id):
        errors.append(f"employee_id {employee_id} does not reference an active employee")

    if data.get("leave_type") not in LEAVE_TYPES:
        errors.append("leave_type must be one of " + ", ".join(LEAVE_TYPES))

    start_date = data.get("start_date")
    end_date = data.get("end_date")
    if not _is_valid_date(start_date):
        errors.append("start date must be a valid YYYY-MM-DD date")
    if not _is_valid_date(end_date):
        errors.append("end date must be a valid YYYY-MM-DD date")
    if _is_valid_date(start_date) and _is_valid_date(end_date) and end_date < start_date:
        errors.append("end date cannot be before start date")

    return errors


def list_employees(include_inactive=False):
    conn = get_connection()
    try:
        query = """
            SELECT e.*, t.name AS team_name, m.name AS manager_name
            FROM employees e
            JOIN teams t ON t.id = e.team_id
            LEFT JOIN employees m ON m.id = e.manager_id
        """
        if not include_inactive:
            query += " WHERE e.is_active = 1"
        query += " ORDER BY e.name"
        rows = conn.execute(query).fetchall()
        return [_row_to_dict(row) for row in rows]
    finally:
        conn.close()


def get_employee(employee_id):
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT e.*, t.name AS team_name, m.name AS manager_name
            FROM employees e
            JOIN teams t ON t.id = e.team_id
            LEFT JOIN employees m ON m.id = e.manager_id
            WHERE e.id = ?
            """,
            (employee_id,),
        ).fetchone()
        return _row_to_dict(row)
    finally:
        conn.close()


def create_employee(data):
    conn = get_connection()
    try:
        with conn:
            cursor = conn.execute(
                """
                INSERT INTO employees
                    (name, role, team_id, manager_id, start_date, salary, employment_type, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                """,
                (
                    data["name"],
                    data["role"],
                    data["team_id"],
                    data.get("manager_id"),
                    data["start_date"],
                    data["salary"],
                    data["employment_type"],
                ),
            )
        return cursor.lastrowid
    finally:
        conn.close()


def update_employee(employee_id, data):
    fields = [field for field in UPDATABLE_FIELDS if field in data]
    if not fields:
        return False

    assignments = ", ".join(f"{field} = ?" for field in fields)
    values = [data[field] for field in fields]
    values.append(employee_id)

    conn = get_connection()
    try:
        with conn:
            cursor = conn.execute(f"UPDATE employees SET {assignments} WHERE id = ?", values)
        return cursor.rowcount > 0
    finally:
        conn.close()


def deactivate_employee(employee_id):
    conn = get_connection()
    try:
        with conn:
            cursor = conn.execute("UPDATE employees SET is_active = 0 WHERE id = ?", (employee_id,))
        return cursor.rowcount > 0
    finally:
        conn.close()


def get_org_chart():
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT id, name, role, manager_id FROM employees WHERE is_active = 1 ORDER BY name"
        ).fetchall()
    finally:
        conn.close()

    nodes = {row["id"]: {"id": row["id"], "name": row["name"], "role": row["role"], "reports": []} for row in rows}
    roots = []
    for row in rows:
        node = nodes[row["id"]]
        if row["manager_id"] is not None and row["manager_id"] in nodes:
            nodes[row["manager_id"]]["reports"].append(node)
        else:
            roots.append(node)
    return roots


def create_leave_request(data):
    conn = get_connection()
    try:
        with conn:
            cursor = conn.execute(
                """
                INSERT INTO leave_requests (employee_id, leave_type, start_date, end_date, reason)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    data["employee_id"],
                    data["leave_type"],
                    data["start_date"],
                    data["end_date"],
                    data.get("reason"),
                ),
            )
        return cursor.lastrowid
    finally:
        conn.close()


def get_leave_request(request_id):
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT lr.*, e.name AS employee_name, e.team_id AS employee_team_id
            FROM leave_requests lr
            JOIN employees e ON e.id = lr.employee_id
            WHERE lr.id = ?
            """,
            (request_id,),
        ).fetchone()
        return _row_to_dict(row)
    finally:
        conn.close()


def list_leave_requests(status=None, employee_id=None):
    conn = get_connection()
    try:
        query = """
            SELECT lr.*, e.name AS employee_name, e.team_id AS employee_team_id
            FROM leave_requests lr
            JOIN employees e ON e.id = lr.employee_id
            WHERE 1 = 1
        """
        params = []
        if status is not None:
            query += " AND lr.status = ?"
            params.append(status)
        if employee_id is not None:
            query += " AND lr.employee_id = ?"
            params.append(employee_id)
        query += " ORDER BY lr.requested_at"
        rows = conn.execute(query, params).fetchall()
        return [_row_to_dict(row) for row in rows]
    finally:
        conn.close()


def decide_leave_request(request_id, status, decided_by, decided_at):
    conn = get_connection()
    try:
        with conn:
            cursor = conn.execute(
                """
                UPDATE leave_requests
                SET status = ?, decided_by = ?, decided_at = ?
                WHERE id = ?
                """,
                (status, decided_by, decided_at, request_id),
            )
        return cursor.rowcount > 0
    finally:
        conn.close()


def count_active_team_members(team_id):
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT COUNT(*) AS c FROM employees WHERE team_id = ? AND is_active = 1", (team_id,)
        ).fetchone()
        return row["c"]
    finally:
        conn.close()


def count_team_members_on_approved_leave(team_id, start_date, end_date, exclude_employee_id=None):
    """Count active team members with an approved leave request overlapping the given date range.

    The overlap check mirrors leave_rules.date_ranges_overlap (start_a <=
    end_b AND start_b <= end_a), done in SQL here since it needs to scan
    the team's leave requests rather than compare two known ranges.
    """
    conn = get_connection()
    try:
        query = """
            SELECT COUNT(DISTINCT lr.employee_id) AS c
            FROM leave_requests lr
            JOIN employees e ON e.id = lr.employee_id
            WHERE e.team_id = ?
              AND e.is_active = 1
              AND lr.status = 'approved'
              AND lr.start_date <= ?
              AND lr.end_date >= ?
        """
        params = [team_id, end_date, start_date]
        if exclude_employee_id is not None:
            query += " AND lr.employee_id != ?"
            params.append(exclude_employee_id)
        row = conn.execute(query, params).fetchone()
        return row["c"]
    finally:
        conn.close()


def sum_approved_unpaid_days_in_period(employee_id, period_start, period_end):
    """Sum approved unpaid leave days for one employee that fall inside a payroll period.

    Clips each leave request to the period boundaries before counting, so
    a leave request that only partially overlaps the period only
    contributes the days actually inside it.
    """
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT start_date, end_date
            FROM leave_requests
            WHERE employee_id = ?
              AND leave_type = 'unpaid'
              AND status = 'approved'
              AND start_date <= ?
              AND end_date >= ?
            """,
            (employee_id, period_end, period_start),
        ).fetchall()
    finally:
        conn.close()

    total = 0
    for row in rows:
        clipped_start = max(row["start_date"], period_start)
        clipped_end = min(row["end_date"], period_end)
        start = date.fromisoformat(clipped_start)
        end = date.fromisoformat(clipped_end)
        total += (end - start).days + 1
    return total


def payroll_run_exists_for_period(period_start, period_end):
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id FROM payroll_runs WHERE period_start = ? AND period_end = ?",
            (period_start, period_end),
        ).fetchone()
        return row["id"] if row else None
    finally:
        conn.close()


def create_payroll_run(period_start, period_end):
    conn = get_connection()
    try:
        with conn:
            cursor = conn.execute(
                "INSERT INTO payroll_runs (period_start, period_end) VALUES (?, ?)",
                (period_start, period_end),
            )
        return cursor.lastrowid
    finally:
        conn.close()


def get_payroll_run(run_id):
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM payroll_runs WHERE id = ?", (run_id,)).fetchone()
        return _row_to_dict(row)
    finally:
        conn.close()


def list_payroll_runs():
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM payroll_runs ORDER BY period_start DESC").fetchall()
        return [_row_to_dict(row) for row in rows]
    finally:
        conn.close()


def create_payslip(payroll_run_id, employee_id, gross_pay, tax_deduction, social_security_deduction, net_pay, unpaid_days, notes=None):
    conn = get_connection()
    try:
        with conn:
            cursor = conn.execute(
                """
                INSERT INTO payslips
                    (payroll_run_id, employee_id, gross_pay, tax_deduction, social_security_deduction, net_pay, unpaid_days, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payroll_run_id,
                    employee_id,
                    gross_pay,
                    tax_deduction,
                    social_security_deduction,
                    net_pay,
                    unpaid_days,
                    notes,
                ),
            )
        return cursor.lastrowid
    finally:
        conn.close()


def list_payslips_for_run(run_id):
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT p.*, e.name AS employee_name, e.team_id AS employee_team_id
            FROM payslips p
            JOIN employees e ON e.id = p.employee_id
            WHERE p.payroll_run_id = ?
            ORDER BY e.name
            """,
            (run_id,),
        ).fetchall()
        return [_row_to_dict(row) for row in rows]
    finally:
        conn.close()
