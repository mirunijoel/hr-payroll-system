// @ts-check
const { defineConfig } = require('@playwright/test');

// Tests share one Flask server and its SQLite database for the whole run
// (no per-test database, unlike the backend's pytest suite), so they run
// serially and are written to use freshly created data rather than
// mutating the shared seed rows, see the comments in each spec file.
module.exports = defineConfig({
  testDir: './tests',
  fullyParallel: false,
  workers: 1,
  reporter: 'list',
  use: {
    baseURL: 'http://127.0.0.1:5000',
    locale: 'en-US',
    trace: 'retain-on-failure',
  },
  // Resets backend/database.db and starts a fresh Flask instance before
  // the run, then tears it down after, see scripts/reset-and-start-backend.js.
  // reuseExistingServer is always false: reusing a server from a previous
  // run would mean reusing its accumulated database too, which is exactly
  // what breaks this suite (see the comment above).
  webServer: {
    command: 'node scripts/reset-and-start-backend.js',
    url: 'http://127.0.0.1:5000/health',
    reuseExistingServer: false,
    timeout: 30000,
  },
});
