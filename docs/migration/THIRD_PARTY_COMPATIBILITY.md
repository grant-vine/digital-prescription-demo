# Third-Party Package Compatibility - Expo SDK 54

**Generated:** 2026-02-14  
**Task:** 77 - Third-Party Package Compatibility Check  
**Status:** ✅ COMPLETE

---

## Executive Summary

| Status | Count | Impact |
|--------|-------|--------|
| ✅ Compatible (No Changes) | 2 packages | axios, @playwright/test |
| ⚠️ Requires Updates | 5 packages | 3 HIGH priority, 2 MEDIUM |
| 🔴 Breaking Changes | 1 package | react-native-gesture-handler (Reanimated v4) |

**Total Estimated Migration Time:** 6-9 hours

---

## Critical Findings

### 🔴 CRITICAL: TypeScript MUST be Updated
- **Current:** 5.1.3 → **Required:** 5.3.3+
- **Why:** React 19.1.0 type definitions require TS 5.3+
- **Impact:** Build will fail without update
- **Effort:** Low (15 min + minor type fixes)
- **Priority:** BLOCKER for SDK 54 upgrade

### 🔴 BREAKING CHANGE: React Native Reanimated v4
- **Impact:** `useAnimatedGestureHandler` API **REMOVED**
- **Affected:** All gesture handling code (doctor signing, patient wallet interactions)
- **Migration:** Refactor to `Gesture` object API
- **Effort:** **HIGH** - 3-5 hours (2-4 hours per complex gesture)
- **Priority:** HIGH

### ⚠️ New Architecture is MANDATORY
- SDK 54 is the **FINAL release** supporting Legacy Architecture
- ALL native packages MUST support TurboModules/Fabric
- All recommended versions are compatible ✅

---

## Package Compatibility Matrix

| Package | Current Version | SDK 54 Compatible | Recommended Version | Priority | Effort | Breaking Changes |
|---------|----------------|-------------------|---------------------|----------|--------|------------------|
| **axios** | 1.13.5 | ✅ Yes | Keep current | LOW | 0 min | None |
| **@playwright/test** | 1.58.2 | ✅ Yes | Keep current | LOW | 0 min | None |
| **typescript** | 5.1.3 | ❌ No | ~5.3.3 | 🔴 HIGH | 30 min | React 19 types |
| **react-native-gesture-handler** | 2.12.0 | ⚠️ Update Required | ~2.28.0 | 🔴 HIGH | 3-5 hours | Reanimated v4 API |
| **react-native-screens** | 3.22.0 | ⚠️ Update Required | ~4.16.0 | 🔴 HIGH | 30 min | New Architecture |
| **react-native-safe-area-context** | 4.6.3 | ⚠️ Update Required | ~5.6.0 | 🔴 HIGH | 30 min | New Architecture |
| **react-native-qrcode-svg** | 6.3.21 | ✅ Yes | Keep current | ⚠️ MEDIUM | 15 min | Requires `react-native-svg@15.12.1` |

---

## Detailed Package Analysis

### 1. axios@^1.13.5 ✅

**Status:** ✅ Compatible - No changes needed

**Details:**
- Pure JavaScript library (no native code)
- Works with any React Native version
- No dependency on New Architecture
- No breaking changes between SDK 49 and SDK 54

**Action:** None required

---

### 2. @playwright/test@^1.58.2 ✅

**Status:** ✅ Compatible - No changes needed

**Details:**
- Dev dependency, runs outside React Native runtime
- Used for E2E testing only
- No interaction with native code
- Current version supports Node 20+ (SDK 54 requirement)

**Action:** None required

---

### 3. typescript@^5.1.3 🔴

**Status:** ❌ BLOCKER - Must upgrade to 5.3.3+

**Details:**
- React 19.1.0 requires TypeScript 5.3+ for type definitions
- Expo SDK 54 officially uses TypeScript 5.3.3
- Current version (5.1.3) will cause type errors with React 19

**Breaking Changes:**
- Stricter type checking in some areas
- May surface new type errors in existing code
- `const` type parameters (new feature)
- Improved type narrowing

**Migration Path:**
```bash
npm install -D typescript@~5.3.3
npx tsc --noEmit  # Check for new type errors
```

**Estimated Effort:** 30 minutes (15 min install + 15 min fix type errors)

**Priority:** 🔴 HIGH - Blocker for SDK 54 upgrade

---

### 4. react-native-gesture-handler@~2.12.0 🔴

**Status:** ⚠️ Requires Update - Major breaking changes

**Details:**
- Current: 2.12.0 (SDK 49)
- Required: 2.28.0+ (SDK 54)
- 16 minor version jump
- Reanimated v4 integration (major API change)

**Breaking Changes:**

#### 🔴 CRITICAL: `useAnimatedGestureHandler` REMOVED

The `useAnimatedGestureHandler` hook has been **completely removed** in Reanimated v4. All gesture handling code must be refactored to use the new `Gesture` object API.

