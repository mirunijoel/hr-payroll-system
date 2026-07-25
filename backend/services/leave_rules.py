"""Safeguard rules for leave requests, on top of the basic submit/approve/reject workflow.

Business rules implemented here:

- Notice period: a request submitted with less than 3 days between the
  request and the leave's start date is flagged as short notice. This is
  informational only, it does not block submission, since a manager may
  still have a good reason to approve a last-minute request (illness,
  emergency). It just makes sure short-notice requests are visible rather
  than blending in with everything else.
- Team coverage: approving a request is flagged as a coverage risk if it
  would put more than half of a team's active headcount on approved leave
  at the same time, for any day the requests overlap. Also a warning, not
  a block, a manager might have valid reasons for over 50% out (e.g. a
  planned team offsite), but they should see the risk before confirming.
- Stale pending requests: a request still pending more than 5 days after
  submission is flagged, so it surfaces on a dashboard instead of quietly
  sitting unanswered.

All three are flags surfaced to whoever is deciding, not hard blocks, real
leave systems fail when requests silently vanish or coverage gaps go
unnoticed, not because the software refused a request outright. Every
function here is pure: no Flask, no database access, no clock reads. The
caller supplies dates (and "now") explicitly, and team/overlap counts are
expected to come from a data-access layer, not from this module.
"""

NOTICE_PERIOD_DAYS = 3
STALE_REQUEST_DAYS = 5
TEAM_COVERAGE_THRESHOLD = 0.5


def notice_period_days(requested_at, leave_start_date):
    """Return the number of days between when a request was submitted and when the leave starts.

    Negative if the request was submitted after the leave was already
    scheduled to start, which can legitimately happen for backdated sick
    leave.
    """
    return (leave_start_date - requested_at.date()).days


def is_short_notice(requested_at, leave_start_date, minimum_days=NOTICE_PERIOD_DAYS):
    """Flag a request as short notice if it gives less than minimum_days notice.

    A request submitted exactly minimum_days before the leave starts is
    not flagged, only strictly less counts as short notice.
    """
    return notice_period_days(requested_at, leave_start_date) < minimum_days


def days_pending(requested_at, as_of):
    """Return how many days a request has been sitting since it was submitted."""
    return (as_of.date() - requested_at.date()).days


def is_stale_pending_request(requested_at, as_of, threshold_days=STALE_REQUEST_DAYS):
    """Flag a still-pending request as stale once it has been waiting more than threshold_days."""
    return days_pending(requested_at, as_of) > threshold_days


def date_ranges_overlap(start_a, end_a, start_b, end_b):
    """Return whether two inclusive date ranges share at least one day."""
    return start_a <= end_b and start_b <= end_a


def team_coverage_ratio(team_size, employees_out):
    """Return the fraction of an active team that would be out simultaneously.

    Zero for an empty team rather than dividing by zero, an empty team
    has no coverage to protect.
    """
    if team_size == 0:
        return 0.0
    return employees_out / team_size


def exceeds_team_coverage_threshold(team_size, employees_out, threshold=TEAM_COVERAGE_THRESHOLD):
    """Flag whether approving a request would push team coverage past the threshold.

    Strictly greater than the threshold, so exactly 50% out (e.g. 2 of 4
    team members) does not trigger the warning, only crossing past half
    does.
    """
    return team_coverage_ratio(team_size, employees_out) > threshold
