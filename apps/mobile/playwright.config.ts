import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright configuration for E2E testing of Expo Web application.
 * 
 * This config:
 * - Tests against Expo Web dev server (http://localhost:8081)
 * - Records video of all test runs (1280x720, 30fps)
 * - Retries flaky tests up to 2 times
 * - Runs tests serially (not in parallel) for demo stability
 * - Uses Chrome for consistency with Expo Web
 * - Preserves test results and videos always
 */

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  timeout: 120000,
  retries: 2,
  expect: { timeout: 10000 },

  use: {
    baseURL: 'http://localhost:8081',
    video: {
      mode: 'on',
      size: { width: 1280, height: 720 },
    },
    viewport: { width: 1280, height: 720 },
    permissions: ['camera'],
  },

  projects: [
    {
      name: 'demo-video',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  webServer: {
    command: 'npx expo start --web --non-interactive',
    port: 8081,
    timeout: 120000,
    reuseExistingServer: true,
  },

  outputDir: 'test-results/',
  preserveOutput: 'always',
});
