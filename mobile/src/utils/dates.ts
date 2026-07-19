import { endOfWeek, format, parseISO, startOfWeek } from 'date-fns';

export const formatDate = (dateStr: string): string => {
  return format(parseISO(dateStr), 'EEE M/d');
};

export const formatDateLong = (dateStr: string): string => {
  return format(parseISO(dateStr), 'EEEE, MMMM d');
};

export const formatTime = (timeStr: string): string => {
  const [hours, minutes] = timeStr.split(':');
  const hour = parseInt(hours, 10);
  const ampm = hour >= 12 ? 'PM' : 'AM';
  const displayHour = hour % 12 || 12;
  return `${displayHour}:${minutes} ${ampm}`;
};

export const formatLocalDateTime = (dateTimeStr?: string | null): string => {
  if (!dateTimeStr) {
    return '—';
  }

  const date = new Date(dateTimeStr);
  if (Number.isNaN(date.getTime())) {
    return '—';
  }

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date);
};

export const getCurrentWeekRange = (): { start: string; end: string } => {
  const now = new Date();
  const monday = startOfWeek(now, { weekStartsOn: 1 });
  const sunday = endOfWeek(now, { weekStartsOn: 1 });
  return {
    start: format(monday, 'yyyy-MM-dd'),
    end: format(sunday, 'yyyy-MM-dd'),
  };
};

export const formatWeekRange = (startDate: string, endDate: string): string => {
  const start = parseISO(startDate);
  const end = parseISO(endDate);
  return `${format(start, 'MMM d')} – ${format(end, 'MMM d, yyyy')}`;
};