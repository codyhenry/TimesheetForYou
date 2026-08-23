# TimesheetForYou

Timesheet app for nanny companies.

This repo contains a Django REST API backend and a React Native/Expo mobile app.

## Project Structure

```txt
TimesheetForYou/
  timesheet_project/   # Django + Django REST Framework backend
  mobile/              # React Native / Expo app
```

## Prerequisites

Install these before running the app:

- Python 3.10+
- Node.js 18+
- npm
- Expo Go app on your iOS or Android device, if testing on a physical phone
- PostgreSQL, optional for local development

The backend can run with SQLite by default if no PostgreSQL environment variables are provided.

## Backend Setup: Django REST API

From the repo root:

```bash
cd timesheet_project
python -m venv .venv
```

Activate the virtual environment.

On macOS/Linux:

```bash
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run migrations:

```bash
python manage.py migrate
```

Create an admin user:

```bash
python manage.py createsuperuser
```

Start the backend server:

```bash
python manage.py runserver 0.0.0.0:8000
```

Useful backend URLs:

- Django admin: `http://localhost:8000/django-admin/`
- API token endpoint: `http://localhost:8000/api/token/`
- API token refresh endpoint: `http://localhost:8000/api/token/refresh/`
- Dashboard: `http://localhost:8000/dashboard/`
- Health check: `http://localhost:8000/healthz/`

## Optional Backend Environment Variables

For local SQLite development, no `.env` file is required.

For PostgreSQL, create `timesheet_project/.env`:

```env
DEBUG=True
SECRET_KEY=django-insecure-local-dev-key
ALLOWED_HOSTS=*
POSTGRES_DB=timesheet_for_you
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

## Production Deployment Configuration

Production should run with `DEBUG=False`, a strong `SECRET_KEY`, explicit host/origin allowlists, PostgreSQL, collected static files, and HTTPS-only cookies.

Required production environment variables:

```env
DEBUG=False
SECRET_KEY=replace-with-a-long-random-secret
ALLOWED_HOSTS=timesheet.example.com,www.timesheet.example.com
CSRF_TRUSTED_ORIGINS=https://timesheet.example.com,https://www.timesheet.example.com
POSTGRES_DB=timesheet_for_you
POSTGRES_USER=timesheet_for_you
POSTGRES_PASSWORD=replace-with-database-password
POSTGRES_HOST=replace-with-database-host
POSTGRES_PORT=5432
```

`ALLOWED_HOSTS` must contain explicit domains in production. `ALLOWED_HOSTS=*` is accepted only for local/debug development and will fail startup when `DEBUG=False`.

Production requires PostgreSQL configuration. When `DEBUG=False`, the app fails startup instead of falling back to SQLite if `POSTGRES_DB` / `DB_NAME` is missing.

Recommended production environment variables:

```env
DB_CONN_MAX_AGE=60
DB_SSL_REQUIRE=True
USE_WHITENOISE=True
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_REDIRECT_EXEMPT=^healthz/$
SECURE_HSTS_SECONDS=0
SECURE_HSTS_INCLUDE_SUBDOMAINS=False
SECURE_HSTS_PRELOAD=False
SECURE_REFERRER_POLICY=same-origin
```

`USE_X_FORWARDED_PROTO` defaults to `False`. Set `USE_X_FORWARDED_PROTO=True` only when Django is behind a trusted HTTPS-terminating proxy or load balancer that strips client-supplied forwarding headers and sets `X-Forwarded-Proto: https` itself.

`SECURE_HSTS_SECONDS` defaults to `0` so a new deployment can verify HTTPS behavior before sending long-lived browser HSTS headers. After HTTPS is confirmed stable for every production domain and subdomain you intend to serve, set `SECURE_HSTS_SECONDS=31536000`.

Static files are served through WhiteNoise when `USE_WHITENOISE=True`. Run this during deployment after installing dependencies and before starting the web process:

```bash
cd timesheet_project
python manage.py collectstatic --noinput
```

Suggested production release sequence:

```bash
cd timesheet_project
pip install -r requirements.txt
python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py check --deploy
```

The health check endpoint is unauthenticated and returns JSON at `/healthz/`:

```json
{"status": "ok"}
```

Use it for load balancer or platform health checks. It intentionally does not touch the database, so it confirms that Django can boot and route requests without making the app unhealthy during transient database maintenance.

`/healthz/` is included in `SECURE_REDIRECT_EXEMPT` by default so HTTP platform probes can receive a 200 response even when `SECURE_SSL_REDIRECT=True`. If your platform supports HTTPS health probes instead, you may remove that exemption and probe the HTTPS endpoint.

### Production Checklist

- Set `DEBUG=False`.
- Set a unique production `SECRET_KEY`.
- Set `ALLOWED_HOSTS` to the exact production domains; do not use `*`.
- Set `CSRF_TRUSTED_ORIGINS` to the exact HTTPS origins used by dashboard/browser clients.
- Run PostgreSQL in production; SQLite is only for local development and is rejected when `DEBUG=False`.
- Run `migrate` and `collectstatic` during deployment.
- Serve the app behind HTTPS.
- Keep `SESSION_COOKIE_SECURE=True` and `CSRF_COOKIE_SECURE=True` in production.
- Keep `SECURE_SSL_REDIRECT=True` unless HTTPS redirection is handled before traffic reaches Django.
- Set `USE_X_FORWARDED_PROTO=True` only behind a trusted proxy that strips incoming forwarding headers and sets `X-Forwarded-Proto` correctly.
- Keep `/healthz/` exempted from SSL redirects unless your health probe uses HTTPS.
- Set long-lived HSTS only after HTTPS is confirmed stable for all intended domains.
- Run `python manage.py check --deploy` before promoting a release.

## Optional S3 Media Storage

Local development uses the filesystem under `timesheet_project/media/` by default.

Set `USE_S3=True` in production to store uploaded parent signatures and generated timesheet PDFs in a private S3 bucket through Django's default file storage.

```env
USE_S3=True
AWS_STORAGE_BUCKET_NAME=timesheet-for-you-prod-media
AWS_S3_REGION_NAME=us-east-1
AWS_LOCATION=media
AWS_QUERYSTRING_AUTH=True
AWS_QUERYSTRING_EXPIRE=3600
AWS_S3_FILE_OVERWRITE=False
AWS_S3_CACHE_CONTROL=private, max-age=300
```

AWS credentials should be provided by the runtime environment, such as an IAM role or the standard `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` environment variables. The app only needs object-level access to the configured media prefix in an existing bucket; it does not create AWS infrastructure at runtime.

Example least-privilege IAM policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "TimesheetMediaObjectAccess",
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
      "Resource": "arn:aws:s3:::timesheet-for-you-prod-media/media/*"
    }
  ]
}
```

