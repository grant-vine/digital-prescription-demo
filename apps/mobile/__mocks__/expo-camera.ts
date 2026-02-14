import React from 'react';
import { View } from 'react-native';

/**
 * Mock for expo-camera module used in tests
 * Provides mocked CameraView component and useCameraPermissions hook
 * Updated for Expo SDK 50+ API (Camera → CameraView)
 */

interface CameraProps {
  onBarcodeScanned?: (data: unknown) => void;
  children?: React.ReactNode;
  [key: string]: unknown;
}

export const CameraView = React.forwardRef(
  ({ children, ...props }: CameraProps, ref: React.Ref<View>) =>
    React.createElement(
      View,
      {
        ref,
        testID: 'camera-view-component',
        ...props,
      },
      children
    )
);

CameraView.displayName = 'MockCameraView';

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

export default {
  CameraView,
  useCameraPermissions,
  BarCodeScanner,
};
