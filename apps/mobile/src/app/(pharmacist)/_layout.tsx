import { Stack } from 'expo-router';
import { ThemeProvider } from '../../components/theme';

export default function PharmacistLayout() {
  return (
    <ThemeProvider role="pharmacist">
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
    </ThemeProvider>
  );
}
