# Expo SDK 49 → 54 Breaking Changes Analysis

**Generated:** 2026-02-14  
**Task:** 76 - SDK 49→54 Breaking Changes Review  
**Current SDK:** 49 (expo@~49.0.0, react-native@0.72.10, expo-router@^2.0.15)

---

## Executive Summary

| Metric | Value |
|--------|-------|
| **SDK Versions Jumped** | 5 (49 → 50 → 51 → 52 → 53 → 54) |
| **React Native Upgrade** | 0.72.10 → 0.81.0 |
| **Total Breaking Changes** | 15+ significant changes |
| **HIGH Risk Areas** | 4 (expo-router, New Architecture, Android edge-to-edge, Metro exports) |
| **Files Requiring Changes** | 4 (package.json, app.json, QRScanner.tsx, scan.tsx, verify.tsx) |
| **Migration Complexity** | HIGH |

### Critical Findings

1. **expo-camera**: Our codebase ALREADY uses the new `CameraView` API (imported from 'expo-camera'), but the package.json has the old version (~13.4.4). This is a **MISMATCH** that needs immediate fixing.

2. **expo-router**: Major version jump from v2 → v3 (SDK 50) → v4 (SDK 52). Multiple breaking changes in navigation behavior.

3. **New Architecture**: Enabled by default in SDK 53, mandatory in SDK 55. Must test with third-party libraries.

4. **Android Edge-to-Edge**: Mandatory in SDK 54 (cannot disable). Affects UI layout.

---

## SDK 50 Changes (React Native 0.73)

### 1. expo-camera: New CameraView API
**What Changed:**
- Old `Camera` component from `expo-camera` is deprecated
- New `CameraView` component introduced under `expo-camera/next`
- Barcode scanning props changed: `onBarCodeScanned` → `onBarcodeScanned`

**Files Affected:**
- `apps/mobile/src/components/qr/QRScanner.tsx` (line 3)
- `apps/mobile/src/app/patient/scan.tsx` (line 3)
- `apps/mobile/src/app/pharmacist/verify.tsx` (line 11)

**Current Code Status:** ✅ ALREADY MIGRATED
```typescript
// Current code (ALREADY correct for SDK 50+):
import { CameraView, useCameraPermissions } from 'expo-camera';
<CameraView onBarcodeScanned={handler} />
```

**Migration Path:**
```typescript
// SDK 49 (old):
import { Camera } from 'expo-camera';
<Camera onBarCodeScanned={handler} />

// SDK 50+ (new):
import { CameraView } from 'expo-camera/next'; // SDK 50
// OR
import { CameraView } from 'expo-camera';      // SDK 51+
<CameraView onBarcodeScanned={handler} />
```

**Risk:** LOW (already using new API, but package version is old)

---

### 2. Expo Router v3
**What Changed:**
- API Routes (experimental server endpoints)
- Bundle splitting improvements
- Typed Routes changes
- `Href` type is no longer generic
- Local search params in nested layouts return strings instead of objects

**Files Affected:**
- `apps/mobile/src/app/_layout.tsx`
- All route files using `useLocalSearchParams()`

**Migration Path:**
```typescript
// SDK 49 (v2):
import { Href } from 'expo-router';
router.push<SomeType>('/route');

// SDK 50+ (v3):
import { Href } from 'expo-router';
router.push('/route'); // No generic type needed
```

**Risk:** MEDIUM (router.navigate() behavior changed in v4)

---

### 3. Android Build Requirements
**What Changed:**
- Android SDK 34 minimum
- AGP 8 required
- Java 17 required (was Java 11)
- Android minimum supported version bumped to API 23 (Android 6)

**Files Affected:**
- `apps/mobile/app.json`
- Build environment

**Migration Path:**
```json
// app.json
{
  "expo": {
    "android": {
      "minSdkVersion": 23
    }
  }
}
```

**Risk:** MEDIUM (CI/CD and local builds need Java 17)

---

