# Deployment

Hosted on shared cPanel hosting using Passenger's Python App feature. Render
and Railway free tiers were both exhausted at the time, so cPanel was the
available option.

## cPanel Python App configuration
- **Application root**: `/home1/pbcbible/hr-payroll-system.pbcbiblestudy.org/backend`
- **Application startup file**: `passenger_wsgi.py`
- **Application Entry point**: `application`
- **Python version**: 3.13, virtualenv at
  `/home1/pbcbible/virtualenv/hr-payroll-system.pbcbiblestudy.org/backend/3.13`

`passenger_wsgi.py` imports the Flask app factory from `app.py` and exposes
the created app as `application`, which is what Passenger looks for.

## Deploy flow
Deployment is not a symlink into the git checkout. The application root is a
separate, real directory that Passenger serves from, and each push to `main`
copies the current `backend/` contents into it. GitHub Actions
(`.github/workflows/deploy.yml`) runs over SSH on every push to `main`:

1. `git pull origin main` in the repo checkout.
2. Copy `backend/` into the application root with `tar`, excluding `tmp/`,
   `venv/`, and `database.db`. The server doesn't have `rsync` installed, and
   the copy never deletes existing files in the application root, so the
   live database and any other runtime state are never touched by an
   automated deploy.
3. Activate the app's virtualenv and reinstall dependencies from
   `requirements.txt`.
4. Touch `tmp/restart.txt` in the application root, Passenger's standard
   signal to restart the app on the next request.

## Secrets used by the workflow
- `SSH_HOST`, `SSH_PORT`, `SSH_USER`, `SSH_PRIVATE_KEY`: SSH access to the
  server.
- `APP_PATH`: path to the git checkout that gets pulled.
- `DEPLOY_TARGET_PATH`: the cPanel application root the backend is copied
  into.
- `VENV_PATH`: the virtualenv directory activated before installing
  dependencies.
