import { WeeklyTimesheet } from '../types';

export type TimesheetReminderWindow = 'friday_night' | 'saturday_morning';

export interface TimesheetReminder {
  window: TimesheetReminderWindow;
  title: string;
  message: string;
}

const SUBMITTED_STATUSES = new Set([
  'submitted_with_unsigned_entries',
  'submitted_fully_signed',
]);

const parseLocalDate = (value: string) => {
  const [year, month, day] = value.split('-').map(Number);
  return new Date(year, month - 1, day);
};

const isSameLocalDate = (first: Date, second: Date) =>
  first.getFullYear() === second.getFullYear() &&
  first.getMonth() === second.getMonth() &&
  first.getDate() === second.getDate();

export const isTimesheetSubmitted = (timesheet: Pick<WeeklyTimesheet, 'status'>) =>
  SUBMITTED_STATUSES.has(timesheet.status);

export const getInAppTimesheetReminder = (
  timesheet: Pick<WeeklyTimesheet, 'status' | 'week_end_date'>,
  now = new Date(),
): TimesheetReminder | null => {
  if (isTimesheetSubmitted(timesheet)) {
    return null;
  }

  const friday = parseLocalDate(timesheet.week_end_date);
  const saturday = new Date(friday);
  saturday.setDate(friday.getDate() + 1);
  const hour = now.getHours();

  if (isSameLocalDate(now, friday) && hour >= 17) {
    return {
      window: 'friday_night',
      title: 'Timesheet due soon',
      message: 'Your timesheet is due Saturday at noon. Submit it once your entries are ready.',
    };
  }

  if (isSameLocalDate(now, saturday) && hour >= 6 && hour < 12) {
    return {
      window: 'saturday_morning',
      title: 'Timesheet due today',
      message: 'Your timesheet is due at noon today. Submit it once your entries are ready.',
    };
  }

  return null;
};

export const getPushNotificationScaffoldStatus = () => ({
  available: false,
  reason:
    'Push notifications are scaffolded as a product path, but expo-notifications is not installed yet. Add expo-notifications before scheduling device notifications.',
});
