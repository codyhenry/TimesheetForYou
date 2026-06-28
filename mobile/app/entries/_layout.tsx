import { Stack } from 'expo-router';

export default function EntriesLayout() {
  return (
    <Stack>
      <Stack.Screen name="new" options={{ title: 'New Entry' }} />
      <Stack.Screen name="[id]" options={{ title: 'Entry Details' }} />
      <Stack.Screen name="[id]/review" options={{ title: 'Parent Review' }} />
      <Stack.Screen name="[id]/signature" options={{ title: 'Signature' }} />
    </Stack>
  );
}
