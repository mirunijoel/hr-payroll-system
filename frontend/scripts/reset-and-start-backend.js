#!/usr/bin/env node

// Used as playwright.config.js's webServer command. Deletes the shared
// SQLite database so every test run starts from the same seeded state
// (see the README note on why this isn't optional for this suite), then
// starts the Flask app directly through the factory rather than
// `python app.py`, so it runs without the debug reloader. The reloader
// forks a second process, which would survive Playwright's shutdown
// signal to this wrapper and hold port 5000 open for the next run.

const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const backendDir = path.join(__dirname, '..', '..', 'backend');
const dbPath = path.join(backendDir, 'database.db');

if (fs.existsSync(dbPath)) {
  fs.unlinkSync(dbPath);
}

const runServer =
  "from app import create_app; create_app().run(host='127.0.0.1', port=5000)";
const server = spawn('python', ['-c', runServer], {
  cwd: backendDir,
  stdio: 'inherit',
});

for (const signal of ['SIGINT', 'SIGTERM']) {
  process.on(signal, () => server.kill(signal));
}

server.on('exit', (code) => {
  process.exit(code === null ? 1 : code);
});
