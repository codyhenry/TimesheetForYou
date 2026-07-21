export const TIMESHEET_DUE_NOTIFICATION_WINDOWS = [
  {
    id: 'friday_night',
    label: 'Friday night',
    description: 'Only notify when the current week timesheet is not submitted.',
  },
  {
    id: 'saturday_morning',
    label: 'Saturday morning',
    description: 'Only notify before the Saturday noon deadline when the current week timesheet is not submitted.',
  },
] as const;

export const PUSH_NOTIFICATION_SETUP_NOTES = [
  'Install expo-notifications when device-level reminders are ready to ship.',
  'Request notification permission after nanny login, not before authentication.',
  'Schedule reminders only after checking the current timesheet submitted status.',
  'Cancel pending reminders immediately after a successful submit or resubmit.',
];
