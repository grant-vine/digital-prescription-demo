# Mobile App

**Parent:** [Root AGENTS.md](../../AGENTS.md)

## OVERVIEW

React Native 0.81 + Expo SDK 54 + Expo Router v4. Three role-based route groups with distinct color themes. TypeScript strict mode.

**Updated**: 2026-02-14 - Upgraded to SDK 54 for app store compliance.

## STRUCTURE

```
apps/mobile/
├── src/
│   ├── app/                     # Expo Router file-based routing
│   │   ├── index.tsx            # Role selector (entry point)
│   │   ├── doctor/              # Doctor route group (blue #2563EB)
│   │   │   ├── _layout.tsx      # Group layout
│   │   │   ├── auth.tsx         # Login/register
│   │   │   ├── dashboard.tsx    # Main dashboard
│   │   │   └── prescriptions/   # sign, medication-entry, patient-select, qr-display, repeat-config
│   │   ├── patient/             # Patient route group (cyan #0891B2)
│   │   │   ├── _layout.tsx
│   │   │   ├── auth.tsx, wallet.tsx, scan.tsx
│   │   │   └── prescriptions/   # [id].tsx, share.tsx
│   │   └── pharmacist/          # Pharmacist route group (green #059669)
│   │       ├── _layout.tsx
│   │       ├── auth.tsx, verify.tsx
│   │       └── prescriptions/[id]/dispense.tsx
│   ├── components/
│   │   ├── qr/                  # QRDisplay.tsx, QRScanner.tsx, ManualEntry.tsx
│   │   ├── theme/               # ThemeProvider.tsx, DoctorTheme.ts, PatientTheme.ts, PharmacistTheme.ts, index.ts
│   │   ├── ThemedInput.tsx       # Text input with validation, icons, helper text
│   │   ├── InfoTooltip.tsx       # Modal-based help tooltip
│   │   ├── CardContainer.tsx     # Responsive card wrapper with shadow
│   │   ├── DemoLoginButtons.tsx  # Demo credential selector (DEMO_MODE only)
│   │   ├── StepIndicator.tsx     # Horizontal progress indicator
│   │   ├── ErrorBoundary.tsx     # App-wide crash protection
│   │   ├── RoleCard.tsx          # Expandable role selector card
│   │   └── WorkflowDiagram.tsx   # Responsive workflow visualization
│   ├── services/
│   │   └── api.ts               # Single axios client — all backend calls
│   └── tests/
│       └── structure.test.ts    # Validates file structure
├── e2e/                         # E2E specs: doctor, patient, pharmacist, error-scenarios
├── __mocks__/                   # expo-camera.ts, react-native-qrcode-svg/ (directory mock)
├── jest.config.js               # jest-expo preset, node environment
├── jest.setup.js                # Global test setup
├── tsconfig.json                # strict, noUnusedLocals, noUnusedParameters, @/* alias
├── babel.config.js              # Expo babel preset
└── package.json                 # @digital-prescription/mobile
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Add doctor screen | `src/app/doctor/` | File name = route path |
| Add patient screen | `src/app/patient/` | Dynamic routes: `[id].tsx` |
| Add pharmacist screen | `src/app/pharmacist/` | Nested: `prescriptions/[id]/dispense.tsx` |
| Add shared component | `src/components/` | Import via `@/components/...` |
| Add API method | `src/services/api.ts` | Single module, axios instance |
| Add theme | `src/components/theme/` | Export from `index.ts` |
| Add E2E test | `e2e/` | One spec per role |
| Add mock | `__mocks__/` | Match module path |

## CONVENTIONS

- **File-based routing**: Filename = route. `(group)/` = layout group (not in URL path)
- **`_layout.tsx`**: Required in each route group for navigation config
- **Tests colocated**: `screen.test.tsx` next to `screen.tsx`
- **Path alias**: `@/*` maps to `src/*` — use for all imports from src
- **Single API module**: All backend calls in `src/services/api.ts`
- **Themes**: Each role has a theme file; `ThemeProvider` wraps based on route group
- **StyleSheet**: Inline `StyleSheet.create()` per component (no external CSS-in-JS)

## ANTI-PATTERNS

- **DO NOT** use `as any` or `@ts-ignore` — strict TypeScript enforced
- **DO NOT** create separate API service files per feature — single `api.ts`
- **DO NOT** hard-code colors — use theme constants from `src/components/theme/`
- **DO NOT** skip `_layout.tsx` in route groups — Expo Router requires it

## COMMANDS

```bash
# From apps/mobile/
npx expo start --clear           # Dev server
npm test                         # All jest tests
npm test -- src/app/(doctor)/    # Tests in directory
npm test -- e2e/doctor.spec.ts   # E2E spec
npx tsc --noEmit                 # Type check
```

## DEMO MODE COMPONENTS

### Shared Components (Phases 1-2)

| Component | Purpose | Location |
|-----------|---------|----------|
| ThemedInput | Text input with validation, icons, helper text | `src/components/ThemedInput.tsx` |
| InfoTooltip | Modal-based help tooltip | `src/components/InfoTooltip.tsx` |
| CardContainer | Responsive card wrapper with shadow | `src/components/CardContainer.tsx` |
| DemoLoginButtons | Demo credential selector (DEMO_MODE only) | `src/components/DemoLoginButtons.tsx` |
| StepIndicator | Horizontal progress indicator | `src/components/StepIndicator.tsx` |
| ErrorBoundary | App-wide crash protection | `src/components/ErrorBoundary.tsx` |
| RoleCard | Expandable role selector card | `src/components/RoleCard.tsx` |
| WorkflowDiagram | Responsive workflow visualization | `src/components/WorkflowDiagram.tsx` |

### Demo Configuration

Environment variable `EXPO_PUBLIC_DEMO_MODE` controls demo features visibility. Set via Expo config `extra.demoMode` or directly as an environment variable during development.

---

## SDK 54 MIGRATION NOTES

**Completed**: 2026-02-14

### Key Changes
- Upgraded from SDK 49 → SDK 54 (5 major versions)
- React Native 0.72 → 0.81
- React 18.2 → 19.1
- TypeScript 5.3 → 5.6
- Expo Router v2 → v4

### Breaking Changes Fixed
- **React 19 ref pattern**: Animated values now use lazy initialization (refs cannot be accessed during render)
- **Camera API**: Already using CameraView (SDK 50+ API) - no migration needed
- **SafeAreaView**: Migrated to `react-native-safe-area-context` (5 files updated)
- **Jest transforms**: Added `expo-modules-core` to transformIgnorePatterns

### App Store Compliance
- **iOS**: Deployment target 15.1+ (meets April 2026 requirement for iOS 26 SDK)
- **Android**: Target SDK 35, Compile SDK 35 (meets Nov 2025 API 35 requirement)

### Camera Component Usage
- Component: `CameraView` from `expo-camera` (SDK 50+ modern API)
- Old API: `Camera` component (deprecated in SDK 50)
- Location: `src/components/qr/QRScanner.tsx`, `src/app/patient/scan.tsx`, `src/app/pharmacist/verify.tsx`
- All camera code already uses the modern API - no updates needed during migration