## Mobile Setup: React Native / Expo

Open a second terminal from the repo root:

```bash
cd mobile
npm install
```

Create `mobile/.env`.

For web development on the same machine as the backend:

```env
EXPO_PUBLIC_API_URL=http://localhost:8000
```

For testing on a physical phone with Expo Go, use your computer's local network IP address instead of `localhost`:

```env
EXPO_PUBLIC_API_URL=http://YOUR_COMPUTER_LOCAL_IP:8000
```

Example:

```env
EXPO_PUBLIC_API_URL=http://192.168.1.25:8000
```

Your phone and computer must be on the same Wi-Fi network.

## Run the Mobile App on a Phone

Start the Django backend first:

```bash
cd timesheet_project
python manage.py runserver 0.0.0.0:8000
```

Then start Expo:

```bash
cd mobile
npm start
```

Expo will show a QR code. Open the Expo Go app on your phone and scan the QR code.

You can also run platform-specific commands:

```bash
npm run android
npm run ios
```

Notes:

- Android physical device: use your computer's local IP in `EXPO_PUBLIC_API_URL`.
- iOS physical device: use your computer's local IP in `EXPO_PUBLIC_API_URL`.
- Android emulator may be able to use `http://10.0.2.2:8000`.
- iOS simulator can usually use `http://localhost:8000`.

## Run the Mobile App on Web

Start the backend:

```bash
cd timesheet_project
python manage.py runserver 0.0.0.0:8000
```

In another terminal, start Expo web:

```bash
cd mobile
npm run web
```

The web app should open in your browser. If it does not, follow the URL printed by Expo in the terminal.

For web, this value usually works in `mobile/.env`:

```env
EXPO_PUBLIC_API_URL=http://localhost:8000
```

## Common Development Flow

Use two terminals.

Terminal 1: backend

```bash
cd timesheet_project
source .venv/bin/activate
python manage.py runserver 0.0.0.0:8000
```

Terminal 2: mobile

```bash
cd mobile
npm start
```

## Troubleshooting

### The mobile app cannot connect to the API

If testing on a physical phone, do not use `localhost` in `EXPO_PUBLIC_API_URL`. Use your computer's local network IP address:

```env
EXPO_PUBLIC_API_URL=http://YOUR_COMPUTER_LOCAL_IP:8000
```

Also make sure:

- the backend is running with `0.0.0.0:8000`
- the phone and computer are on the same Wi-Fi network
- your firewall allows connections to port `8000`

### Login fails with connection errors

Confirm the token endpoint is reachable:

```txt
http://YOUR_API_HOST:8000/api/token/
```

### Database errors during startup

Run migrations:

```bash
cd timesheet_project
python manage.py migrate
```

### Static/media files during development

When `DEBUG=True`, Django serves media files from the local `media/` directory.

## MVP Notes

The app is intended to support this workflow:

1. Nanny logs into the mobile app.
2. Nanny adds time entries for one or more families during the week.
3. Parent signs individual entries on the nanny's phone.
4. Nanny submits the weekly timesheet.
5. Backend generates a PDF.
6. Admin reviews submitted timesheets and downloads PDFs.

Submitted timesheets can be edited and resubmitted until an office/admin user locks the week. Admins may add or edit internal notes, and submitted PDFs are replaced on resubmission before the week is locked.
