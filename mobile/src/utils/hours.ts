const QUARTER_HOUR_MINUTES = 15;

export const calculateHoursPreview = (startTime: string, endTime: string): string | null => {
  if (!startTime || !endTime) return null;
  const [startH, startM] = startTime.split(':').map(Number);
  const [endH, endM] = endTime.split(':').map(Number);
  const startMinutes = startH * 60 + startM;
  const endMinutes = endH * 60 + endM;
  if (endMinutes <= startMinutes) return null;

  const roundedMinutes = Math.ceil((endMinutes - startMinutes) / QUARTER_HOUR_MINUTES) * QUARTER_HOUR_MINUTES;
  return (roundedMinutes / 60).toFixed(2);
};
