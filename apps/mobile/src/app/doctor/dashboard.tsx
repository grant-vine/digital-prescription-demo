import { useState, useEffect, useCallback } from 'react';
import { View, Text, TouchableOpacity, ActivityIndicator, StyleSheet, FlatList, RefreshControl, SafeAreaView, StatusBar } from 'react-native';
import { useRouter } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { api, Prescription } from '../../services/api';
import { DoctorTheme } from '../../components/theme/DoctorTheme';

const ThemedText = ({ style, type = 'body', children, ...props }: any) => {
  const baseStyle = {
    color: DoctorTheme.colors.text,
    ...DoctorTheme.typography[type as keyof typeof DoctorTheme.typography],
  };
  return <Text style={[baseStyle, style]} {...props}>{children}</Text>;
};

const ThemedButton = ({ title, onPress, variant = 'primary', disabled, loading, style, textStyle, testID }: any) => {
  const backgroundColor = variant === 'primary' ? DoctorTheme.colors.primary : 'transparent';
  const textColor = variant === 'primary' ? '#ffffff' : DoctorTheme.colors.primary;
  const borderColor = variant === 'outline' ? DoctorTheme.colors.border : 'transparent';

  const finalStyle = StyleSheet.flatten([
    styles.button,
    { backgroundColor, borderColor, borderWidth: variant === 'outline' ? 1 : 0 },
    disabled && styles.buttonDisabled,
    style
  ]);

  const finalTextStyle = StyleSheet.flatten([
    styles.buttonText,
    { color: textColor },
    textStyle,
    (disabled || loading) && { opacity: 0.6 }
  ]);

  return (
    <TouchableOpacity
      onPress={onPress}
      disabled={disabled || loading}
      style={finalStyle}
      testID={testID}
      activeOpacity={0.7}
    >
      {loading ? (
        <ActivityIndicator color={textColor} />
      ) : (
        <Text style={finalTextStyle}>{title}</Text>
      )}
    </TouchableOpacity>
  );
};

const DashboardHeader = ({ name, email, onLogout }: { name: string, email: string, onLogout: () => void }) => (
  <View style={styles.header}>
    <View style={styles.headerTop}>
      <View>
        <ThemedText type="h2" style={styles.greeting}>Welcome,</ThemedText>
        <ThemedText type="h1" style={styles.doctorName}>{name || 'Doctor'}</ThemedText>
        {email ? <ThemedText type="small" style={styles.doctorEmail}>{email}</ThemedText> : null}
      </View>
      <TouchableOpacity onPress={onLogout} style={styles.logoutButton}>
        <ThemedText style={styles.logoutText}>Logout</ThemedText>
      </TouchableOpacity>
    </View>
  </View>
);

const StatsCard = ({ label, value, color }: { label: string, value: number, color?: string }) => (
  <View style={styles.statCard}>
    <ThemedText type="h2" style={[styles.statValue, color ? { color } : null]}>{value}</ThemedText>
    <ThemedText type="small" style={styles.statLabel}>{label}</ThemedText>
  </View>
);

const PrescriptionCard = ({ prescription, onPress }: { prescription: Prescription, onPress: (id: number) => void }) => {
  const isActive = new Date(prescription.date_expires) > new Date();
  
  return (
    <TouchableOpacity 
      style={styles.card} 
      onPress={() => onPress(prescription.id)}
      testID="prescription-card"
      activeOpacity={0.7}
    >
      <View style={styles.cardHeader}>
        <ThemedText type="h3" style={styles.medicationName}>{prescription.medication_name}</ThemedText>
        <View style={[styles.statusBadge, isActive ? styles.statusActive : styles.statusExpired]}>
          <Text style={[styles.statusText, isActive ? styles.statusTextActive : styles.statusTextExpired]}>
            {isActive ? 'Active' : 'Expired'}
          </Text>
        </View>
      </View>
      
      <View style={styles.cardRow}>
        <ThemedText style={styles.cardLabel}>Patient ID:</ThemedText>
        <ThemedText style={styles.cardValue}>{prescription.patient_id}</ThemedText>
      </View>
      
      <View style={styles.cardRow}>
        <ThemedText style={styles.cardLabel}>Quantity:</ThemedText>
        <ThemedText style={styles.cardValue}>{prescription.quantity}</ThemedText>
      </View>
      
      <View style={styles.cardFooter}>
        <ThemedText type="small" style={styles.cardDate}>
          Issued: {new Date(prescription.date_issued).toLocaleDateString()}
        </ThemedText>
      </View>
    </TouchableOpacity>
  );
};

