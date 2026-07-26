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
});
