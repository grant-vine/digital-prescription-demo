import React from 'react';
import { View } from 'react-native';

/**
 * Mock for expo-camera module used in tests
 * Provides mocked Camera component and useCameraPermissions hook
 */

interface CameraProps {
  onBarcodeScanned?: (data: unknown) => void;
  children?: React.ReactNode;
  [key: string]: unknown;
}

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
  Camera,
  useCameraPermissions,
  BarCodeScanner,
};
