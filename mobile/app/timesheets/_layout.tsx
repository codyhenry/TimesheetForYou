import { Stack } from 'expo-router';

export default function TimesheetsLayout() {
  return (
    <Stack>
      <Stack.Screen name="current" options={{ title: 'This Week' }} />
      <Stack.Screen name="past" options={{ title: 'Past Timesheets' }} />
      <Stack.Screen name="[id]" options={{ title: 'Timesheet' }} />
    </Stack>
  );
}
