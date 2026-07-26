const { test, expect } = require('@playwright/test');

// These three tests intentionally depend on running in this order, in
// this file, on the shared server: no payroll run exists yet, then one
// gets generated, then the third test relies on that run already
// existing to check the duplicate-period guard. Playwright runs tests
// within one file sequentially in declaration order, and this project's
// config forces workers to 1 project-wide, so that ordering holds.

test.describe('Payroll', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.click('button[data-view="payroll"]');
    await page.waitForSelector('#payroll-generate-form');
  });

  test('shows an empty state before any payroll has been generated', async ({ page }) => {
    await expect(page.locator('#payroll-runs-container')).toContainText('No payroll runs generated yet.');
  });

  test('can generate a payroll run and see correct payslip figures', async ({ page, request }) => {
    const activeEmployees = await (await request.get('/api/employees')).json();

    await page.fill('input[name="period_start"]', '2026-07-01');
    await page.fill('input[name="period_end"]', '2026-07-31');
    await page.click('#payroll-generate-form button[type="submit"]');

    await page.waitForSelector('#payroll-payslips-container table tbody tr');
    const payslips = page.locator('#payroll-payslips-container tbody tr');
    await expect(payslips).toHaveCount(activeEmployees.length);

    // Farid Hassan has 3 approved unpaid days in the seed data for this period.
    const faridRow = payslips.filter({ hasText: 'Farid Hassan' });
    await expect(faridRow).toContainText('3,432.26');
    await expect(faridRow).toContainText('2,883.09');

    // Ivy Chen is a mid-month joiner (started 2026-07-10) in the seed data.
    const ivyRow = payslips.filter({ hasText: 'Ivy Chen' });
    await expect(ivyRow).toContainText('3,193.55');
  });

  test('rejects generating a period that was already generated', async ({ page }) => {
    // Relies on the previous test having already generated 2026-07-01 to 2026-07-31.
    await page.fill('input[name="period_start"]', '2026-07-01');
    await page.fill('input[name="period_end"]', '2026-07-31');
    await page.click('#payroll-generate-form button[type="submit"]');

    await expect(page.locator('#payroll-generate-errors')).toContainText('already exists');
  });
});
