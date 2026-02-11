module.exports = {
  preset: 'jest-expo',
  testMatch: ['**/?(*.)+(spec|test).[jt]s?(x)'],
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/**/index.ts',
  ],
  setupFilesAfterEnv: [],
  testEnvironment: 'node',
  transformIgnorePatterns: [
    'node_modules/(?!(react-native|expo|expo-router|@react-native)/)',
  ],
};