export default function DoctorDashboard() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [prescriptions, setPrescriptions] = useState<Prescription[]>([]);
  const [doctorName, setDoctorName] = useState('');
  const [doctorEmail, setDoctorEmail] = useState('');

  const fetchPrescriptions = useCallback(async () => {
    try {
      setError(null);
      const response = await api.getPrescriptions();
      setPrescriptions(response.items || []);
    } catch (err: any) {
      console.error('Fetch error:', err);
      setError(err.message || 'Failed to load prescriptions');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  const handleRefresh = useCallback(() => {
    setRefreshing(true);
    fetchPrescriptions();
  }, [fetchPrescriptions]);

  useEffect(() => {
    const checkAuthAndLoad = async () => {
      try {
        const token = await AsyncStorage.getItem('access_token');
        if (!token) {
router.replace('/doctor/auth');
          return;
        }

        const name = await AsyncStorage.getItem('doctor_name');
        const email = await AsyncStorage.getItem('doctor_email');
        if (name) setDoctorName(name);
        if (email) setDoctorEmail(email);

        await fetchPrescriptions();
      } catch (e) {
        router.replace('/doctor/auth');
      }
    };

    checkAuthAndLoad();
  }, [fetchPrescriptions, router]);

  const handleLogout = async () => {
    await AsyncStorage.removeItem('access_token');
    await AsyncStorage.removeItem('refresh_token');
    router.replace('/doctor/auth');
  };

  const handleNewPrescription = () => {
    router.push('/doctor/prescriptions/patient-select');
  };

  const handlePrescriptionTap = (id: number) => {
    router.push(`/doctor/prescriptions/${id}`);
  };

  const activeCount = prescriptions.filter(p => new Date(p.date_expires) > new Date()).length;
  const dispensedCount = prescriptions.length;

   const ListHeader = () => (
     <View>
       <DashboardHeader 
         name={doctorName} 
         email={doctorEmail} 
         onLogout={handleLogout} 
       />
       
       {loading && !refreshing && (
         <View style={styles.loadingContainer}>
           <ActivityIndicator size="large" color={DoctorTheme.colors.primary} testID="loading-spinner" />
           <ThemedText style={styles.loadingText}>Loading prescriptions...</ThemedText>
         </View>
       )}
       
       {error && (
         <View style={styles.errorContainer}>
           <ThemedText style={styles.errorText}>{error}</ThemedText>
           <ThemedButton 
             title="Refresh" 
             onPress={fetchPrescriptions} 
             variant="outline"
             style={styles.errorButton}
             testID="refresh-button"
           />
         </View>
       )}
       
       <View style={styles.statsContainer}>
         <StatsCard label="Total" value={prescriptions.length} color={DoctorTheme.colors.primary} />
         <StatsCard label="Active" value={activeCount} color={DoctorTheme.colors.success} />
         <StatsCard label="Dispensed" value={dispensedCount} color={DoctorTheme.colors.textSecondary} />
       </View>

       <View style={styles.actionContainer}>
         <ThemedButton 
           title="+ New Prescription" 
           onPress={handleNewPrescription}
           style={styles.createButton}
         />
       </View>

       <ThemedText type="h3" style={styles.sectionTitle}>Recent Prescriptions</ThemedText>
     </View>
   );

  const EmptyState = () => (
    <View style={styles.emptyState}>
      <ThemedText style={styles.emptyTitle}>No prescriptions yet</ThemedText>
      <ThemedText style={styles.emptySubtitle}>Get started by adding your first one</ThemedText>
    </View>
  );

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" backgroundColor={DoctorTheme.colors.background} />
      <FlatList
        data={prescriptions}
        renderItem={({ item }) => <PrescriptionCard prescription={item} onPress={handlePrescriptionTap} />}
        keyExtractor={(item) => item.id.toString()}
        contentContainerStyle={styles.listContent}
        ListHeaderComponent={ListHeader}
        ListEmptyComponent={EmptyState}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={handleRefresh}
            colors={[DoctorTheme.colors.primary]}
            tintColor={DoctorTheme.colors.primary}
            testID="refresh-control"
          />
        }
      />
    </SafeAreaView>
   );
}


