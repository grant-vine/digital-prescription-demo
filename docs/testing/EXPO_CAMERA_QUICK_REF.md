# Expo-Camera Testing Quick Reference

**TL;DR:** Mock it in unit tests, skip it in E2E tests, test the manual entry fallback.

---

## The CameraView Error

**Error:**
```
Module 'expo-camera' has no exported member 'CameraView'
```

**Fix:**
```typescript
// WRONG (SDK 50+)
import { CameraView } from 'expo-camera';

// CORRECT (SDK 49)
import { Camera } from 'expo-camera';
```

---

## Unit Testing Pattern

```typescript
// 1. Mock the module
jest.mock('expo-camera');

// 2. Mock permission states
const { useCameraPermissions } = require('expo-camera');
useCameraPermissions.mockReturnValueOnce([
  { granted: true },
  jest.fn()
]);

// 3. Render component
const { getByTestId } = render(<QRScanner onQRCodeScanned={onScan} />);

// 4. Manually trigger scan
const camera = getByTestId('camera-component');
camera.props.onBarCodeScanned({
  data: JSON.stringify(credential),
  type: 'qr'
});

// 5. Verify callback
expect(onScan).toHaveBeenCalled();
```

---

## E2E Testing Pattern

```typescript
// DON'T test camera - too flaky
❌ await page.click('text=Scan QR Code');

// DO test manual entry
✅ await page.click('text=Enter Code Manually');
✅ await page.fill('[placeholder="Code"]', 'RX-123');
✅ await page.click('text=Submit');
```

---

## What to Test Where

| Test Type | Test This | Don't Test This |
|-----------|-----------|-----------------|
| **Unit** | ✅ Permission logic<br>✅ QR parsing<br>✅ Validation<br>✅ Error handling | ❌ Camera hardware<br>❌ Actual QR scanning |
| **E2E** | ✅ Manual entry flow<br>✅ Permission UI<br>✅ Error messages | ❌ Camera feed<br>❌ QR code detection |

---

## Mock File Location

**File:** `apps/mobile/__mocks__/expo-camera.ts`

**What it does:**
- Exports `Camera` component as a `View` with testID
- Exports `CameraView` as alias (SDK 50+ compatibility)
- Mocks `useCameraPermissions` to return granted state
- Provides `BarCodeScanner` constants

**How to use:**
```typescript
jest.mock('expo-camera'); // Automatically uses __mocks__/expo-camera.ts
```

---

## Common Mistakes

| ❌ Wrong | ✅ Right |
|---------|---------|
| Import `CameraView` | Import `Camera` |
| Test camera hardware | Test callback logic |
| Mock camera in Playwright | Test manual entry |
| Use real QR codes in tests | Pass JSON directly to callbacks |

---

## Quick Fixes Checklist

- [ ] Change `CameraView` → `Camera` in all files
- [ ] Change `onBarcodeScanned` → `onBarCodeScanned`
- [ ] Change `barcodeScannerSettings` → `barCodeScannerSettings`
- [ ] Update `__mocks__/expo-camera.ts` to export `CameraView` alias
- [ ] Update tests to manually trigger `onBarCodeScanned`
- [ ] Add manual entry fallback to UI

---

## Full Guide

See [`EXPO_CAMERA_TESTING_GUIDE.md`](./EXPO_CAMERA_TESTING_GUIDE.md) for:
- Detailed explanations
- Code examples
- Playwright limitations research
- Best practices
- References

---

**Last Updated:** 2026-02-14  
**Expo SDK:** 49  
**expo-camera:** 13.4.4
