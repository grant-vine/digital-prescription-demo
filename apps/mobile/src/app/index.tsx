import { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';

type Role = 'doctor' | 'patient' | 'pharmacist' | null;

export default function RoleSelector() {
  const [selectedRole, setSelectedRole] = useState<Role>(null);

  const roles = [
    {
      id: 'doctor',
      name: 'Doctor',
      color: '#2563EB',
      description: 'Create and sign prescriptions',
    },
    {
      id: 'patient',
      name: 'Patient',
      color: '#0891B2',
      description: 'Receive and manage prescriptions',
    },
    {
      id: 'pharmacist',
      name: 'Pharmacist',
      color: '#059669',
      description: 'Verify and dispense medications',
    },
  ];

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Digital Prescription Demo</Text>
      <Text style={styles.subtitle}>Select your role to continue</Text>

      <View style={styles.rolesContainer}>
        {roles.map((role) => (
          <TouchableOpacity
            key={role.id}
            style={[
              styles.roleButton,
              {
                backgroundColor:
                  selectedRole === role.id ? role.color : '#f0f0f0',
                borderColor: role.color,
              },
            ]}
            onPress={() => setSelectedRole(role.id as Role)}
          >
            <Text
              style={[
                styles.roleName,
                {
                  color: selectedRole === role.id ? '#fff' : role.color,
                },
              ]}
            >
              {role.name}
            </Text>
            <Text
              style={[
                styles.roleDescription,
                {
                  color: selectedRole === role.id ? '#fff' : '#666',
                },
              ]}
            >
              {role.description}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {selectedRole && (
        <TouchableOpacity
          style={[
            styles.continueButton,
            {
              backgroundColor:
                roles.find((r) => r.id === selectedRole)?.color || '#2563EB',
            },
          ]}
        >
          <Text style={styles.continueButtonText}>Continue as {selectedRole}</Text>
        </TouchableOpacity>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 20,
    backgroundColor: '#fff',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    marginBottom: 12,
    textAlign: 'center',
    color: '#000',
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
    marginBottom: 32,
    textAlign: 'center',
  },
  rolesContainer: {
    width: '100%',
    marginBottom: 24,
  },
  roleButton: {
    borderWidth: 2,
    borderRadius: 12,
    paddingVertical: 20,
    paddingHorizontal: 16,
    marginBottom: 12,
    alignItems: 'center',
  },
  roleName: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 8,
  },
  roleDescription: {
    fontSize: 14,
    textAlign: 'center',
  },
  continueButton: {
    width: '100%',
    paddingVertical: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  continueButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});
