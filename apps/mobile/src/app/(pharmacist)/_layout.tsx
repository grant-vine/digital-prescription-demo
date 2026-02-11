import { Stack } from 'expo-router';

export default function PharmacistLayout() {
  return (
    <Stack
      screenOptions={{
        headerStyle: {
          backgroundColor: '#059669',
        },
        headerTintColor: '#fff',
        headerTitleStyle: {
          fontWeight: 'bold',
        },
      }}
    >
      <Stack.Screen name="index" options={{ title: 'Verify Prescriptions' }} />
    </Stack>
  );
}