### 4. iOS Build Requirements
**What Changed:**
- iOS minimum deployment target bumped to 13.4
- Xcode 15 required (was 14)

**Risk:** MEDIUM (CI/CD needs Xcode 15+)

---

### 5. @expo/vector-icons Updated
**What Changed:**
- Updated to react-native-vector-icons@10.0.0
- Ionicons: `ios-` and `md-` prefixes removed
- FontAwesome6 added

**Files Affected:**
- Any file using `@expo/vector-icons` with Ionicons

**Migration Path:**
```typescript
// Before:
<Ionicons name="ios-home" />

// After:
<Ionicons name="home" />
```

**Risk:** LOW (if using TypeScript, will catch errors)

---

## SDK 51 Changes (React Native 0.74)

### 6. expo-camera: Import Path Change
**What Changed:**
- `expo-camera/next` → `expo-camera` (new API is now default)
- Old API available at `expo-camera/legacy` until SDK 52

**Files Affected:**
- All files importing from 'expo-camera'

**Migration Path:**
```typescript
// SDK 50:
import { CameraView } from 'expo-camera/next';

// SDK 51+:
import { CameraView } from 'expo-camera';
```

**Risk:** LOW (already using correct import)

---

### 7. New Architecture Opt-In
**What Changed:**
- New Architecture (bridgeless) support added
- Opt-in for testing (not enabled by default)
- Many libraries adding support

**Migration Path:**
```json
// app.json - to opt in:
{
  "expo": {
    "newArchEnabled": true
  }
}
```

**Risk:** HIGH (must verify all native library compatibility)

---

### 8. expo-sqlite: Import Path Change
**What Changed:**
- `expo-sqlite/next` → `expo-sqlite`
- New API is now default

**Risk:** LOW (not using expo-sqlite in current codebase)

---

## SDK 52 Changes (React Native 0.76)

### 9. New Architecture Default for New Projects
**What Changed:**
- New projects have `newArchEnabled: true` by default
- Existing projects: opt-in only (not auto-enabled)
- Expo Go only supports New Architecture

**Risk:** HIGH (libraries must support New Architecture)

---

### 10. Expo Router v4 (via React Navigation v7)
**What Changed:**
- React Navigation upgraded to v7
- `router.navigate()` behavior changed - now behaves like `router.push()`
- Previously: navigate would go back to existing route in stack
- Now: always pushes new screen

**Files Affected:**
- All files using `router.navigate()`

**Current Code Analysis:**
```typescript
// apps/mobile/src/app/patient/scan.tsx (line 105)
router.replace('/patient/wallet'); // Uses replace - OK

// apps/mobile/src/app/pharmacist/verify.tsx (line 152)
router.push('/pharmacist/prescriptions/dispense'); // Uses push - OK
```

**Migration Path:**
```typescript
// To get old navigate behavior (go back if exists):
// Use router.dismiss() or router.dismissAll() first, then router.push()

// Before (v3):
router.navigate('/route'); // Would go back if in stack

// After (v4):
router.dismissTo('/route'); // New API to go back to route
// OR
router.push('/route'); // Always pushes
```

**Risk:** HIGH (navigation behavior changes could break UX)

---

### 11. Legacy Camera/SQLite Removed
**What Changed:**
- `expo-camera/legacy` removed
- `expo-sqlite/legacy` removed
- `expo-barcode-scanner` removed (was deprecated in SDK 50)

**Risk:** LOW (already using new APIs)

---

### 12. Minimum iOS Version Bump
**What Changed:**
- iOS minimum deployment target: 13.4 → 15.1
- Xcode 16 required (was 15)

**Risk:** MEDIUM (CI/CD needs Xcode 16)

---

### 13. Splash Screen Changes
**What Changed:**
- Migrated to Android 12+ SplashScreen API
- Full screen splash images no longer supported on Android
- Dark mode splash screens now officially supported

**Files Affected:**
- `apps/mobile/app.json`

**Risk:** MEDIUM (if using full-screen Android splash)

---

