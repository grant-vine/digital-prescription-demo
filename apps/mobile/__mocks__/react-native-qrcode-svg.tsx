/* eslint-disable @typescript-eslint/no-explicit-any */
import React from 'react';
import { View, Text } from 'react-native';

export default function QRCode({ value, size }: any) {
  return React.createElement(
    View,
    { testID: 'qr-code-mock', style: { width: size, height: size } },
    React.createElement(Text, {}, `QR Code: ${value?.substring(0, 20)}...`)
  );
}
