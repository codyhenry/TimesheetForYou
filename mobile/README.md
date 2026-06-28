# TimesheetForYou Mobile App

React Native Expo mobile MVP for nannies to log weekly time entries, collect parent signatures, and submit timesheets to the existing Django backend.

## Prerequisites

- Node.js 18+
- npm
- Expo Go app or iOS/Android simulator
- Django backend running from `../timesheet_project`

## Setup

1. Copy the environment file:
   ```bash
   cp .env.example .env
   ```
2. Update `EXPO_PUBLIC_API_URL` if your backend is not running at `http://localhost:8000`.
3. Install dependencies:
   ```bash
   npm install
   ```
4. Start Expo:
   ```bash
   npx expo start
   ```

## Scripts

- `npm run start` - start Expo
- `npm run android` - open Android target
- `npm run ios` - open iOS target
- `npm run web` - open web target

## Features

- JWT login against the Django backend
- Current weekly timesheet overview
- Create, edit, and delete time entries
- Parent review and signature capture flow
- Submit timesheets with signed/unsigned status handling
- View current and past timesheets
- Open generated PDF submissions from the backend

## Notes

- The app expects the backend API routes defined in `timesheet_project/config/urls.py`.
- On a physical device, replace `localhost` with your computer's LAN IP address in `.env`.
