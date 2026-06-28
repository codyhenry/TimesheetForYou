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

Submitted timesheets are locked. Admins may add or edit internal notes, but submitted time entries, signatures, totals, and PDFs should not be changed for the MVP.