**Old API (SDK 49):**
```typescript
import { useAnimatedGestureHandler } from 'react-native-reanimated';

const gestureHandler = useAnimatedGestureHandler({
  onStart: (_, ctx) => {
    ctx.startX = translateX.value;
  },
  onActive: (event, ctx) => {
    translateX.value = ctx.startX + event.translationX;
  },
  onEnd: (_) => {
    translateX.value = withSpring(0);
  }
});

<PanGestureHandler onGestureEvent={gestureHandler}>
  <Animated.View style={animatedStyle} />
</PanGestureHandler>
```

**New API (SDK 54):**
```typescript
import { Gesture } from 'react-native-gesture-handler';
import { useSharedValue, useAnimatedStyle } from 'react-native-reanimated';
import { GestureDetector } from 'react-native-gesture-handler';

const gesture = Gesture.Pan()
  .onBegin(() => {
    startX.value = translateX.value;
  })
  .onChange((event) => {
    translateX.value = startX.value + event.translationX;
  })
  .onFinalize(() => {
    translateX.value = withSpring(0);
  });

<GestureDetector gesture={gesture}>
  <Animated.View style={animatedStyle} />
</GestureDetector>
```

**Key Differences:**
- `onStart` → `onBegin` (lifecycle change)
- `onActive` → `onChange` (naming change)
- `onEnd` → `onFinalize` (lifecycle change)
- No more context object - use `useSharedValue()` for state
- Wrap in `GestureDetector` instead of `PanGestureHandler`

**Files to Check:**
```bash
grep -r "useAnimatedGestureHandler" apps/mobile/src/
grep -r "GestureHandler>" apps/mobile/src/
grep -r "onGestureEvent" apps/mobile/src/
```

**Migration Path:**
```bash
npx expo install react-native-gesture-handler@~2.28.0
npm install react-native-worklets@0.5.1  # New dependency required
```

Then refactor all gesture code to use new API.

**Estimated Effort:** 3-5 hours (2-4 hours per complex gesture)

**Priority:** 🔴 HIGH - Required for SDK 54, significant code changes

---

### 5. react-native-screens@~3.22.0 🔴

**Status:** ⚠️ Requires Update - New Architecture support

**Details:**
- Current: 3.22.0 (SDK 49)
- Required: 4.16.0+ (SDK 54)
- Major version bump for New Architecture compatibility
- Mostly drop-in replacement

**Breaking Changes:**
- v4 is **New Architecture only** (no Legacy Architecture fallback)
- `Screen` component API unchanged
- Native module interface changed (internal, no code changes needed)

**Migration Path:**
```bash
npx expo install react-native-screens@~4.16.0
cd ios && pod install && cd ..  # Update iOS native modules
```

**Estimated Effort:** 30 minutes (15 min install + 15 min testing)

**Priority:** 🔴 HIGH - Required for SDK 54

---

### 6. react-native-safe-area-context@4.6.3 🔴

**Status:** ⚠️ Requires Update - New Architecture support

**Details:**
- Current: 4.6.3 (SDK 49)
- Required: 5.6.0+ (SDK 54)
- v4 does **NOT** support New Architecture
- v5 is **New Architecture only**

**Breaking Changes:**

#### Import Source Change (CRITICAL)

**Old API (SDK 49):**
```typescript
// ❌ DEPRECATED in React Native 0.81
import { SafeAreaView } from 'react-native';
```

**New API (SDK 54):**
```typescript
// ✅ REQUIRED
import { SafeAreaView } from 'react-native-safe-area-context';
```

**Why:** React Native's built-in `SafeAreaView` is deprecated in 0.81 and will be removed in 0.82. The `react-native-safe-area-context` package is now the official recommendation.

**Files to Check:**
```bash
grep -r "from 'react-native'" apps/mobile/src/ | grep SafeAreaView
```

**Migration Path:**
```bash
npx expo install react-native-safe-area-context@~5.6.0
cd ios && pod install && cd ..  # Update iOS native modules
```

Then update all imports from `react-native` to `react-native-safe-area-context`.

**Estimated Effort:** 30 minutes (15 min install + 15 min import updates)

**Priority:** 🔴 HIGH - Required for SDK 54

---

### 7. react-native-qrcode-svg@^6.3.21 ⚠️

**Status:** ✅ Compatible - Minor dependency addition needed

**Details:**
- Current version (6.3.21) works with SDK 54
- Pure JavaScript library (no native code)
- **However:** Requires `react-native-svg@15.12.1` as peer dependency
- SDK 54 uses `react-native-svg@15.12.1` (New Architecture compatible)

**Action Required:**
```bash
npx expo install react-native-svg  # Expo will install correct version (15.12.1)
```

**Estimated Effort:** 15 minutes

**Priority:** ⚠️ MEDIUM - QR code generation will fail without `react-native-svg`

---

## Migration Sequence (Task 79)

### Phase 1: CRITICAL Dependencies (BEFORE SDK 54 upgrade)

