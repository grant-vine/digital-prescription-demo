## Title
Mobile Wallet Deep Integration

## User Story
As a patient using a mobile device, I want deep integration with native mobile capabilities including biometric authentication, push notifications, offline access, and secure enclave key storage so that my digital prescription wallet is as convenient and secure as a native app experience.

## Description
This story delivers production-grade mobile wallet capabilities that go beyond a basic web wrapper. It includes native device integration, enhanced security through hardware-backed keys, rich notifications, background sync, and platform-specific optimizations for both iOS and Android.

## Acceptance Criteria

### Biometric Authentication
- [ ] Support platform biometric authentication:
  - iOS: Face ID and Touch ID
  - Android: Fingerprint and Face Unlock
- [ ] Biometric enrollment on first wallet setup
- [ ] Option to require biometric for:
  - App unlock
  - Prescription viewing
  - Sharing prescriptions
  - Critical operations (delete, export)
- [ ] Fallback to PIN/password if biometric fails
- [ ] Biometric status indicator in UI
- [ ] Graceful handling of biometric changes (new fingerprint enrolled)

### Secure Enclave Key Storage
- [ ] Hardware-backed key storage:
  - iOS: Secure Enclave / Keychain
  - Android: Keystore / StrongBox (if available)
- [ ] Private keys never leave secure hardware
- [ ] Key generation within secure enclave
- [ ] Key attestation for verification
- [ ] Automatic key rotation support
- [ ] Backup/recovery through encrypted key export (with user consent)

### Push Notifications
- [ ] Rich push notifications for:
  - New prescription received
  - Prescription expiring soon (7 days, 1 day)
  - Refill reminder
  - Pharmacy verification completed
  - Prescription shared successfully
- [ ] Notification actions:
  - "View" - opens prescription directly
  - "Share" - quick share to preferred pharmacy
  - "Dismiss" - clears notification
  - "Remind Later" - snooze notification
- [ ] Notification preferences:
  - Enable/disable per notification type
  - Quiet hours configuration
  - Priority levels
- [ ] Deep linking from notifications to specific screens

### Offline Capabilities
- [ ] Offline prescription access:
  - Cache all prescriptions locally (encrypted)
  - View prescription details without network
  - Show cached verification status
  - Display last sync timestamp
- [ ] Background sync:
  - Sync when connection restored
  - Periodic sync (configurable interval)
  - Push-triggered sync for urgent updates
- [ ] Offline actions queue:
  - Queue share requests for later
  - Queue verification requests
  - Execute when online
  - Show pending actions indicator

### Background Processing
- [ ] Background fetch for prescription updates
- [ ] Silent push notifications for data sync
- [ ] Background credential refresh before expiration
- [ ] Scheduled tasks (daily cleanup, periodic sync)
- [ ] Battery-optimized background activity

### Platform-Specific Features

#### iOS
- [ ] Widget support (Home Screen widget showing active prescriptions)
- [ ] App Clips for quick prescription sharing
- [ ] Siri Shortcuts ("Show my prescriptions", "Share with pharmacy")
- [ ] Handoff support (continue on other Apple devices)
- [ ] iCloud backup for app data (optional, encrypted)
- [ ] Dark Mode support
- [ ] Dynamic Type support for accessibility

#### Android
- [ ] App shortcuts (long-press menu)
- [ ] Notification channels with granular control
- [ ] Adaptive icons
- [ ] App standby bucket optimization
- [ ] Doze mode compatibility
- [ ] Material You dynamic theming
- [ ] Android 14+ enhanced credential manager integration

### Enhanced Security
- [ ] Screenshot protection for sensitive screens
- [ ] App switcher blur (hide content in recent apps)
- [ ] Auto-lock after inactivity (configurable: 1/5/15 minutes)
- [ ] Jailbreak/root detection with warnings
- [ ] Certificate pinning for API connections
- [ ] Network security config (disable cleartext traffic)
- [ ] Obfuscation and anti-tampering (ProGuard/R8)

### Deep Linking
- [ ] Universal Links / App Links:
  - `https://rxdemo.com/prescription/{id}` - open specific prescription
  - `https://rxdemo.com/share/{token}` - accept shared prescription
  - `https://rxdemo.com/verify/{code}` - quick verification
- [ ] Custom URL scheme fallback:
  - `rxdemo://prescription/{id}`
  - `rxdemo://share/{token}`
- [ ] QR code scanning with deep link handling
- [ ] NFC tag support for pharmacy check-in (future)

### Mobile-Specific UI/UX
- [ ] Pull-to-refresh for prescription list
- [ ] Swipe actions on prescription cards:
  - Swipe right: Quick share
  - Swipe left: Delete/archive
- [ ] Haptic feedback for actions
- [ ] Native share sheet integration
- [ ] Camera integration for QR scanning
- [ ] Contact picker for sharing
- [ ] Native date/time pickers

### Performance Optimization
- [ ] Image optimization for medication photos
- [ ] Lazy loading for prescription history
- [ ] Pagination for large prescription lists
- [ ] Debounced search
- [ ] Skeleton screens during loading
- [ ] Optimistic UI updates