## SDK 53 Changes (React Native 0.79, React 19)

### 14. New Architecture Default Everywhere
**What Changed:**
- New Architecture enabled by default in ALL projects
- Must explicitly opt-out if not ready
- SDK 54 is last version with Legacy Architecture support

**Migration Path:**
```json
// To opt out temporarily:
{
  "expo": {
    "newArchEnabled": false
  }
}
```

**Risk:** HIGH (must verify library compatibility)

---

### 15. Metro Package.json Exports Enabled
**What Changed:**
- `package.json` `exports` field now enabled by default
- Some libraries may have compatibility issues
- Known issues with @supabase/supabase-js and @firebase/*

**Migration Path:**
```javascript
// metro.config.js - to opt out:
module.exports = {
  resolver: {
    unstable_enablePackageExports: false,
  },
};
```

**Risk:** MEDIUM (could cause bundling issues)

---

### 16. expo-background-fetch Deprecated
**What Changed:**
- Replaced by `expo-background-task`
- New library uses modern platform APIs

**Risk:** LOW (not using background fetch)

---

### 17. expo-av Deprecated
**What Changed:**
- Video replaced by `expo-video` (SDK 52)
- Audio replaced by `expo-audio` (SDK 53)
- Will be removed in SDK 55

**Risk:** LOW (not using expo-av)

---

### 18. Node.js Version Requirement
**What Changed:**
- Node 18 reached EOL
- Minimum Node 20 recommended

**Risk:** LOW (development environment change)

---

## SDK 54 Changes (React Native 0.81, React 19.1)

### 19. Edge-to-Edge Mandatory on Android
**What Changed:**
- Edge-to-edge enabled in all Android apps
- Cannot be disabled
- Android targets API 36 (Android 16)
- `react-native-edge-to-edge` no longer a dependency

**Files Affected:**
- All screen layouts
- `apps/mobile/app.json`

**Migration Path:**
```json
// app.json - configure navigation bar:
{
  "expo": {
    "androidNavigationBar": {
      "enforceContrast": false
    }
  }
}
```

**Risk:** HIGH (UI layout may need adjustments for system bars)

---

### 20. expo-file-system API Change
**What Changed:**
- New API (`expo-file-system/next`) is now default
- Old API available at `expo-file-system/legacy`
- Will be removed in SDK 55

**Risk:** LOW (not using expo-file-system directly)

---

### 21. expo-notifications Deprecated Exports Removed
**What Changed:**
- Various deprecated function exports removed
- Config plugin approach now required

**Risk:** LOW (not using expo-notifications)

---

### 22. SafeAreaView Deprecated
**What Changed:**
- React Native's `<SafeAreaView>` deprecated
- Must use `react-native-safe-area-context`

**Files Affected:**
- Any file using React Native's SafeAreaView

**Migration Path:**
```typescript
// Before:
import { SafeAreaView } from 'react-native';

// After:
import { SafeAreaView } from 'react-native-safe-area-context';
```

**Risk:** LOW (already using react-native-safe-area-context@4.6.3)

---

### 23. Minimum Xcode Version
**What Changed:**
- Minimum Xcode 16.1
- Xcode 26 recommended

**Risk:** MEDIUM (CI/CD needs Xcode 16.1+)

---

### 24. New Architecture Final Warning
**What Changed:**
- SDK 54 is LAST version with Legacy Architecture support
- SDK 55 will ONLY support New Architecture
- Reanimated v4 only supports New Architecture

**Risk:** HIGH (must migrate to New Architecture)

---

## Affected Files Summary

| File | Line(s) | Issue | Risk |
|------|---------|-------|------|
| `package.json` | 21 | expo@~49.0.0 → expo@^54.0.0 | HIGH |
| `package.json` | 23 | expo-camera@~13.4.4 → ~16.0.0 | MEDIUM |
| `package.json` | 26 | expo-router@^2.0.15 → ~4.0.0 | HIGH |
| `package.json` | 32 | react-native@0.72.10 → 0.81.0 | HIGH |
| `app.json` | 22-29 | Review camera plugin config | LOW |
| `app.json` | - | Add newArchEnabled field | HIGH |
| `_layout.tsx` | 1-13 | Router v4 compatibility | MEDIUM |

---

## Migration Checklist

### Pre-Migration
- [ ] Backup current codebase
- [ ] Run full test suite (baseline)
- [ ] Document current dependencies
- [ ] Check library compatibility with New Architecture

### Phase 1: SDK 50-51 (Core Updates)
- [ ] Update expo to ^51.0.0
- [ ] Update expo-camera to ~15.0.0
- [ ] Update expo-router to ~3.0.0
- [ ] Update React Native to 0.74
- [ ] Fix any expo-router v3 issues
- [ ] Test QR scanning functionality

### Phase 2: SDK 52 (Router v4 + New Arch Testing)
- [ ] Update expo to ^52.0.0
- [ ] Update expo-router to ~4.0.0
- [ ] Update React Native to 0.76
- [ ] Review router.navigate() usage
- [ ] Test with newArchEnabled: true
- [ ] Verify all native libraries work

### Phase 3: SDK 53 (React 19)
- [ ] Update expo to ^53.0.0
- [ ] Update React Native to 0.79
- [ ] Update React to 19.0.0
- [ ] Handle Metro exports issues
- [ ] Full regression testing

### Phase 4: SDK 54 (Final)
- [ ] Update expo to ^54.0.0
- [ ] Update React Native to 0.81
- [ ] Update React to 19.1.0
- [ ] Review Android edge-to-edge layout
- [ ] Test on Android 16 / iOS 26
- [ ] Final full test suite

### Post-Migration
- [ ] Update CI/CD to Xcode 16.1+
- [ ] Update CI/CD to Node 20+
- [ ] Update CI/CD to Java 17+
- [ ] Document any workarounds
- [ ] Train team on New Architecture

---

## Third-Party Library Compatibility

| Library | Current | SDK 54 Compatible | Notes |
|---------|---------|-------------------|-------|
| @react-native-async-storage/async-storage | 1.18.2 | ✅ Yes | New Arch compatible |
| axios | 1.13.5 | ✅ Yes | No native code |
| react-native-qrcode-svg | 6.3.21 | ⚠️ Check | Verify New Arch support |
| react-native-gesture-handler | 2.12.0 | ✅ Yes | Needs update |
| react-native-safe-area-context | 4.6.3 | ✅ Yes | New Arch compatible |
| react-native-screens | 3.22.0 | ✅ Yes | Needs update |

---

## Risk Assessment

### HIGH Risk
1. **New Architecture Migration** - Could break native library compatibility
2. **expo-router v4** - Navigation behavior changes
3. **Android Edge-to-Edge** - UI layout changes
4. **React 19** - Potential breaking changes in React patterns

### MEDIUM Risk
1. **React Native 0.72 → 0.81** - 9 minor versions, many internal changes
2. **Xcode Requirements** - CI/CD infrastructure updates needed
3. **Metro Package Exports** - Could cause bundling issues

### LOW Risk
1. **expo-camera** - Already using new API
2. **SafeAreaView** - Already using correct library
3. **Vector Icons** - TypeScript will catch issues

---

## Reference Links

- [Expo SDK 50 Changelog](https://expo.dev/changelog/2024/01-18-sdk-50)
- [Expo SDK 51 Changelog](https://expo.dev/changelog/2024/05-07-sdk-51)
- [Expo SDK 52 Changelog](https://expo.dev/changelog/2024/11-12-sdk-52)
- [Expo SDK 53 Changelog](https://expo.dev/changelog/sdk-53)
- [Expo SDK 54 Changelog](https://expo.dev/changelog/sdk-54)
- [React Native New Architecture](https://reactnative.dev/blog/2024/10/23/the-new-architecture-is-here)
- [Expo Router v4 Breaking Changes](https://reactnavigation.org/blog/2024/11/06/react-navigation-7.0)
