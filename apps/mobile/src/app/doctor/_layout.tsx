import { Stack } from 'expo-router';
import { ThemeProvider } from '../../components/theme';

export default function DoctorLayout() {
  return (
    <ThemeProvider role="doctor">
      <Stack
        screenOptions={{
          headerStyle: {
            backgroundColor: '#2563EB',
          },
          headerTintColor: '#fff',
          headerTitleStyle: {
            fontWeight: 'bold',
          },
        }}
      >
        <Stack.Screen name="auth" options={{ title: 'Doctor Login' }} />
      </Stack>
    </ThemeProvider>
  );
}
