from flask import Blueprint, jsonify, request

import models

bp = Blueprint("employees", __name__, url_prefix="/api/employees")


@bp.get("")
def list_employees():
    include_inactive = request.args.get("include_inactive", "false").lower() == "true"
    return jsonify(models.list_employees(include_inactive=include_inactive))


@bp.get("/org-chart")
def org_chart():
    return jsonify(models.get_org_chart())


@bp.get("/<int:employee_id>")
def get_employee(employee_id):
    employee = models.get_employee(employee_id)
    if employee is None:
        return jsonify(error="employee not found"), 404
    return jsonify(employee)


@bp.post("")
def create_employee():
    data = request.get_json(silent=True) or {}
    errors = models.validate_employee_payload(data)
    if errors:
        return jsonify(errors=errors), 400

    employee_id = models.create_employee(data)
    return jsonify(models.get_employee(employee_id)), 201


@bp.put("/<int:employee_id>")
def update_employee(employee_id):
    if models.get_employee(employee_id) is None:
        return jsonify(error="employee not found"), 404

    data = request.get_json(silent=True) or {}
    errors = models.validate_employee_payload(data, employee_id=employee_id, partial=True)
    if errors:
        return jsonify(errors=errors), 400

    models.update_employee(employee_id, data)
    return jsonify(models.get_employee(employee_id))


@bp.post("/<int:employee_id>/deactivate")
def deactivate_employee(employee_id):
    if models.get_employee(employee_id) is None:
        return jsonify(error="employee not found"), 404

    models.deactivate_employee(employee_id)
    return jsonify(models.get_employee(employee_id))
