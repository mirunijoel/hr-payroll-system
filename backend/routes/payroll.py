from datetime import date

from flask import Blueprint, jsonify, request

import models
from services import payroll_calculator

bp = Blueprint("payroll", __name__, url_prefix="/api/payroll")


def _is_valid_date(value):
    try:
        date.fromisoformat(value)
        return True
    except (TypeError, ValueError):
        return False


def _zero_pay_note(gross_pay, employee_start_date, period_end_date):
    """Explain a zero gross pay result on the payslip rather than leaving it unexplained."""
    if gross_pay != 0:
        return None
    if employee_start_date > period_end_date:
        return "not yet employed during this period"
    return "entire period taken as unpaid leave"


@bp.get("/runs")
def list_runs():
    return jsonify(models.list_payroll_runs())


@bp.get("/runs/<int:run_id>")
def get_run(run_id):
    run = models.get_payroll_run(run_id)
    if run is None:
        return jsonify(error="payroll run not found"), 404
    run = dict(run)
    run["payslips"] = models.list_payslips_for_run(run_id)
    return jsonify(run)


@bp.post("/runs")
def create_run():
    """Generate a payroll run: one payslip per active employee for the given period.

    Unpaid days come from approved unpaid leave requests overlapping the
    period, only leave that is both unpaid and approved reduces gross
    pay, pending or rejected requests do not.
    """
    data = request.get_json(silent=True) or {}
    period_start = data.get("period_start")
    period_end = data.get("period_end")

    errors = []
    if not _is_valid_date(period_start):
        errors.append("period_start must be a valid YYYY-MM-DD date")
    if not _is_valid_date(period_end):
        errors.append("period_end must be a valid YYYY-MM-DD date")
    if not errors and period_end < period_start:
        errors.append("period_end cannot be before period_start")
    if errors:
        return jsonify(errors=errors), 400

    if models.payroll_run_exists_for_period(period_start, period_end):
        return jsonify(error=f"a payroll run already exists for {period_start} to {period_end}"), 400

    period_start_date = date.fromisoformat(period_start)
    period_end_date = date.fromisoformat(period_end)

    run_id = models.create_payroll_run(period_start, period_end)

    for employee in models.list_employees(include_inactive=False):
        employee_start_date = date.fromisoformat(employee["start_date"])
        unpaid_days = models.sum_approved_unpaid_days_in_period(employee["id"], period_start, period_end)
        payslip = payroll_calculator.generate_payslip(
            employee["salary"], period_start_date, period_end_date, employee_start_date, unpaid_days
        )
        notes = _zero_pay_note(payslip["gross_pay"], employee_start_date, period_end_date)
        models.create_payslip(
            run_id,
            employee["id"],
            payslip["gross_pay"],
            payslip["tax_deduction"],
            payslip["social_security_deduction"],
            payslip["net_pay"],
            payslip["unpaid_days"],
            notes,
        )

    run = dict(models.get_payroll_run(run_id))
    run["payslips"] = models.list_payslips_for_run(run_id)
    return jsonify(run), 201
