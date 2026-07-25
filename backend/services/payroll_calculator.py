"""Payroll math for a single employee over a single pay period.

Business rules implemented here:

- Gross pay is the employee's monthly salary prorated by days actually
  worked in the period. Both a mid-month start date and unpaid leave days
  reduce the days worked, using the same day-count so the two interact
  correctly rather than being applied as separate, conflicting discounts.
- Tax is a progressive marginal bracket scheme: each bracket's rate only
  applies to the slice of gross pay that falls inside it, not the whole
  amount.
- Social security is a flat rate on gross pay, capped at a fixed maximum
  contribution.
- Net pay is gross pay minus both deductions.
- Employment type (full_time / part_time / contract) does not change any
  of the above. The brief allows a simplified scheme rather than a
  type-specific one, and every employee is paid the same way: prorated
  monthly salary, same tax brackets, same social security rate.

Every function here is pure: no Flask, no database access, no I/O. Dates
are plain datetime.date objects so this module can be tested and reasoned
about in isolation from how a period or employee record gets loaded.
"""

TAX_BRACKETS = (
    (0, 15000, 0.10),
    (15000, 40000, 0.20),
    (40000, None, 0.30),
)

SOCIAL_SECURITY_RATE = 0.06

# Documented assumption: capped at 6% of the top tax bracket threshold
# (40,000), since the brief asks for a simple scheme without specifying
# a real cap. There is no statutory basis for this number, it just keeps
# high earners' social security contribution bounded.
SOCIAL_SECURITY_CAP = 2400.0


def days_in_period(period_start, period_end):
    """Return the number of days in a payroll period, inclusive of both ends.

    A period running 2026-07-01 to 2026-07-31 is 31 days. This is used as
    the denominator for prorating salary, so it must match how the period
    was defined when the payroll run was created (normally a full
    calendar month).
    """
    return (period_end - period_start).days + 1


def days_before_join(period_start, period_end, employee_start_date):
    """Return how many days at the start of the period the employee was not yet employed.

    Zero if they joined on or before the period start. Equal to the full
    period length if they joined after the period ends, since none of the
    period falls after their start date in that case.
    """
    if employee_start_date <= period_start:
        return 0
    if employee_start_date > period_end:
        return days_in_period(period_start, period_end)
    return (employee_start_date - period_start).days


def days_worked_in_period(period_start, period_end, employee_start_date, unpaid_days):
    """Return days actually worked, after both mid-month joining and unpaid leave.

    Mid-month joiners and unpaid leave both reduce the same pool of
    available days (period length minus days before the employee joined),
    rather than being subtracted independently. This matters because an
    employee who joined 10 days into the period only has (period length -
    10) days available in the first place, unpaid leave can only reduce
    what's left of that, not the full period.

    Clamped to [0, available_days] so unpaid leave that exceeds the days
    the employee was actually employed for doesn't push the result
    negative.
    """
    available_days = days_in_period(period_start, period_end) - days_before_join(
        period_start, period_end, employee_start_date
    )
    worked = available_days - unpaid_days
    return max(0, min(worked, available_days))


def prorate_gross_pay(monthly_salary, total_days, worked_days):
    """Prorate a monthly salary by the fraction of the period actually worked."""
    if total_days == 0:
        return 0.0
    return round(monthly_salary / total_days * worked_days, 2)


def calculate_gross_pay(monthly_salary, period_start, period_end, employee_start_date, unpaid_days):
    """Calculate gross pay for the period, accounting for join date and unpaid leave.

    A full unpaid month (or a start date entirely after the period)
    naturally produces 0 days worked, and therefore 0 gross pay rather
    than a negative amount, since days_worked_in_period is clamped at 0.
    """
    total_days = days_in_period(period_start, period_end)
    worked = days_worked_in_period(period_start, period_end, employee_start_date, unpaid_days)
    return prorate_gross_pay(monthly_salary, total_days, worked)


def calculate_tax(gross_pay):
    """Calculate tax owed using progressive marginal brackets.

    Only the slice of gross pay inside each bracket is taxed at that
    bracket's rate. A salary exactly on a boundary (15,000 or 40,000)
    falls entirely within the lower bracket for that dollar, matching
    the documented ranges (0-15,000 at 10%, 15,001-40,000 at 20%,
    40,000+ at 30%): the loop stops as soon as gross pay no longer
    exceeds a bracket's lower bound, so the boundary value itself never
    spills into the next bracket.
    """
    tax = 0.0
    for lower, upper, rate in TAX_BRACKETS:
        if gross_pay <= lower:
            break
        taxable = (gross_pay if upper is None else min(gross_pay, upper)) - lower
        tax += taxable * rate
    return round(tax, 2)


def calculate_social_security(gross_pay):
    """Calculate the flat-rate social security deduction, capped at SOCIAL_SECURITY_CAP."""
    return round(min(gross_pay * SOCIAL_SECURITY_RATE, SOCIAL_SECURITY_CAP), 2)


def calculate_net_pay(gross_pay, tax_deduction, social_security_deduction):
    """Calculate net pay as gross pay minus both deductions."""
    return round(gross_pay - tax_deduction - social_security_deduction, 2)


def generate_payslip(monthly_salary, period_start, period_end, employee_start_date, unpaid_days=0):
    """Generate a full payslip breakdown for one employee over one period.

    Zero-deduction cases fall out of the formulas themselves rather than
    needing special-casing here: a full unpaid month or a start date
    after the period produces 0 gross pay, which in turn produces 0 tax
    and 0 social security, never a negative net pay.
    """
    worked = days_worked_in_period(period_start, period_end, employee_start_date, unpaid_days)
    total_days = days_in_period(period_start, period_end)
    gross_pay = prorate_gross_pay(monthly_salary, total_days, worked)
    tax_deduction = calculate_tax(gross_pay)
    social_security_deduction = calculate_social_security(gross_pay)
    net_pay = calculate_net_pay(gross_pay, tax_deduction, social_security_deduction)

    return {
        "days_worked": worked,
        "unpaid_days": unpaid_days,
        "gross_pay": gross_pay,
        "tax_deduction": tax_deduction,
        "social_security_deduction": social_security_deduction,
        "net_pay": net_pay,
    }
