# Third-Party Package Compatibility Report: Expo SDK 54 & React Native 0.81

**Generated:** February 14, 2026  
**Target SDK:** Expo SDK 54 (React Native 0.81.5, React 19.1.0)  
**Migration Context:** Upgrading from Expo SDK 49  
**New Architecture:** MANDATORY (SDK 54 is the FINAL release supporting Legacy Architecture)

---

## Executive Summary

| Status | Count | Packages |
|--------|-------|----------|
| ✅ Compatible (No Changes) | 2 | axios, @playwright/test |
| ⚠️ NEEDS UPDATE (Breaking Changes) | 5 | react-native-gesture-handler, react-native-screens, react-native-safe-area-context, react-native-qrcode-svg, typescript |
| 🔴 HIGH PRIORITY | 3 | gesture-handler, screens, safe-area-context |

**Critical Findings:**
- **ALL native packages MUST be updated** for New Architecture compatibility
- **Reanimated v4 breaking changes** affect gesture-handler usage patterns
- **TypeScript 5.3+** is REQUIRED (SDK 54 default, current 5.1.3 incompatible)

---

## Detailed Compatibility Matrix

### 1. **axios** (HTTP Client - No Native Code)

| Aspect | Details |
|--------|---------|
| **Current Version** | ^1.13.5 |
| **SDK 54 Tested** | ✅ 1.13.5+ (any version) |
| **Compatibility** | ✅ **COMPATIBLE** - No changes needed |
| **New Architecture** | ✅ N/A (Pure JS library) |
| **Breaking Changes** | None |
| **Migration Effort** | None required |
| **Known Issues** | ⚠️ [expo/expo#40061](https://github.com/expo/expo/issues/40061): POST request "Network Error" on clean SDK 54 project (NOT library issue - Metro config related) |

**Recommendation:** ✅ **KEEP CURRENT VERSION** - Axios is pure JavaScript with no native dependencies. Works with any RN/Expo version.

**Notes:**
- Any axios version from 1.x works with SDK 54
- The reported Network Error issue (#40061) is an Expo Metro config problem, not axios
- No action required for this package

---

### 2. **react-native-gesture-handler** (Touch Gestures)

| Aspect | Details |
|--------|---------|
| **Current Version** | ~2.12.0 |
| **SDK 54 Required** | **~2.28.0** (bundled version) |
| **Latest Available** | ~2.30.0 (as of Feb 2026) |
| **Compatibility** | ⚠️ **NEEDS UPDATE** |
| **New Architecture** | ✅ Supported in 2.28.0+ |
| **Upgrade Priority** | 🔴 **HIGH** |
| **Breaking Changes** | Major - See below |
| **Migration Effort** | Medium (API updates required) |

**Breaking Changes:**
1. **Reanimated v4 Integration:** 
   - ❌ `useAnimatedGestureHandler` REMOVED (deprecated in v3, removed in v4)
   - ✅ Use `Gesture` object API instead
   - Requires refactoring all gesture handlers

2. **New Architecture Requirements:**
   - Must be on v2.28.0+ for TurboModules/Fabric support
   - Legacy Architecture support dropped in latest versions

3. **Version Compatibility:**
   - 2.12.0 → 2.28.0 is a 16-minor-version jump
   - Multiple breaking changes across this range

**Recommended Version:** `~2.28.0` (SDK 54 bundled) or `~2.30.0` (latest, more stable)

**Migration Steps:**
```typescript
// OLD (v2.12.0 with Reanimated v3)
import { useAnimatedGestureHandler } from 'react-native-reanimated';

const gestureHandler = useAnimatedGestureHandler({
  onStart: (_, ctx) => { /* ... */ },
  onActive: (event, ctx) => { /* ... */ },
  onEnd: (_) => { /* ... */ }
});

// NEW (v2.28.0+ with Reanimated v4)
import { Gesture } from 'react-native-gesture-handler';
import { useSharedValue, useAnimatedStyle } from 'react-native-reanimated';

const gesture = Gesture.Pan()
  .onBegin(() => { /* ... */ })
  .onChange((event) => { /* ... */ })
  .onFinalize(() => { /* ... */ });
```

**Known Issues:**
- [#2528](https://github.com/gorhom/react-native-bottom-sheet/issues/2528): Bottom sheet issues with Reanimated v4 (third-party lib issue)
- Worklets dependency now required via `react-native-worklets` package

---

### 3. **react-native-screens** (Native Screen Management)

| Aspect | Details |
|--------|---------|
| **Current Version** | ~3.22.0 |
| **SDK 54 Required** | **~4.16.0** (bundled version) |
| **Latest Available** | ~4.23.0 (as of Feb 2026) |
| **Compatibility** | ⚠️ **NEEDS UPDATE** |
| **New Architecture** | ✅ Supported in 4.16.0+ |
| **Upgrade Priority** | 🔴 **HIGH** |
| **Breaking Changes** | Major version bump (3.x → 4.x) |
| **Migration Effort** | Low (mostly internal changes) |

**Breaking Changes:**
1. **Major Version Bump (3.x → 4.x):**
   - Internal architecture changes for New Architecture
   - Most public API remains compatible
   - Some screen options renamed/removed

2. **New Architecture Migration:**
   - Native module rewritten for TurboModules
   - Fabric renderer support added

**Recommended Version:** `~4.16.0` (SDK 54 bundled) or `~4.23.0` (latest)

**Migration Effort:** Low - Mostly drop-in replacement with `npx expo install react-native-screens`

**Known Issues:** None critical for SDK 54 migration

---

### 4. **react-native-safe-area-context** (Safe Area Handling)

| Aspect | Details |
|--------|---------|
| **Current Version** | 4.6.3 (fixed version) |
| **SDK 54 Required** | **~5.6.0** (bundled version) |
| **Latest Available** | 5.6.2 (as of Feb 2026) |
| **Compatibility** | ⚠️ **NEEDS UPDATE** |
| **New Architecture** | ✅ Supported in 5.x |
| **Upgrade Priority** | 🔴 **HIGH** |
| **Breaking Changes** | Major version bump (4.x → 5.x) |
| **Migration Effort** | Low |

**Breaking Changes:**
1. **Major Version Bump (4.6.3 → 5.6.0):**
   - 4.x DOES NOT support New Architecture
   - 5.x is New Architecture only
   - API largely unchanged (drop-in upgrade)

2. **React Native Core `SafeAreaView` Deprecated:**
   - RN 0.81 officially deprecates built-in `SafeAreaView`
   - Must use `react-native-safe-area-context` version

**Recommended Version:** `~5.6.0` or `5.6.2`

**Migration Steps:**
```typescript
// Ensure ALL imports use react-native-safe-area-context
// NOT react-native core

// ❌ OLD - DEPRECATED in RN 0.81
import { SafeAreaView } from 'react-native';

// ✅ NEW - Required
import { SafeAreaView } from 'react-native-safe-area-context';
```

**Migration Effort:** Minimal - Update package version + verify all imports

**Known Issues:** 
- Version pinning (4.6.3) vs. range (~5.6.0) - Update package.json to use tilde range
- Duplicate dependency warnings if multiple packages depend on different versions

---

### 5. **react-native-qrcode-svg** (QR Code Generation)

| Aspect | Details |
|--------|---------|
| **Current Version** | ^6.3.21 |
| **SDK 54 Tested** | 6.3.x (latest: 6.4.0) |
| **Compatibility** | ⚠️ **VERIFY REQUIRED** |
| **New Architecture** | ⚠️ Depends on `react-native-svg` (15.12.1+ required) |
| **Upgrade Priority** | MEDIUM |
| **Breaking Changes** | Indirect via `react-native-svg` |
| **Migration Effort** | Low |

**Dependencies:**
- **Primary:** `react-native-svg` (native module)
- SDK 54 bundles: `react-native-svg@15.12.1`
- Current project likely has older version

**Critical Consideration:**
- `react-native-qrcode-svg` itself is pure JS
- **BUT** depends on `react-native-svg` which has native code
- `react-native-svg` MUST be updated for New Architecture

**Recommended Action:**
1. Update `react-native-svg` to `15.12.1+` (via `npx expo install react-native-svg`)
2. Keep `react-native-qrcode-svg@^6.3.21` (current version fine)

**Known Issues:**
- [#2784](https://github.com/software-mansion/react-native-svg/issues/2784): SVG onPress handling with pointerEvents (SDK 54)
- Workaround exists in issue thread

**Migration Effort:** Low - Just update underlying SVG library

---

### 6. **typescript** (Type Checking)

| Aspect | Details |
|--------|---------|
| **Current Version** | ^5.1.3 |
| **SDK 54 Required** | **~5.3.3** (minimum 5.3.x) |
| **Latest Available** | 5.7.x (as of Feb 2026) |
| **Compatibility** | ⚠️ **NEEDS UPDATE** |
| **New Architecture** | ✅ N/A (tooling) |
| **Upgrade Priority** | 🔴 **HIGH** |
| **Breaking Changes** | Minor type checking differences |
| **Migration Effort** | Low-Medium |

**Why Update Required:**
1. **Expo SDK 54 uses TypeScript 5.3+:**
   - Type definitions generated with TS 5.3 features
   - 5.1.3 may fail to parse modern type definitions

2. **React 19 Type Definitions:**
   - React 19.1.0 types require TS 5.3+
   - Using 5.1.3 causes type errors with React hooks

**Recommended Version:** `~5.3.3` (SDK 54 default) or `^5.7.2` (latest stable)

**Breaking Changes:**
- Stricter type checking in some edge cases
- New type system features may surface previously hidden type errors

**Migration Steps:**
1. Update to `~5.3.3`: `npm install -D typescript@~5.3.3`
2. Run type check: `npx tsc --noEmit`
3. Fix any new type errors (likely minimal)

**Migration Effort:** Low - Mostly drop-in, may need minor type fixes

---

### 7. **@playwright/test** (E2E Testing - Dev Dependency)

| Aspect | Details |
|--------|---------|
| **Current Version** | ^1.58.2 |
| **SDK 54 Compatibility** | ✅ **COMPATIBLE** |
| **New Architecture** | ✅ N/A (dev tooling, runs outside app) |
| **Upgrade Priority** | LOW |
| **Breaking Changes** | None for SDK 54 |
| **Migration Effort** | None |

**Analysis:**
- Playwright tests run **outside** the React Native runtime
- Tests against the built app (web or compiled binaries)
- No direct dependency on Expo SDK version
- Version 1.58.2 is current as of Feb 2026

**Recommendation:** ✅ **KEEP CURRENT VERSION** - No changes needed

**Notes:**
- Can upgrade to 1.59.x+ if desired (independent of Expo)
- Ensure test suite runs against SDK 54 builds after migration
- Update any SDK 49-specific test fixtures/mocks

---

## Migration Priority & Sequence

### Phase 1: CRITICAL (Before Core Upgrade)
**Required for SDK 54 to function**

1. **typescript** → `~5.3.3`
   ```bash
   npm install -D typescript@~5.3.3
   ```

2. **react-native-gesture-handler** → `~2.28.0`
   ```bash
   npx expo install react-native-gesture-handler@~2.28.0
   ```

3. **react-native-screens** → `~4.16.0`
   ```bash
   npx expo install react-native-screens@~4.16.0
   ```

4. **react-native-safe-area-context** → `~5.6.0`
   ```bash
   npx expo install react-native-safe-area-context@~5.6.0
   ```

### Phase 2: VERIFY (After Core Upgrade)

5. **react-native-svg** → `15.12.1` (dependency of qrcode-svg)
   ```bash
   npx expo install react-native-svg
   ```

6. **Verify react-native-qrcode-svg** works with updated svg library
   - Run QR generation tests
   - No version change needed for qrcode-svg itself

### Phase 3: OPTIONAL

7. **axios** - No action required
8. **@playwright/test** - No action required

---

## Breaking Changes Summary

### High Impact (Code Changes Required)

1. **Gesture Handler + Reanimated v4**
   - **Change:** `useAnimatedGestureHandler` removed
   - **Action:** Refactor to `Gesture` object API
   - **Files Affected:** All gesture handling code
   - **Effort:** 2-4 hours per complex gesture

2. **SafeAreaView Import Changes**
   - **Change:** RN core version deprecated
   - **Action:** Update all imports to use `react-native-safe-area-context`
   - **Files Affected:** All screens using SafeAreaView
   - **Effort:** 30 minutes (search-replace)

### Medium Impact (Version Updates Only)

3. **TypeScript 5.3+**
   - **Change:** Minimum version bump
   - **Action:** Update package, fix any new type errors
   - **Files Affected:** Type definition files
   - **Effort:** 1-2 hours for type fixes

4. **react-native-screens 3.x → 4.x**
   - **Change:** Major version for New Architecture
   - **Action:** Update via expo install
   - **Files Affected:** Navigation configuration
   - **Effort:** 15 minutes (mostly automatic)

### Low Impact (Drop-in Upgrades)

5. **safe-area-context 4.x → 5.x**
   - **Change:** New Architecture rewrite
   - **Action:** Update via expo install
   - **Files Affected:** None (API compatible)
   - **Effort:** 5 minutes

---

## New Architecture Considerations

**SDK 54 Status:** Final release supporting BOTH Legacy + New Architecture  
**SDK 55+ Status:** New Architecture ONLY (no legacy support)

### What This Means:

1. **All Native Packages MUST Support New Architecture:**
   - TurboModules (native modules)
   - Fabric (rendering engine)
   - JSI (JavaScript Interface)

2. **Test with New Architecture Enabled:**
   ```json
   // app.json
   {
     "expo": {
       "plugins": [
         [
           "expo-build-properties",
           {
             "ios": { "newArchEnabled": true },
             "android": { "newArchEnabled": true }
           }
         ]
       ]
     }
   }
   ```

3. **Package Compatibility:**
   ✅ All listed packages support New Architecture in recommended versions
   ⚠️ Some third-party libraries may NOT support New Architecture yet

---

## Known Issues & Workarounds

### 1. Axios POST Network Error (SDK 54)
- **Issue:** [expo/expo#40061](https://github.com/expo/expo/issues/40061)
- **Cause:** Metro bundler configuration issue
- **Workaround:** Configure Metro properly (not an axios issue)
- **Status:** Expo team investigating

### 2. Reanimated v4 + Bottom Sheet
- **Issue:** [gorhom/react-native-bottom-sheet#2528](https://github.com/gorhom/react-native-bottom-sheet/issues/2528)
- **Cause:** `@gorhom/bottom-sheet` uses deprecated Reanimated v3 APIs
- **Workaround:** Update bottom-sheet to v5.2.4+ (supports Reanimated v4)
- **Status:** Fixed in latest version

### 3. SVG Touch Handling (SDK 54)
- **Issue:** [react-native-svg#2784](https://github.com/software-mansion/react-native-svg/issues/2784)
- **Cause:** pointerEvents behavior change in New Architecture
- **Workaround:** Explicit pointerEvents="auto" on touchable SVG elements
- **Status:** Tracking issue open

### 4. useWorkletCallback Undefined
- **Issue:** Reddit/GitHub reports after SDK 54 upgrade
- **Cause:** Missing `react-native-worklets` dependency
- **Workaround:** `npx expo install react-native-worklets@0.5.1`
- **Status:** Resolved by adding dependency

---

## Testing Checklist

After upgrading packages, verify:

- [ ] **TypeScript compiles:** `npx tsc --noEmit`
- [ ] **Metro starts:** `npx expo start --clear`
- [ ] **iOS builds:** `npx expo run:ios` (if using dev builds)
- [ ] **Android builds:** `npx expo run:android` (if using dev builds)
- [ ] **Gesture handlers work:** Test all pan/tap/swipe gestures
- [ ] **QR generation works:** Test QRDisplay component
- [ ] **QR scanning works:** Test QRScanner component
- [ ] **Safe areas render:** Verify notch/status bar handling
- [ ] **Navigation works:** Test all screen transitions
- [ ] **API calls work:** Test all axios requests
- [ ] **Playwright tests pass:** `npm test` (update fixtures if needed)

---

## Recommended package.json Changes

```json
{
  "dependencies": {
    "axios": "^1.13.5",                              // ✅ No change
    "react-native-qrcode-svg": "^6.3.21",           // ✅ No change
    "react-native-gesture-handler": "~2.28.0",      // ⚠️ UPDATE from ~2.12.0
    "react-native-screens": "~4.16.0",              // ⚠️ UPDATE from ~3.22.0
    "react-native-safe-area-context": "~5.6.0",     // ⚠️ UPDATE from 4.6.3
    "react-native-svg": "15.12.1",                  // ⚠️ ADD (dependency of qrcode-svg)
    "react-native-worklets": "0.5.1"                // ⚠️ ADD (dependency of Reanimated v4)
  },
  "devDependencies": {
    "@playwright/test": "^1.58.2",                  // ✅ No change
    "typescript": "~5.3.3"                          // ⚠️ UPDATE from ^5.1.3
  }
}
```

---

## Estimated Migration Time

| Task | Estimated Time |
|------|----------------|
| Update package versions | 15 minutes |
| Refactor gesture handlers (Reanimated v4) | 3-5 hours |
| Update SafeAreaView imports | 30 minutes |
| Fix TypeScript errors | 1-2 hours |
| Test QR functionality | 30 minutes |
| Run full test suite | 1 hour |
| **TOTAL** | **6-9 hours** |

**Note:** Time assumes moderate codebase with ~5-10 gesture handlers. Large apps with many gestures may take longer.

---

## References

- [Expo SDK 54 Changelog](https://expo.dev/changelog/sdk-54)
- [Expo SDK 54 Upgrade Guide](https://expo.dev/blog/expo-sdk-upgrade-guide)
- [React Native 0.81 Release Notes](https://reactnative.dev/blog/2025/08/12/react-native-0.81)
- [Reanimated v4 Migration Guide](https://docs.swmansion.com/react-native-reanimated/docs/guides/migration-from-3.x/)
- [React Native New Architecture](https://reactnative.dev/docs/the-new-architecture/landing-page)
- [Expo SDK 54 Third-Party Libraries](https://docs.expo.dev/versions/v54.0.0/sdk/third-party-overview/)

---

**Report Generated:** February 14, 2026  
**Next Task:** Update package.json and begin Phase 1 upgrades (Task 79)
