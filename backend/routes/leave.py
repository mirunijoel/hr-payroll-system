from datetime import date, datetime

from flask import Blueprint, jsonify, request

import models
from services import leave_rules

bp = Blueprint("leave", __name__, url_prefix="/api/leave")


def _annotate(leave_request):
    """Attach the notice and staleness flags to a leave request dict for API responses."""
    leave_request = dict(leave_request)
    requested_at = datetime.strptime(leave_request["requested_at"], "%Y-%m-%d %H:%M:%S")
    leave_start = date.fromisoformat(leave_request["start_date"])

    leave_request["is_short_notice"] = leave_rules.is_short_notice(requested_at, leave_start)
    leave_request["is_stale"] = (
        leave_request["status"] == "pending" and leave_rules.is_stale_pending_request(requested_at, datetime.now())
    )
    return leave_request


@bp.get("")
def list_leave_requests():
    status = request.args.get("status")
    employee_id = request.args.get("employee_id", type=int)
    leave_requests = models.list_leave_requests(status=status, employee_id=employee_id)
    return jsonify([_annotate(r) for r in leave_requests])


@bp.get("/<int:request_id>")
def get_leave_request(request_id):
    leave_request = models.get_leave_request(request_id)
    if leave_request is None:
        return jsonify(error="leave request not found"), 404
    return jsonify(_annotate(leave_request))


@bp.post("")
def create_leave_request():
    data = request.get_json(silent=True) or {}
    errors = models.validate_leave_request_payload(data)
    if errors:
        return jsonify(errors=errors), 400

    request_id = models.create_leave_request(data)
    return jsonify(_annotate(models.get_leave_request(request_id))), 201


def _decide(request_id, status):
    leave_request = models.get_leave_request(request_id)
    if leave_request is None:
        return jsonify(error="leave request not found"), 404

    if leave_request["status"] != "pending":
        return jsonify(error=f"leave request is already {leave_request['status']}"), 400

    data = request.get_json(silent=True) or {}
    decided_by = data.get("decided_by")
    if decided_by is None or not models.active_employee_exists(decided_by):
        return jsonify(errors=["decided_by must reference an active employee"]), 400

    response = _annotate_decision(leave_request, status)

    decided_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    models.decide_leave_request(request_id, status, decided_by, decided_at)
    result = _annotate(models.get_leave_request(request_id))
    if "coverage_warning" in response:
        result["coverage_warning"] = response["coverage_warning"]
    return jsonify(result)


def _annotate_decision(leave_request, status):
    """Compute the team coverage warning for an approval, blank for a rejection.

    Coverage is evaluated as if this request were already approved:
    everyone else on the team already on approved leave over the same
    dates, plus this employee. It never blocks the decision, only
    surfaces the risk in the response.
    """
    result = {}
    if status != "approved":
        return result

    team_id = leave_request["employee_team_id"]
    team_size = models.count_active_team_members(team_id)
    employees_out = (
        models.count_team_members_on_approved_leave(
            team_id,
            leave_request["start_date"],
            leave_request["end_date"],
            exclude_employee_id=leave_request["employee_id"],
        )
        + 1
    )

    if leave_rules.exceeds_team_coverage_threshold(team_size, employees_out):
        result["coverage_warning"] = (
            f"approving this leaves {employees_out} of {team_size} team members out "
            f"simultaneously between {leave_request['start_date']} and {leave_request['end_date']}"
        )
    return result


@bp.post("/<int:request_id>/approve")
def approve_leave_request(request_id):
    return _decide(request_id, "approved")


@bp.post("/<int:request_id>/reject")
def reject_leave_request(request_id):
    return _decide(request_id, "rejected")
