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
        <Stack.Screen name="auth" options={{ title: 'Patient Login' }} />
      </Stack>
    </ThemeProvider>
  );
}
