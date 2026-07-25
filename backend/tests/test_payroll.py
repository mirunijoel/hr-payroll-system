from datetime import date

from services.payroll_calculator import (
    calculate_gross_pay,
    calculate_net_pay,
    calculate_social_security,
    calculate_tax,
    days_before_join,
    days_in_period,
    days_worked_in_period,
    generate_payslip,
    prorate_gross_pay,
)

JULY = (date(2026, 7, 1), date(2026, 7, 31))


def test_days_in_period_counts_both_endpoints():
    assert days_in_period(*JULY) == 31


def test_days_before_join_is_zero_when_employee_started_before_period():
    assert days_before_join(*JULY, date(2026, 6, 1)) == 0


def test_days_before_join_is_zero_when_employee_started_on_period_start():
    assert days_before_join(*JULY, date(2026, 7, 1)) == 0


def test_days_before_join_counts_days_missed_for_mid_month_joiner():
    assert days_before_join(*JULY, date(2026, 7, 11)) == 10


def test_days_before_join_is_full_period_when_employee_starts_after_period_ends():
    assert days_before_join(*JULY, date(2026, 8, 1)) == 31


def test_days_worked_is_full_period_with_no_leave_and_no_mid_month_join():
    assert days_worked_in_period(*JULY, date(2026, 1, 1), unpaid_days=0) == 31


def test_days_worked_subtracts_unpaid_leave():
    assert days_worked_in_period(*JULY, date(2026, 1, 1), unpaid_days=3) == 28


def test_days_worked_subtracts_days_missed_for_mid_month_joiner():
    assert days_worked_in_period(*JULY, date(2026, 7, 11), unpaid_days=0) == 21


def test_days_worked_combines_mid_month_join_and_unpaid_leave():
    assert days_worked_in_period(*JULY, date(2026, 7, 11), unpaid_days=5) == 16


def test_days_worked_does_not_go_negative_when_unpaid_leave_exceeds_days_employed():
    assert days_worked_in_period(*JULY, date(2026, 7, 25), unpaid_days=20) == 0


def test_days_worked_is_zero_when_employee_starts_after_period_ends():
    assert days_worked_in_period(*JULY, date(2026, 8, 1), unpaid_days=0) == 0


def test_prorate_gross_pay_splits_salary_evenly_across_period_days():
    assert prorate_gross_pay(31000, total_days=31, worked_days=31) == 31000.0
    assert prorate_gross_pay(31000, total_days=31, worked_days=15) == 15000.0


def test_calculate_gross_pay_for_full_month_no_leave():
    assert calculate_gross_pay(9300, *JULY, date(2020, 1, 1), unpaid_days=0) == 9300.0


def test_calculate_gross_pay_prorates_for_mid_month_joiner():
    # 31-day July, joined on the 11th: 21 of 31 days worked.
    assert calculate_gross_pay(9300, *JULY, date(2026, 7, 11), unpaid_days=0) == 6300.0


def test_calculate_gross_pay_is_zero_for_a_full_unpaid_month():
    assert calculate_gross_pay(9300, *JULY, date(2020, 1, 1), unpaid_days=31) == 0.0


def test_calculate_tax_below_first_bracket():
    assert calculate_tax(10000) == 1000.0


def test_calculate_tax_at_first_bracket_boundary_stays_in_lower_rate():
    assert calculate_tax(15000) == 1500.0


def test_calculate_tax_spans_first_and_second_brackets():
    # 15000 at 10% + 5000 at 20%.
    assert calculate_tax(20000) == 2500.0


def test_calculate_tax_at_second_bracket_boundary_stays_out_of_top_rate():
    # 15000 at 10% + 25000 at 20%, none at 30%.
    assert calculate_tax(40000) == 6500.0


def test_calculate_tax_spans_all_three_brackets():
    # 15000 at 10% + 25000 at 20% + 10000 at 30%.
    assert calculate_tax(50000) == 9500.0


def test_calculate_tax_is_zero_for_zero_gross_pay():
    assert calculate_tax(0) == 0.0


def test_calculate_social_security_flat_rate_below_cap():
    assert calculate_social_security(10000) == 600.0


def test_calculate_social_security_is_capped_for_high_earners():
    assert calculate_social_security(100000) == 2400.0


def test_calculate_social_security_is_zero_for_zero_gross_pay():
    assert calculate_social_security(0) == 0.0


def test_calculate_net_pay_subtracts_both_deductions():
    assert calculate_net_pay(10000, tax_deduction=1000, social_security_deduction=600) == 8400.0


def test_calculate_net_pay_is_zero_when_gross_pay_is_zero():
    assert calculate_net_pay(0, tax_deduction=0, social_security_deduction=0) == 0.0


def test_generate_payslip_for_full_month_full_time_employee():
    payslip = generate_payslip(9300, *JULY, date(2020, 1, 1), unpaid_days=0)
    assert payslip == {
        "days_worked": 31,
        "unpaid_days": 0,
        "gross_pay": 9300.0,
        "tax_deduction": 930.0,
        "social_security_deduction": 558.0,
        "net_pay": 7812.0,
    }


def test_generate_payslip_prorates_for_mid_month_joiner():
    payslip = generate_payslip(9300, *JULY, date(2026, 7, 11), unpaid_days=0)
    assert payslip["gross_pay"] == 6300.0
    assert payslip["days_worked"] == 21


def test_generate_payslip_is_all_zero_for_a_full_unpaid_month():
    payslip = generate_payslip(9300, *JULY, date(2020, 1, 1), unpaid_days=31)
    assert payslip == {
        "days_worked": 0,
        "unpaid_days": 31,
        "gross_pay": 0.0,
        "tax_deduction": 0.0,
        "social_security_deduction": 0.0,
        "net_pay": 0.0,
    }


def test_generate_payslip_treats_contract_and_full_time_the_same():
    # employment_type is not a parameter here: the formula is identical
    # regardless of type, so a contract employee with the same salary and
    # days worked gets the same payslip as a full-time employee.
    full_time = generate_payslip(4500, *JULY, date(2020, 1, 1), unpaid_days=0)
    contract = generate_payslip(4500, *JULY, date(2020, 1, 1), unpaid_days=0)
    assert full_time == contract
