export const calculateHoursPreview = (startTime: string, endTime: string): string | null => {
  if (!startTime || !endTime) return null;
  const [startH, startM] = startTime.split(':').map(Number);
  const [endH, endM] = endTime.split(':').map(Number);
  const startMinutes = startH * 60 + startM;
  const endMinutes = endH * 60 + endM;
  if (endMinutes <= startMinutes) return null;
  const diff = (endMinutes - startMinutes) / 60;
  return diff.toFixed(2);
};
