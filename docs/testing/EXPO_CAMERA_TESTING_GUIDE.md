# Expo-Camera Testing Guide

**Date:** 2026-02-14  
**Project:** Digital Prescription Demo  
**Expo SDK:** 49 (expo-camera@13.4.4)

---

## Table of Contents

1. [Current Issue](#current-issue)
2. [Official Expo Testing Approach](#official-expo-testing-approach)
3. [Unit Testing Strategy](#unit-testing-strategy)
4. [E2E Testing Strategy](#e2e-testing-strategy)
5. [Recommended Fixes](#recommended-fixes)
6. [Best Practices](#best-practices)
7. [References](#references)

---

## Current Issue

### Problem
TypeScript error when importing `CameraView`:
```
Module 'expo-camera' has no exported member 'CameraView'
```

### Root Cause
- **Project uses:** Expo SDK 49 (`expo-camera@13.4.4`)
- **Code imports:** `CameraView` (introduced in SDK 50+)
- **SDK 49 exports:** `Camera` (not `CameraView`)

### Version Timeline
| SDK Version | Component Name | Status |
|-------------|----------------|--------|
| SDK 49 (current) | `Camera` | ✅ Available |
| SDK 50+ | `CameraView` | ❌ Not available in SDK 49 |

---

## Official Expo Testing Approach

### From Expo Documentation (2026)

**Expo's Recommendations:**
1. Use `jest-expo` preset ✅ (already configured)
2. Mock native modules that require hardware
3. Test component logic, NOT native camera functionality
4. Use `transformIgnorePatterns` to transpile Expo modules

**Example Configuration:**
```json
{
  "jest": {
    "preset": "jest-expo",
    "testEnvironment": "node",
    "transformIgnorePatterns": [
      "node_modules/(?!((jest-)?react-native|@react-native(-community)?)|expo(nent)?|@expo(nent)?/.*)"
    ]
  }
}
```

**What Expo Does NOT Provide:**
- ❌ No official mock for `expo-camera`
- ❌ No test utilities for camera components
- ❌ No guidance on E2E camera testing

**Conclusion:** Custom mocks required (which we have).

---

## Unit Testing Strategy

### Recommended Approach: Mock the Module

#### Current Mock Implementation
Location: `apps/mobile/__mocks__/expo-camera.ts`

```typescript
import React from 'react';
import { View } from 'react-native';

export const Camera = React.forwardRef(({ children, ...props }, ref) =>
  React.createElement(View, {
    ref,
    testID: 'camera-component',
    ...props,
  }, children)
);

export const useCameraPermissions = jest.fn(() => [
  { granted: true },
  jest.fn(),
]);

export const BarCodeScanner = {
  Constants: {
    BarCodeType: {
      qr: 'qr',
    },
  },
};
```

#### What to Test (Unit Level)

**1. Camera Permission Handling (4 tests)**
```typescript
describe('Camera Permissions', () => {
  it('requests permission on mount', () => {
    const { useCameraPermissions } = require('expo-camera');
    const mockRequest = jest.fn();
    useCameraPermissions.mockReturnValueOnce([
      { granted: undefined },
      mockRequest
    ]);

    render(<QRScanner onQRCodeScanned={jest.fn()} />);
    
    expect(mockRequest).toHaveBeenCalled();
  });

  it('displays error when permission denied', () => {
    const { useCameraPermissions } = require('expo-camera');
    useCameraPermissions.mockReturnValueOnce([
      { granted: false },
      jest.fn()
    ]);

    const { getByTestId } = render(<QRScanner onQRCodeScanned={jest.fn()} />);
    
    expect(getByTestId('permission-error')).toBeTruthy();
  });

  it('shows camera when permission granted', () => {
    const { useCameraPermissions } = require('expo-camera');
    useCameraPermissions.mockReturnValueOnce([
      { granted: true },
      jest.fn()
    ]);

    const { getByTestId } = render(<QRScanner onQRCodeScanned={jest.fn()} />);
    
    expect(getByTestId('camera-component')).toBeTruthy();
  });
});
```

**2. QR Code Detection (3 tests)**
```typescript
describe('QR Code Detection', () => {
  it('calls callback when valid QR detected', () => {
    const onScan = jest.fn();
    const { getByTestId } = render(<QRScanner onQRCodeScanned={onScan} />);
    
    const camera = getByTestId('camera-component');
    
    // Manually trigger barcode scan
    const mockCredential = {
      type: ['VerifiableCredential'],
      issuer: 'did:cheqd:testnet:abc123',
      credentialSubject: {
        prescriptionId: 'RX-123',
        patientName: 'John Doe',
        medications: []
      }
    };
    
    camera.props.onBarcodeScanned({
      data: JSON.stringify(mockCredential),
      type: 'qr'
    });
    
    expect(onScan).toHaveBeenCalledWith(
      expect.objectContaining({ issuer: 'did:cheqd:testnet:abc123' })
    );
  });

  it('validates credential structure', () => {
    const onError = jest.fn();
    const { getByTestId } = render(
      <QRScanner onQRCodeScanned={jest.fn()} onError={onError} />
    );
    
    const camera = getByTestId('camera-component');
    
    // Missing required fields
    camera.props.onBarcodeScanned({
      data: JSON.stringify({ type: 'invalid' }),
      type: 'qr'
    });
    
    expect(onError).toHaveBeenCalled();
  });
});
```

**3. Error Handling (5 tests)**
- Invalid JSON format
- Missing credential fields
- Wrong credential type
- Permission denied
- Camera not available

#### Testing Pattern: Manual Callback Triggering

Since the camera is mocked as a View, you **manually trigger** the `onBarcodeScanned` callback:

```typescript
const camera = getByTestId('camera-component');
camera.props.onBarcodeScanned({ data: '...', type: 'qr' });
```

This tests:
- ✅ QR data parsing logic
- ✅ Credential validation
- ✅ Error handling
- ✅ Callback invocation
- ❌ NOT the actual camera hardware

---

## E2E Testing Strategy

### Playwright Limitations

#### What CAN'T Be Done (Reliably)
❌ **Access real device camera in web context**
- Expo Web runs in browser, Playwright controls browser
- No direct access to native mobile camera APIs
- Web camera API (`getUserMedia`) is different from native

❌ **Mock camera feed consistently**
- Requires chromium-specific launch args
- Requires y4m video files (not mp4)
- Very flaky, breaks frequently
- Only works in Chromium (not webkit/firefox)

#### Research: Playwright Camera Mocking

From community research (Medium, GitHub issues):

**Chromium Approach (NOT RECOMMENDED):**
```typescript
// playwright.config.ts
export default defineConfig({
  projects: [{
    name: 'chromium',
    use: {
      ...devices['Desktop Chrome'],
      launchOptions: {
        args: [
          '--use-fake-device-for-media-stream',
          '--use-fake-ui-for-media-stream',
          '--use-file-for-fake-video-capture=/path/to/qr-code.y4m'
        ]
      }
    }
  }]
});
```

**Problems:**
1. Requires converting QR code images to y4m video format
2. File must be on disk, can't dynamically change
3. Chrome caches the video, making dynamic QR codes difficult
4. Very flaky, breaks with Chrome updates
5. No support for webkit/firefox

**GitHub Issue #36303:** Feature request for better camera mocking (still open as of 2026)

### Recommended E2E Approach

#### Option 1: Skip Camera Testing in E2E
**Best for:** MVP demo, limited resources

- ✅ Test manual entry fallback
- ✅ Test prescription display after scan
- ✅ Mock the scan result directly
- ❌ Skip actual camera flow

**Example:**
```typescript
test('pharmacist verifies prescription', async ({ page }) => {
  await page.goto('/pharmacist/verify');
  
  // Click manual entry instead of camera scan
  await page.click('text=Enter Code Manually');
  await page.fill('[placeholder="Prescription ID"]', 'RX-123');
  await page.click('text=Verify');
  
  // Verify results displayed
  await expect(page.locator('text=Dr. Sarah Johnson')).toBeVisible();
});
```

#### Option 2: Mock Camera API
**Best for:** Testing permission flows

```typescript
test.beforeEach(async ({ page }) => {
  // Mock getUserMedia to auto-grant permission
  await page.addInitScript(() => {
    navigator.mediaDevices.getUserMedia = async () => {
      return {
        getTracks: () => [{ stop: () => {} }],
        getVideoTracks: () => [{ stop: () => {} }],
      } as any;
    };
  });
});

test('camera permission granted', async ({ page }) => {
  await page.goto('/patient/scan');
  
  // Should not show permission error
  await expect(page.locator('text=permission denied')).not.toBeVisible();
});
```

#### Option 3: Test in Native App (Detox/Appium)
**Best for:** Production-ready testing

- Requires native build (not Expo Web)
- Uses Detox (iOS/Android) or Appium
- Can access real device camera
- Much more complex setup

**Not recommended for MVP demo.**

---

## Recommended Fixes

### Fix 1: Update Code to Use `Camera` (SDK 49 Compatible)

**Current Code (Broken):**
```typescript
import { CameraView, useCameraPermissions } from 'expo-camera';

<CameraView
  style={styles.camera}
  onBarcodeScanned={handleBarCodeScanned}
  barcodeScannerSettings={{ barcodeTypes: ['qr'] }}
/>
```

**Fixed Code (SDK 49):**
```typescript
import { Camera, useCameraPermissions } from 'expo-camera';

<Camera
  style={styles.camera}
  onBarCodeScanned={handleBarCodeScanned}
  barCodeScannerSettings={{
    barCodeTypes: ['qr'],
  }}
/>
```

**Changes:**
- `CameraView` → `Camera`
- `onBarcodeScanned` → `onBarCodeScanned`
- `barcodeScannerSettings` → `barCodeScannerSettings`

### Fix 2: Update Mock to Export `CameraView` Alias

**Add to `__mocks__/expo-camera.ts`:**
```typescript
export const Camera = React.forwardRef(({ children, ...props }, ref) =>
  React.createElement(View, {
    ref,
    testID: 'camera-component',
    ...props,
  }, children)
);

// Alias for SDK 50+ compatibility
export const CameraView = Camera;
```

This allows code to import either `Camera` or `CameraView` in tests.

### Fix 3: Update Test Imports

**Current Test (Broken):**
```typescript
import { CameraView } from 'expo-camera';
```

**Fixed Test:**
```typescript
// Just use the mock, don't import directly
jest.mock('expo-camera');
```

---

## Best Practices

### Unit Testing
1. ✅ **Mock the entire module** with `jest.mock('expo-camera')`
2. ✅ **Test logic, not hardware** (parsing, validation, callbacks)
3. ✅ **Manually trigger callbacks** via `camera.props.onBarcodeScanned()`
4. ✅ **Test permission states** by mocking `useCameraPermissions` return values
5. ✅ **Verify error handling** with invalid data

### E2E Testing
1. ❌ **Avoid camera mocking** (too flaky, too complex)
2. ✅ **Test manual entry** as primary E2E flow
3. ✅ **Mock getUserMedia** only for permission testing
4. ✅ **Test the fallback path** (QR scan failure → manual entry)
5. ✅ **Focus on user flows**, not camera internals

### Component Design
1. ✅ **Provide manual entry fallback** for QR scanner
2. ✅ **Make barcode handler testable** (accept callback prop)
3. ✅ **Expose testID** on all interactive elements
4. ✅ **Handle permission states explicitly** (granted, denied, undetermined)
5. ✅ **Validate QR data robustly** (JSON parsing, structure validation)

---

## Summary Table

| Testing Level | What to Test | How to Test | Recommendation |
|--------------|--------------|-------------|----------------|
| **Unit** | Permission logic | Mock `useCameraPermissions` | ✅ **PRIMARY APPROACH** |
| **Unit** | QR parsing | Manually trigger `onBarCodeScanned` | ✅ **PRIMARY APPROACH** |
| **Unit** | Error handling | Pass invalid data to callbacks | ✅ **PRIMARY APPROACH** |
| **Integration** | API integration | Mock API + manual scan trigger | ✅ Recommended |
| **E2E** | Camera hardware | Playwright camera mocking | ❌ **NOT RECOMMENDED** |
| **E2E** | Manual entry | Test fallback flow | ✅ **PRIMARY APPROACH** |
| **E2E** | Permission UI | Mock getUserMedia API | ✅ Optional |
| **Native E2E** | Real camera | Detox/Appium | ⚠️ Future enhancement |

---

## References

### Official Documentation
1. **Expo Camera API:** https://docs.expo.dev/versions/latest/sdk/camera/
2. **Expo Unit Testing:** https://docs.expo.dev/develop/unit-testing/
3. **jest-expo preset:** https://www.npmjs.com/package/jest-expo

### Community Resources
4. **Playwright Mock APIs:** https://playwright.dev/docs/next/mock-browser-apis
5. **Medium: Fake video capture with Playwright**  
   https://betterprogramming.pub/fake-video-capture-with-playwright-9314e6380755
6. **Medium: Simulating Webcam Access in Playwright**  
   https://medium.com/@sap7deb/simulating-webcam-access-in-playwright-f403dbbcb166
7. **GitHub Issue #36303:** Feature request for dynamic camera mocking  
   https://github.com/microsoft/playwright/issues/36303

### SDK Version Info
8. **Expo SDK 49 Release Notes:** Confirms `Camera` component
9. **Expo SDK 50 Release Notes:** Introduces `CameraView` (new API)
10. **expo-camera Changelog:** https://github.com/expo/expo/blob/main/packages/expo-camera/CHANGELOG.md

---

## Appendix: Complete Mock Example

**File:** `apps/mobile/__mocks__/expo-camera.ts`

```typescript
import React from 'react';
import { View } from 'react-native';

/**
 * Mock for expo-camera module
 * Compatible with SDK 49 (Camera) and SDK 50+ (CameraView)
 */

interface CameraProps {
  onBarCodeScanned?: (data: unknown) => void;
  onBarcodeScanned?: (data: unknown) => void; // SDK 50+ prop name
  barCodeScannerSettings?: unknown;
  barcodeScannerSettings?: unknown; // SDK 50+ prop name
  children?: React.ReactNode;
  [key: string]: unknown;
}

// SDK 49: Camera component
export const Camera = React.forwardRef(
  ({ children, ...props }: CameraProps, ref: React.Ref<View>) =>
    React.createElement(
      View,
      {
        ref,
        testID: 'camera-component',
        ...props,
      },
      children
    )
);

Camera.displayName = 'MockCamera';

// SDK 50+: CameraView is an alias of Camera
export const CameraView = Camera;

// Permission hook (works in both SDK 49 and 50+)
export const useCameraPermissions = jest.fn(() => [
  { granted: true, status: 'granted' },
  jest.fn().mockResolvedValue({ granted: true }),
]);

// Barcode scanner constants
export const BarCodeScanner = {
  Constants: {
    BarCodeType: {
      qr: 'qr',
      aztec: 'aztec',
      ean13: 'ean13',
      ean8: 'ean8',
      pdf417: 'pdf417',
      upc_e: 'upc_e',
      datamatrix: 'datamatrix',
      code39: 'code39',
      code93: 'code93',
      itf14: 'itf14',
      codabar: 'codabar',
      code128: 'code128',
      upc_a: 'upc_a',
    },
  },
};

export default {
  Camera,
  CameraView,
  useCameraPermissions,
  BarCodeScanner,
};
```

---

**End of Guide**