```bash
# 1. Update TypeScript (MANDATORY - BLOCKER)
npm install -D typescript@~5.3.3

# 2. Update native packages (MANDATORY)
npx expo install react-native-gesture-handler@~2.28.0
npx expo install react-native-screens@~4.16.0
npx expo install react-native-safe-area-context@~5.6.0

# 3. Add new dependencies (REQUIRED)
npx expo install react-native-svg
npm install react-native-worklets@0.5.1

# 4. Update iOS native modules (if on macOS)
cd ios && pod install && cd ..
```

### Phase 2: Code Refactoring (Task 80)

1. **Refactor gesture handlers** (3-5 hours)
   - Search for `useAnimatedGestureHandler`
   - Refactor to `Gesture` object API
   - Replace `PanGestureHandler` with `GestureDetector`
   - Update lifecycle methods (`onStart` → `onBegin`, etc.)

2. **Update SafeAreaView imports** (30 minutes)
   - Search for `import { SafeAreaView } from 'react-native'`
   - Replace with `import { SafeAreaView } from 'react-native-safe-area-context'`

3. **Fix TypeScript 5.3 errors** (1-2 hours)
   - Run `npx tsc --noEmit`
   - Fix any new type errors
   - Update type annotations if needed

### Phase 3: Testing (Task 86-89)

- [ ] TypeScript compiles: `npx tsc --noEmit`
- [ ] Metro starts: `npx expo start --clear`
- [ ] Gesture handlers work (doctor signing, patient wallet interactions)
- [ ] QR code generation works
- [ ] QR code scanning works
- [ ] Safe areas render correctly on iOS/Android
- [ ] API calls work (axios)
- [ ] Playwright E2E tests pass

---

## Known Issues & Workarounds

### 1. Axios POST Network Error (expo/expo#40061)

**Issue:** Some users report network errors with `axios.post()` in Expo SDK 54.

**Root Cause:** NOT an axios issue - Metro bundler configuration problem in Expo SDK 54 beta.

**Status:** Expo team investigating, likely fixed in SDK 54 stable release.

**Workaround:** None needed for current axios version (1.13.5).

**References:**
- https://github.com/expo/expo/issues/40061

---

### 2. Bottom Sheet + Reanimated v4 (#2528)

**Issue:** `@gorhom/react-native-bottom-sheet` breaks with Reanimated v4 API changes.

**Solution:** Update to `@gorhom/bottom-sheet@5.2.4+` (supports Reanimated v4).

**Note:** We don't currently use bottom sheets, but good to know for future features.

**References:**
- https://github.com/gorhom/react-native-bottom-sheet/issues/2528

---

### 3. SVG Touch Handling (#2784)

**Issue:** Touchable SVG elements don't respond to touch in some cases with New Architecture.

**Solution:** Add explicit `pointerEvents="auto"` on touchable SVG elements.

**Example:**
```typescript
<Svg>
  <Rect pointerEvents="auto" onPress={handlePress} />
</Svg>
```

**Note:** May affect QR code display if using SVG touchables.

**References:**
- https://github.com/software-mansion/react-native-svg/issues/2784

---

### 4. useWorkletCallback Undefined

**Issue:** `useWorkletCallback is not a function` error after upgrading to Reanimated v4.

**Root Cause:** Reanimated v4 requires `react-native-worklets` as a separate dependency.

**Solution:**
```bash
npm install react-native-worklets@0.5.1
cd ios && pod install && cd ..
```

**Status:** Included in Phase 1 dependency updates above.

---

## Risk Assessment

### 🔴 HIGH Risk

1. **Gesture Handler Refactoring** - High effort (3-5 hours), potential for bugs
2. **TypeScript 5.3 Upgrade** - May surface hidden type errors
3. **New Architecture** - First-time enablement, compatibility unknown

### ⚠️ MEDIUM Risk

1. **SafeAreaView Import Changes** - Straightforward but affects many files
2. **react-native-screens v4** - Major version bump, potential edge cases

### ✅ LOW Risk

1. **axios** - No changes, well-tested
2. **@playwright/test** - Dev dependency, isolated
3. **react-native-qrcode-svg** - Pure JS, minimal changes

---

## Next Steps (Task 79)

1. ✅ Review this compatibility report
2. Update `apps/mobile/package.json` with recommended versions
3. Run `npx expo install --fix` to resolve peer dependencies
4. Update iOS native modules (`cd ios && pod install`)
5. Begin gesture handler refactoring (highest effort item)
6. Update SafeAreaView imports
7. Fix TypeScript 5.3 errors
8. Run full test suite

---

## Documentation References

- **Expo SDK 54 Changelog:** https://expo.dev/changelog/2024/11-12-sdk-54
- **React Native 0.81 Changelog:** https://github.com/facebook/react-native/releases/tag/v0.81.0
- **React 19.1.0 Changelog:** https://react.dev/blog/2025/01/15/react-19-1
- **Reanimated v4 Migration:** https://docs.swmansion.com/react-native-reanimated/docs/guides/migration
- **New Architecture:** https://reactnative.dev/docs/new-architecture-intro

---

**Report Status:** ✅ COMPLETE  
**Ready for Task 79:** ✅ YES  
**Blockers Identified:** 1 (TypeScript 5.3.3+ required)  
**Total Migration Time:** 6-9 hours
