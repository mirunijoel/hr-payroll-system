const { test, expect } = require('@playwright/test');

// Mutating tests use throwaway employees with distinctive names rather
// than touching the seeded 9, so counts stay meaningful regardless of
// what other spec files have already added or deactivated.

async function fillAddEmployeeForm(page, { name, role, team, startDate, salary }) {
  await page.click('#employees-toggle-add');
  await page.waitForSelector('#add-employee-form');
  await page.fill('#add-employee-form input[name="name"]', name);
  await page.fill('#add-employee-form input[name="role"]', role);
  await page.selectOption('#add-employee-form select[name="team_id"]', { label: team });
  await page.fill('#add-employee-form input[name="start_date"]', startDate);
  await page.fill('#add-employee-form input[name="salary"]', String(salary));
  await page.click('#add-employee-form button[type="submit"]');
}

test.describe('Employees', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.click('button[data-view="employees"]');
    await page.waitForSelector('#employees-table-container table tbody tr');
  });

  test('lists at least the seeded employees', async ({ page }) => {
    const rowCount = await page.locator('#employees-table-container tbody tr').count();
    expect(rowCount).toBeGreaterThanOrEqual(9);
    await expect(page.locator('#employees-table-container')).toContainText('Asha Kumar');
  });

  test('org chart nests reports under their manager', async ({ page }) => {
    const ben = page.locator('#org-chart-container li', { hasText: 'Ben Ortiz' }).first();
    await expect(ben).toContainText('Chloe Tan');
    await expect(ben).toContainText('David Osei');
    await expect(ben).toContainText('Ivy Chen');
  });

  test('can create a new employee through the form', async ({ page }) => {
    const before = await page.locator('#employees-table-container tbody tr').count();

    await fillAddEmployeeForm(page, {
      name: 'E2E Test Employee',
      role: 'QA',
      team: 'Engineering',
      startDate: '2027-01-05',
      salary: 4000,
    });

    await expect(page.locator('#employees-table-container')).toContainText('E2E Test Employee');
    const after = await page.locator('#employees-table-container tbody tr').count();
    expect(after).toBe(before + 1);
  });

  test('can deactivate an employee, it drops out of the default list but stays visible with the toggle', async ({ page }) => {
    await fillAddEmployeeForm(page, {
      name: 'E2E Deactivate Me',
      role: 'QA',
      team: 'Engineering',
      startDate: '2027-01-06',
      salary: 4000,
    });
    await expect(page.locator('#employees-table-container')).toContainText('E2E Deactivate Me');

    page.once('dialog', (dialog) => dialog.accept());
    await page
      .locator('#employees-table-container tr', { hasText: 'E2E Deactivate Me' })
      .locator('[data-deactivate]')
      .click();

    await expect(page.locator('#employees-table-container')).not.toContainText('E2E Deactivate Me');

    await page.check('#employees-include-inactive');
    await expect(page.locator('#employees-table-container')).toContainText('E2E Deactivate Me');
  });
});
