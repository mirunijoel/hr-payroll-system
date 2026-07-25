from datetime import datetime

from database import get_connection

EMPLOYMENT_TYPES = ("full_time", "part_time", "contract")
UPDATABLE_FIELDS = ("name", "role", "team_id", "manager_id", "start_date", "salary", "employment_type")


def _row_to_dict(row):
    return dict(row) if row is not None else None


def _is_valid_date(value):
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except (TypeError, ValueError):
        return False


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
