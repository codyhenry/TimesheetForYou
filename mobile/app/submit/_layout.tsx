import { Stack } from 'expo-router';

export default function SubmitLayout() {
  return (
    <Stack>
      <Stack.Screen name="[timesheetId]" options={{ title: 'Submit Timesheet' }} />
      <Stack.Screen name="confirmation" options={{ title: 'Confirmation' }} />
    </Stack>
  );
}