### Mobile Settings
```
┌──────────────────────────────────────────┐
│ SETTINGS                                 │
├──────────────────────────────────────────┤
│                                          │
│ SECURITY                                 │
│ [ ] Biometric Authentication      On     │
│ [ ] Require Biometric for Share   On     │
│ Auto-Lock: After 5 minutes               │
│                                          │
│ NOTIFICATIONS                            │
│ [ ] New Prescriptions             On     │
│ [ ] Expiration Warnings           On     │
│ [ ] Refill Reminders              On     │
│ Quiet Hours: 22:00 - 07:00               │
│                                          │
│ OFFLINE                                  │
│ [ ] Enable Offline Mode           On     │
│ Sync Interval: Every 4 hours             │
│ Storage Used: 24.5 MB                    │
│                                          │
│ ABOUT                                    │
│ Version: 1.0.0                           │
│ Last Sync: 2 minutes ago                 │
│ Secure Enclave: ✓ Active                 │
└──────────────────────────────────────────┘
```

## API Integration Points

```
POST /api/v1/mobile/devices/register
DELETE /api/v1/mobile/devices/{id}
POST /api/v1/mobile/push/register
POST /api/v1/mobile/sync
GET  /api/v1/mobile/prescriptions/sync
POST /api/v1/mobile/verify-offline
```

## Technical Implementation

### Secure Storage (React Native)
```typescript
// Secure storage with hardware backing
import * as SecureStore from 'expo-secure-store';
import * as LocalAuthentication from 'expo-local-authentication';

class SecureWalletStorage {
  async storePrivateKey(keyId: string, privateKey: string): Promise<void> {
    // Uses iOS Keychain / Android Keystore
    await SecureStore.setItemAsync(
      `wallet_key_${keyId}`,
      privateKey,
      {
        keychainService: 'com.rxdigital.wallet',
        requireAuthentication: true, // Biometric required
      }
    );
  }
  
  async authenticateWithBiometric(): Promise<boolean> {
    const result = await LocalAuthentication.authenticateAsync({
      promptMessage: 'Authenticate to access your wallet',
      fallbackLabel: 'Use PIN',
      cancelLabel: 'Cancel',
    });
    return result.success;
  }
}
```

### Push Notifications (Expo)
```typescript
import * as Notifications from 'expo-notifications';

class PushNotificationService {
  async registerForPushNotifications(): Promise<string> {
    const { status } = await Notifications.requestPermissionsAsync();
    if (status !== 'granted') {
      throw new Error('Push notification permission denied');
    }
    
    const token = (await Notifications.getExpoPushTokenAsync()).data;
    await this.registerTokenWithBackend(token);
    return token;
  }
  
  setupNotificationHandlers() {
    // Foreground notifications
    Notifications.setNotificationHandler({
      handleNotification: async () => ({
        shouldShowAlert: true,
        shouldPlaySound: true,
        shouldSetBadge: true,
      }),
    });
    
    // Handle notification tap
    Notifications.addNotificationResponseReceivedListener(response => {
      const { prescriptionId } = response.notification.request.content.data;
      navigation.navigate('PrescriptionDetail', { id: prescriptionId });
    });
  }
}
```

### Offline Storage (WatermelonDB)
```typescript
import { Model, field } from '@nozbe/watermelondb';

class Prescription extends Model {
  static table = 'prescriptions';
  
  @field('prescription_id') prescriptionId!: string;
  @field('data') data!: string; // Encrypted JSON
  @field('synced_at') syncedAt!: number;
  @field('status') status!: string;
  
  async decrypt(): Promise<PrescriptionData> {
    const key = await SecureWalletStorage.retrieveKey();
    return decrypt(this.data, key);
  }
}

// Sync configuration
const syncConfig = {
  pullChanges: async ({ lastPulledAt }) => {
    const response = await fetch(
      `/api/v1/mobile/prescriptions/sync?since=${lastPulledAt}`
    );
    return { changes: await response.json(), timestamp: Date.now() };
  },
  pushChanges: async ({ changes }) => {
    await fetch('/api/v1/mobile/sync', {
      method: 'POST',
      body: JSON.stringify(changes),
    });
  },
};
```

## Notes

### Platform Requirements
- **iOS**: iOS 14+ (for full Secure Enclave support)
- **Android**: Android 10+ (API 29) with StrongBox preference
- **Expo SDK**: 49+ for latest native capabilities

### Privacy Considerations
- Location data only collected if explicitly permitted
- Biometric data never leaves device
- Encrypted backups only with user consent
- Minimal data collection for analytics

### Testing Requirements
- Test on physical devices (simulators lack secure hardware)
- Test biometric enrollment/removal scenarios
- Test offline mode thoroughly
- Test push notifications in foreground/background/killed states
- Test across different iOS/Android versions

### Performance Targets
- App launch: <3 seconds
- Biometric prompt: <1 second
- Prescription list load: <2 seconds (cached)
- Sync operation: <5 seconds
- Battery impact: <2% per hour background activity

## Estimation
- **Story Points**: 13
- **Time Estimate**: 5-7 days
- **Dependencies**: US-005 (Patient Wallet Setup), US-006 (Receive Prescription)

## Related Stories
- US-005: Patient Wallet Setup & Authentication
- US-006: Receive Prescription in Wallet
- US-007: View Prescription Details
- US-008: Share Prescription with Pharmacist
- US-018: DIDComm v2 Messaging (for push notifications)
