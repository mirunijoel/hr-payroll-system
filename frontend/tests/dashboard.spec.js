const { test, expect } = require('@playwright/test');

// Read-only against seed data. Never assert on totals that other specs
// could change (e.g. "no payroll runs yet"), only on specific seeded rows
// that no other spec's throwaway data touches or falls into range of.

test.describe('Dashboard', () => {
  test('shows the three stat tiles', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('.stat-tile')).toHaveCount(3);
  });

  test('lists the seeded pending requests as pending approvals', async ({ page }) => {
    await page.goto('/');
    const pending = page.locator('#dashboard-pending-container');
    await expect(pending).toContainText('Ivy Chen');
    await expect(pending).toContainText('David Osei');
  });

  test('shows leave taken this year for employees with approved seed leave', async ({ page }) => {
    await page.goto('/');
    const leaveTaken = page.locator('#dashboard-leave-taken-container');
    await expect(leaveTaken).toContainText('Chloe Tan');
    await expect(leaveTaken).toContainText('Farid Hassan');
  });

  test('shows nobody out, since the seeded approved leave is in the past', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('#dashboard-whos-out-container')).toContainText(
      'No one is out, or scheduled to be out in the next two weeks.'
    );
  });
});
