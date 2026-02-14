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
        <Stack.Screen name="auth" options={{ title: 'Pharmacist Login' }} />
      </Stack>
    </ThemeProvider>
  );
}
