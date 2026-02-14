import { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  FlatList,
  ActivityIndicator,
  StyleSheet,
} from 'react-native';
import { router } from 'expo-router';
import { api } from '../../services/api';
import { PatientTheme } from '../../components/theme/PatientTheme';

interface Medication {
  name: string;
  dosage: string;
  frequency: string;
  duration: string;
  quantity: string;
  instructions: string;
}

interface Prescription {
  id: string | number;
  patient_name: string;
  doctor_name: string;
  doctor_did: string;
  medications: Medication[];
  created_at: string;
  expires_at?: string;
  date_expires?: string;
  status: 'active' | 'expired' | 'used';
  signature?: string;
  digital_signature?: string;
}

const ThemedText = ({ children, style, ...props }: any) => (
  <Text style={[{ color: PatientTheme.colors.text }, style]} {...props}>
    {children}
  </Text>
);

const ThemedButton = ({ title, onPress, disabled, testID }: any) => (
  <TouchableOpacity
    onPress={onPress}
    disabled={disabled}
    testID={testID}
    style={[styles.button, disabled && styles.buttonDisabled]}
  >
    <Text style={styles.buttonText}>{title}</Text>
  </TouchableOpacity>
);

export default function PatientWalletScreen() {
  const [prescriptions, setPrescriptions] = useState<Prescription[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'expired' | 'used'>('all');

  const loadPrescriptions = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      const result = await api.getPrescriptions();
      setPrescriptions((result.items || []) as unknown as Prescription[]);
    } catch (err: any) {
      setError('Failed to load prescriptions');
      setPrescriptions([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let isMounted = true;
    
    const fetchData = async () => {
      await Promise.resolve();
      if (!isMounted) return;
      await loadPrescriptions();
    };
    
    fetchData();
    
    return () => {
      isMounted = false;
    };
  }, [loadPrescriptions]);

  const handleRetry = () => {
    loadPrescriptions();
  };

  const getStatusBadgeColor = (status: string) => {
    if (status === 'active') return PatientTheme.colors.success;
    if (status === 'expired') return PatientTheme.colors.error;
    return '#6B7280';
  };

  const getStatusBadgeText = (status: string) => {
    if (status === 'active') return 'VALID';
    if (status === 'expired') return 'EXPIRED';
    return 'USED';
  };

  const filteredPrescriptions = prescriptions
    .filter((p) => {
      if (!searchQuery) return true;
      return p.medications.some((m) =>
        m.name.toLowerCase().includes(searchQuery.toLowerCase())
      );
    })
    .filter((p) => statusFilter === 'all' || p.status === statusFilter);

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator
          size="large"
          color={PatientTheme.colors.primary}
          testID="loading-spinner"
        />
        <ThemedText>Loading prescriptions...</ThemedText>
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.centerContainer}>
        <ThemedText testID="error-message" style={styles.errorText}>
          {error}
        </ThemedText>
        <ThemedButton title="Retry" onPress={handleRetry} testID="retry-button" />
      </View>
    );
  }

  if (filteredPrescriptions.length === 0) {
    return (
      <View style={styles.centerContainer}>
        <ThemedText style={styles.emptyText}>
          No prescriptions received yet. Check back soon to start managing your medications!
        </ThemedText>
      </View>
    );
  }

  const renderPrescriptionCard = ({ item }: { item: Prescription }) => {
    const medNames = item.medications.map((m) => m.name).join(', ');
    return (
      <TouchableOpacity
        style={styles.card}
        onPress={() => router.push(`/patient/prescriptions/${item.id}`)}
        testID="prescription-card"
      >
        <View style={styles.cardHeader}>
          <ThemedText style={styles.doctorName}>{item.doctor_name}</ThemedText>
          <View
            style={[
              styles.badge,
              { backgroundColor: getStatusBadgeColor(item.status) },
            ]}
          >
            <Text style={styles.badgeText}>{getStatusBadgeText(item.status)}</Text>
          </View>
        </View>
        <ThemedText style={styles.medications}>{medNames}</ThemedText>
         <View style={styles.footer}>
           <ThemedText style={styles.smallText}>
             {item.created_at.split('T')[0]} • {item.doctor_name}
           </ThemedText>
           <ThemedText style={styles.smallText}>
             Expires: {(item.expires_at || item.date_expires || '').split('T')[0]}
           </ThemedText>
         </View>
      </TouchableOpacity>
    );
  };

  return (
    <View style={styles.container} testID="patient-wallet">
      <ScrollView contentContainerStyle={styles.content}>
        <ThemedText style={styles.title}>Your Prescriptions</ThemedText>

        <TextInput
          placeholder="Search by medication name"
          placeholderTextColor="#94A3B8"
          value={searchQuery}
          onChangeText={setSearchQuery}
          style={styles.searchInput}
          testID="search-input"
        />

        <View style={styles.filterSection}>
          <ThemedText style={styles.filterLabel}>Filter:</ThemedText>
          <View style={styles.filterRow}>
            {(['all', 'active', 'expired', 'used'] as const).map((status) => (
              <TouchableOpacity
                key={status}
                style={[
                  styles.filterBtn,
                  statusFilter === status && styles.filterBtnActive,
                ]}
                onPress={() => setStatusFilter(status)}
                testID={`filter-${status}`}
              >
                <Text
                  style={[
                    styles.filterBtnText,
                    statusFilter === status && styles.filterBtnTextActive,
                  ]}
                >
                  {status === 'all' ? 'All' : status === 'active' ? 'Ready' : status === 'expired' ? 'Past Due' : 'Filled'}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        <FlatList
          data={filteredPrescriptions}
          renderItem={renderPrescriptionCard}
          keyExtractor={(p) => String(p.id)}
          scrollEnabled={false}
        />
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: PatientTheme.colors.background,
  },
  content: {
    padding: PatientTheme.spacing.lg,
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: PatientTheme.colors.background,
    padding: PatientTheme.spacing.lg,
  },
  title: {
    ...PatientTheme.typography.title,
    marginBottom: PatientTheme.spacing.lg,
  },
  searchInput: {
    backgroundColor: PatientTheme.colors.surface,
    borderWidth: 1,
    borderColor: '#CBD5E1',
    borderRadius: 8,
    padding: PatientTheme.spacing.md,
    marginBottom: PatientTheme.spacing.lg,
    color: PatientTheme.colors.text,
  },
  filterSection: {
    marginBottom: PatientTheme.spacing.lg,
  },
  filterLabel: {
    fontWeight: '600',
    marginBottom: PatientTheme.spacing.sm,
  },
  filterRow: {
    flexDirection: 'row',
    gap: PatientTheme.spacing.sm,
    flexWrap: 'wrap',
  },
  filterBtn: {
    paddingHorizontal: PatientTheme.spacing.md,
    paddingVertical: 6,
    borderRadius: 6,
    backgroundColor: '#E0F2FE',
    borderWidth: 1,
    borderColor: PatientTheme.colors.primary,
  },
  filterBtnActive: {
    backgroundColor: PatientTheme.colors.primary,
  },
  filterBtnText: {
    color: PatientTheme.colors.primary,
    fontSize: 13,
    fontWeight: '600',
  },
  filterBtnTextActive: {
    color: '#FFFFFF',
  },
  card: {
    backgroundColor: PatientTheme.colors.surface,
    borderRadius: 8,
    padding: PatientTheme.spacing.md,
    marginBottom: PatientTheme.spacing.md,
    borderWidth: 1,
    borderColor: '#CBD5E1',
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: PatientTheme.spacing.md,
  },
  doctorName: {
    fontSize: 16,
    fontWeight: '600',
    flex: 1,
  },
  badge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 4,
    marginLeft: PatientTheme.spacing.sm,
  },
  badgeText: {
    color: '#FFFFFF',
    fontSize: 11,
    fontWeight: '700',
  },
  medications: {
    fontSize: 14,
    fontWeight: '500',
    marginBottom: PatientTheme.spacing.md,
  },
  footer: {
    borderTopWidth: 1,
    borderTopColor: '#E2E8F0',
    paddingTop: PatientTheme.spacing.sm,
  },
  smallText: {
    fontSize: 12,
    color: PatientTheme.colors.textSecondary,
    marginVertical: 2,
  },
  errorText: {
    color: PatientTheme.colors.error,
    marginBottom: PatientTheme.spacing.lg,
    textAlign: 'center',
  },
  emptyText: {
    fontSize: 16,
    textAlign: 'center',
    fontStyle: 'italic',
  },
  button: {
    backgroundColor: PatientTheme.colors.primary,
    padding: PatientTheme.spacing.md,
    borderRadius: 8,
    alignItems: 'center',
  },
  buttonDisabled: {
    backgroundColor: '#94A3B8',
  },
  buttonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
});
