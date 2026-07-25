from datetime import date, datetime

from services.leave_rules import (
    date_ranges_overlap,
    days_pending,
    exceeds_team_coverage_threshold,
    is_short_notice,
    is_stale_pending_request,
    notice_period_days,
    team_coverage_ratio,
)


def test_notice_period_days_counts_full_days_between_request_and_leave_start():
    requested_at = datetime(2026, 7, 1, 9, 0)
    assert notice_period_days(requested_at, date(2026, 7, 8)) == 7


def test_notice_period_days_is_negative_for_backdated_sick_leave():
    requested_at = datetime(2026, 7, 10, 9, 0)
    assert notice_period_days(requested_at, date(2026, 7, 8)) == -2


def test_is_short_notice_flags_less_than_three_days():
    requested_at = datetime(2026, 7, 1, 9, 0)
    assert is_short_notice(requested_at, date(2026, 7, 2)) is True


def test_is_short_notice_does_not_flag_exactly_three_days():
    requested_at = datetime(2026, 7, 1, 9, 0)
    assert is_short_notice(requested_at, date(2026, 7, 4)) is False


def test_is_short_notice_does_not_flag_ample_notice():
    requested_at = datetime(2026, 7, 1, 9, 0)
    assert is_short_notice(requested_at, date(2026, 7, 20)) is False


def test_days_pending_counts_days_since_submission():
    requested_at = datetime(2026, 7, 1, 9, 0)
    as_of = datetime(2026, 7, 6, 9, 0)
    assert days_pending(requested_at, as_of) == 5


def test_is_stale_pending_request_flags_over_five_days():
    requested_at = datetime(2026, 7, 1, 9, 0)
    as_of = datetime(2026, 7, 7, 9, 0)
    assert is_stale_pending_request(requested_at, as_of) is True


def test_is_stale_pending_request_does_not_flag_exactly_five_days():
    requested_at = datetime(2026, 7, 1, 9, 0)
    as_of = datetime(2026, 7, 6, 9, 0)
    assert is_stale_pending_request(requested_at, as_of) is False


def test_date_ranges_overlap_when_ranges_intersect():
    assert date_ranges_overlap(date(2026, 7, 1), date(2026, 7, 5), date(2026, 7, 4), date(2026, 7, 10)) is True


def test_date_ranges_overlap_when_one_day_shared_at_boundary():
    assert date_ranges_overlap(date(2026, 7, 1), date(2026, 7, 5), date(2026, 7, 5), date(2026, 7, 10)) is True


def test_date_ranges_overlap_is_false_when_ranges_are_apart():
    assert date_ranges_overlap(date(2026, 7, 1), date(2026, 7, 5), date(2026, 7, 6), date(2026, 7, 10)) is False


def test_team_coverage_ratio_is_zero_for_empty_team():
    assert team_coverage_ratio(team_size=0, employees_out=0) == 0.0


def test_team_coverage_ratio_computes_fraction_out():
    assert team_coverage_ratio(team_size=4, employees_out=2) == 0.5


def test_exceeds_team_coverage_threshold_is_false_at_exactly_fifty_percent():
    assert exceeds_team_coverage_threshold(team_size=4, employees_out=2) is False


def test_exceeds_team_coverage_threshold_is_true_above_fifty_percent():
    assert exceeds_team_coverage_threshold(team_size=4, employees_out=3) is True


def test_exceeds_team_coverage_threshold_is_false_when_no_one_is_out():
    assert exceeds_team_coverage_threshold(team_size=5, employees_out=0) is False
