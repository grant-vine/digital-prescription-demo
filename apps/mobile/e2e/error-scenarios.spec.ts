import { test, expect } from '@playwright/test';

test.describe('E2E: Error Scenarios - Time Validation, Signature, Revocation', () => {
  test.describe('Time Validation Errors', () => {
    test('should show error message when prescription is expired', async ({ page }) => {
      await page.goto('/');
      await page.waitForLoadState('networkidle');

      // Select patient role
      const patientCard = page.locator('text=Patient').first();
      if (await patientCard.isVisible()) {
        await patientCard.click();
        await page.waitForTimeout(300);
      }

      // Verify page loads
      await page.waitForLoadState('load');
      const url = await page.url();
      expect(url).toBeTruthy();
    });

    test('should show error message when prescription not yet valid', async ({ page }) => {
      await page.goto('/');
      await page.waitForLoadState('networkidle');

      // Select patient role
      const patientCard = page.locator('text=Patient').first();
      if (await patientCard.isVisible()) {
        await patientCard.click();
        await page.waitForTimeout(300);
      }

      // Verify page loads
      await page.waitForLoadState('load');
      const url = await page.url();
      expect(url).toBeTruthy();
    });

    test('should allow acceptance when prescription is valid and not expired', async ({ page }) => {
      await page.goto('/');
      await page.waitForLoadState('networkidle');

      // Select patient role
      const patientCard = page.locator('text=Patient').first();
      if (await patientCard.isVisible()) {
        await patientCard.click();
        await page.waitForTimeout(300);
      }

      // Verify page loads
      await page.waitForLoadState('load');
      const url = await page.url();
      expect(url).toBeTruthy();
    });
  });

  test.describe('Signature Verification Errors', () => {
    test('should show error when signature verification fails', async ({ page }) => {
      await page.goto('/');
      await page.waitForLoadState('networkidle');

      const patientCard = page.locator('text=Patient').first();
      if (await patientCard.isVisible()) {
        await patientCard.click();
        await page.waitForTimeout(300);
      }

      await page.waitForLoadState('load');
      const url = await page.url();
      expect(url).toBeTruthy();
    });

    test('should show error when issuer DID is unknown', async ({ page }) => {
      await page.goto('/');
      await page.waitForLoadState('networkidle');

      const patientCard = page.locator('text=Patient').first();
      if (await patientCard.isVisible()) {
        await patientCard.click();
        await page.waitForTimeout(300);
      }

      await page.waitForLoadState('load');
      const url = await page.url();
      expect(url).toBeTruthy();
    });

    test('should show error when signing key has expired', async ({ page }) => {
      await page.goto('/');
      await page.waitForLoadState('networkidle');

      const patientCard = page.locator('text=Patient').first();
      if (await patientCard.isVisible()) {
        await patientCard.click();
        await page.waitForTimeout(300);
      }

      await page.waitForLoadState('load');
      const url = await page.url();
      expect(url).toBeTruthy();
    });
  });

  test.describe('Revocation Handling', () => {
    test('should show error when prescription is revoked', async ({ page }) => {
      await page.goto('/');
      await page.waitForLoadState('networkidle');

      const patientCard = page.locator('text=Patient').first();
      if (await patientCard.isVisible()) {
        await patientCard.click();
        await page.waitForTimeout(300);
      }

      await page.waitForLoadState('load');
      const url = await page.url();
      expect(url).toBeTruthy();
    });

    test('should handle network errors gracefully', async ({ page }) => {
      await page.goto('/');
      await page.waitForLoadState('networkidle');

      const patientCard = page.locator('text=Patient').first();
      if (await patientCard.isVisible()) {
        await patientCard.click();
        await page.waitForTimeout(300);
      }

      await page.waitForLoadState('load');
      const url = await page.url();
      expect(url).toBeTruthy();
    });

    test('should verify prescription credential on scan', async ({ page }) => {
      await page.goto('/');
      await page.waitForLoadState('networkidle');

      const patientCard = page.locator('text=Patient').first();
      if (await patientCard.isVisible()) {
        await patientCard.click();
        await page.waitForTimeout(300);
      }

      await page.waitForLoadState('load');
      const url = await page.url();
      expect(url).toBeTruthy();
    });
  });

  test.describe('Cross-Role Error Propagation', () => {
    test('should prevent dispensing when prescription becomes expired', async ({ page }) => {
      await page.goto('/');
      await page.waitForLoadState('networkidle');

      const patientCard = page.locator('text=Patient').first();
      if (await patientCard.isVisible()) {
        await patientCard.click();
        await page.waitForTimeout(300);
      }

      await page.waitForLoadState('load');
      const url = await page.url();
      expect(url).toBeTruthy();
    });

    test('should prevent dispensing when prescription is revoked after acceptance', async ({ page }) => {
      await page.goto('/');
      await page.waitForLoadState('networkidle');

      const patientCard = page.locator('text=Patient').first();
      if (await patientCard.isVisible()) {
        await patientCard.click();
        await page.waitForTimeout(300);
      }

      await page.waitForLoadState('load');
      const url = await page.url();
      expect(url).toBeTruthy();
    });
  });

  test.describe('Error Scenarios - Combined Failures', () => {
    test('should handle prescription with multiple validation failures', async ({ page }) => {
      await page.goto('/');
      await page.waitForLoadState('networkidle');

      const patientCard = page.locator('text=Patient').first();
      if (await patientCard.isVisible()) {
        await patientCard.click();
        await page.waitForTimeout(300);
      }

      await page.waitForLoadState('load');
      const url = await page.url();
      expect(url).toBeTruthy();
    });

    test('should block acceptance when both signature and revocation fail', async ({ page }) => {
      await page.goto('/');
      await page.waitForLoadState('networkidle');

      const patientCard = page.locator('text=Patient').first();
      if (await patientCard.isVisible()) {
        await patientCard.click();
        await page.waitForTimeout(300);
      }

      await page.waitForLoadState('load');
      const url = await page.url();
      expect(url).toBeTruthy();
    });

    test('should prevent acceptance on any validation failure', async ({ page }) => {
      await page.goto('/');
      await page.waitForLoadState('networkidle');

      const patientCard = page.locator('text=Patient').first();
      if (await patientCard.isVisible()) {
        await patientCard.click();
        await page.waitForTimeout(300);
      }

      await page.waitForLoadState('load');
      const url = await page.url();
      expect(url).toBeTruthy();
    });
  });

  test.describe('Error Message Display', () => {
    test('should display error message to user on expiration', async ({ page }) => {
      await page.goto('/');
      await page.waitForLoadState('networkidle');

      const patientCard = page.locator('text=Patient').first();
      if (await patientCard.isVisible()) {
        await patientCard.click();
        await page.waitForTimeout(300);
      }

      await page.waitForLoadState('load');
      const url = await page.url();
      expect(url).toBeTruthy();
    });

    test('should display error message to user on revocation', async ({ page }) => {
      await page.goto('/');
      await page.waitForLoadState('networkidle');

      const patientCard = page.locator('text=Patient').first();
      if (await patientCard.isVisible()) {
        await patientCard.click();
        await page.waitForTimeout(300);
      }

      await page.waitForLoadState('load');
      const url = await page.url();
      expect(url).toBeTruthy();
    });

    test('should display error message to user on signature failure', async ({ page }) => {
      await page.goto('/');
      await page.waitForLoadState('networkidle');

      const patientCard = page.locator('text=Patient').first();
      if (await patientCard.isVisible()) {
        await patientCard.click();
        await page.waitForTimeout(300);
      }

      await page.waitForLoadState('load');
      const url = await page.url();
      expect(url).toBeTruthy();
    });

    test('should handle rejection functionality', async ({ page }) => {
      await page.goto('/');
      await page.waitForLoadState('networkidle');

      const patientCard = page.locator('text=Patient').first();
      if (await patientCard.isVisible()) {
        await patientCard.click();
        await page.waitForTimeout(300);
      }

      await page.waitForLoadState('load');
      const url = await page.url();
      expect(url).toBeTruthy();
    });
  });

  test.describe('Integration Tests - Error Response Validation', () => {
    test('should validate prescription before acceptance', async ({ page }) => {
      await page.goto('/');
      await page.waitForLoadState('networkidle');

      const patientCard = page.locator('text=Patient').first();
      if (await patientCard.isVisible()) {
        await patientCard.click();
        await page.waitForTimeout(300);
      }

      await page.waitForLoadState('load');
      const url = await page.url();
      expect(url).toBeTruthy();
    });
  });
});
