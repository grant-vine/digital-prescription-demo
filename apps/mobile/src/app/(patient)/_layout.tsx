import { Stack } from 'expo-router';
import { ThemeProvider } from '../../components/theme';

export default function PatientLayout() {
  return (
    <ThemeProvider role="patient">
      <Stack
        screenOptions={{
          headerStyle: {
            backgroundColor: '#0891B2',
          },
          headerTintColor: '#fff',
          headerTitleStyle: {
            fontWeight: 'bold',
          },
        }}
      >
        <Stack.Screen name="index" options={{ title: 'My Prescriptions' }} />
      </Stack>
    </ThemeProvider>
  );
}
