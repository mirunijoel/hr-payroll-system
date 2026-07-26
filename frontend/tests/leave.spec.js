const { test, expect } = require('@playwright/test');

// Mutating tests submit fresh requests dated in 2027, both to avoid
// colliding with the seeded rows other assertions rely on and to stay
// out of the dashboard's "this year"/"next 14 days" windows.

test.describe('Leave', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.click('button[data-view="leave"]');
    await page.waitForSelector('#leave-list-container table tbody tr');
  });

  test('lists seeded requests with status badges', async ({ page }) => {
    const list = page.locator('#leave-list-container');
    await expect(list).toContainText('Hassan Ali');
    await expect(list.locator('.badge-critical').first()).toContainText('rejected');
    await expect(list.locator('.badge-good').first()).toBeVisible();
  });

  test('flags a seeded pending request as short notice', async ({ page }) => {
    const ivyRow = page.locator('#leave-list-container tr', { hasText: 'Ivy Chen' });
    await expect(ivyRow.locator('.badge-warning', { hasText: 'Short notice' })).toBeVisible();
  });

  test('can submit a new leave request and see it appear as pending', async ({ page }) => {
    await page.click('#leave-toggle-form');
    await page.waitForSelector('#leave-form');
    await page.selectOption('#leave-form select[name="employee_id"]', { label: 'Grace Lin' });
    await page.selectOption('#leave-form select[name="leave_type"]', 'paid');
    await page.fill('#leave-form input[name="start_date"]', '2027-02-01');
    await page.fill('#leave-form input[name="end_date"]', '2027-02-02');
    await page.fill('#leave-form textarea[name="reason"]', 'E2E submit test');
    await page.click('#leave-form button[type="submit"]');

    const row = page.locator('#leave-list-container tr', { hasText: 'E2E submit test' });
    await expect(row.locator('.badge', { hasText: 'pending' })).toBeVisible();
  });

  test('can approve a pending request and it shows as approved', async ({ page }) => {
    await page.click('#leave-toggle-form');
    await page.waitForSelector('#leave-form');
    await page.selectOption('#leave-form select[name="employee_id"]', { label: 'Elena Petrova' });
    await page.selectOption('#leave-form select[name="leave_type"]', 'paid');
    await page.fill('#leave-form input[name="start_date"]', '2027-03-01');
    await page.fill('#leave-form input[name="end_date"]', '2027-03-02');
    await page.fill('#leave-form textarea[name="reason"]', 'E2E approve test');
    await page.click('#leave-form button[type="submit"]');

    await page.selectOption('#leave-acting-as', { label: 'Grace Lin' });
    const row = page.locator('#leave-list-container tr', { hasText: 'E2E approve test' });
    await row.locator('button:has-text("Approve")').click();

    await expect(page.locator('#leave-list-container tr', { hasText: 'E2E approve test' })).toContainText(
      'approved'
    );
  });

  test('approving without picking "Acting as" shows an error and does not decide the request', async ({ page }) => {
    await page.click('#leave-toggle-form');
    await page.waitForSelector('#leave-form');
    await page.selectOption('#leave-form select[name="employee_id"]', { label: 'Hassan Ali' });
    await page.selectOption('#leave-form select[name="leave_type"]', 'paid');
    await page.fill('#leave-form input[name="start_date"]', '2027-04-01');
    await page.fill('#leave-form input[name="end_date"]', '2027-04-02');
    await page.fill('#leave-form textarea[name="reason"]', 'E2E missing decider test');
    await page.click('#leave-form button[type="submit"]');

    const row = page.locator('#leave-list-container tr', { hasText: 'E2E missing decider test' });
    await row.locator('button:has-text("Approve")').click();

    await expect(page.locator('#leave-message')).toContainText('Select who is deciding first');
    await expect(row.locator('.badge', { hasText: 'pending' })).toBeVisible();
  });
});