const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: DoctorTheme.colors.background,
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: DoctorTheme.spacing.xl,
    backgroundColor: DoctorTheme.colors.background,
  },
  listContent: {
    padding: DoctorTheme.spacing.md,
    paddingBottom: DoctorTheme.spacing.xl * 2,
  },
  header: {
    marginBottom: DoctorTheme.spacing.lg,
  },
  headerTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  greeting: {
    color: DoctorTheme.colors.textSecondary,
    marginBottom: 2,
  },
  doctorName: {
    color: DoctorTheme.colors.primary,
    marginBottom: 2,
  },
  doctorEmail: {
    color: DoctorTheme.colors.textSecondary,
  },
  logoutButton: {
    padding: DoctorTheme.spacing.sm,
  },
  logoutText: {
    color: DoctorTheme.colors.error,
    fontWeight: '600',
  },
  statsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: DoctorTheme.spacing.lg,
    gap: DoctorTheme.spacing.sm,
  },
  statCard: {
    flex: 1,
    backgroundColor: DoctorTheme.colors.surface,
    padding: DoctorTheme.spacing.md,
    borderRadius: 16,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
    borderWidth: 1,
    borderColor: DoctorTheme.colors.border,
  },
  statValue: {
    fontSize: 28,
    marginBottom: 4,
  },
  statLabel: {
    color: DoctorTheme.colors.textSecondary,
    fontWeight: '600',
  },
  actionContainer: {
    marginBottom: DoctorTheme.spacing.lg,
  },
  createButton: {
    shadowColor: DoctorTheme.colors.primary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 4,
  },
  sectionTitle: {
    marginBottom: DoctorTheme.spacing.md,
    marginLeft: DoctorTheme.spacing.xs,
  },
  card: {
    backgroundColor: DoctorTheme.colors.surface,
    borderRadius: 16,
    padding: DoctorTheme.spacing.md,
    marginBottom: DoctorTheme.spacing.md,
    borderWidth: 1,
    borderColor: DoctorTheme.colors.border,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: DoctorTheme.spacing.sm,
  },
  medicationName: {
    color: DoctorTheme.colors.text,
    flex: 1,
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  statusActive: {
    backgroundColor: '#d1fae5', 
  },
  statusExpired: {
    backgroundColor: '#fee2e2', 
  },
  statusText: {
    fontSize: 12,
    fontWeight: '600',
  },
  statusTextActive: {
    color: DoctorTheme.colors.success,
  },
  statusTextExpired: {
    color: DoctorTheme.colors.error,
  },
  cardRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  cardLabel: {
    color: DoctorTheme.colors.textSecondary,
    fontSize: 14,
  },
  cardValue: {
    color: DoctorTheme.colors.text,
    fontSize: 14,
    fontWeight: '500',
  },
  cardFooter: {
    marginTop: DoctorTheme.spacing.sm,
    paddingTop: DoctorTheme.spacing.sm,
    borderTopWidth: 1,
    borderTopColor: '#f1f5f9',
  },
  cardDate: {
    color: DoctorTheme.colors.textSecondary,
    fontStyle: 'italic',
  },
  emptyState: {
    padding: DoctorTheme.spacing.xl,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: DoctorTheme.spacing.xl,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: DoctorTheme.colors.textSecondary,
    marginBottom: 8,
  },
  emptySubtitle: {
    color: DoctorTheme.colors.textSecondary,
    textAlign: 'center',
  },
  button: {
    height: 50,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  buttonText: {
    fontSize: 16,
    fontWeight: '600',
  },
   loadingText: {
     marginTop: DoctorTheme.spacing.md,
     color: DoctorTheme.colors.textSecondary,
   },
   loadingContainer: {
     paddingVertical: DoctorTheme.spacing.lg,
     alignItems: 'center',
     justifyContent: 'center',
     marginBottom: DoctorTheme.spacing.lg,
   },
   errorContainer: {
     backgroundColor: '#fef2f2',
     borderLeftWidth: 4,
     borderLeftColor: DoctorTheme.colors.error,
     padding: DoctorTheme.spacing.md,
     borderRadius: 8,
     marginBottom: DoctorTheme.spacing.lg,
   },
   errorButton: {
     marginTop: DoctorTheme.spacing.md,
   },
  errorText: {
    color: DoctorTheme.colors.error,
    marginBottom: DoctorTheme.spacing.lg,
    textAlign: 'center',
  },
});
