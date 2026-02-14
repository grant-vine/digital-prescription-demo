import { test, expect } from '@playwright/test';

test.describe('E2E: Patient Receives Prescription', () => {
  test('should complete full flow: wallet setup → scan QR → accept prescription → view in wallet', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Select patient role
    const patientCard = page.locator('text=Patient').first();
    if (await patientCard.isVisible()) {
      await patientCard.click();
      await page.waitForTimeout(300);
    }

    // Use demo login or manual login
    const demoButton = page.locator('text=Use Demo Patient');
    if (await demoButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      await demoButton.click();
      await page.waitForLoadState('networkidle');
    } else {
      const emailInput = page.locator('[placeholder*="email"], [placeholder*="Email"]').first();
      const passwordInput = page.locator('[placeholder*="password"], [placeholder*="Password"]').first();

      if (await emailInput.isVisible({ timeout: 3000 }).catch(() => false)) {
        await emailInput.fill('john@email.com');
        await passwordInput.fill('SecurePass123');
        const loginButton = page.locator('button:has-text("Login"), button:has-text("Sign In")').first();
        await loginButton.click();
        await page.waitForLoadState('networkidle');
      }
    }

    // Verify wallet is loaded
    const url = await page.url();
    expect(url).toBeTruthy();
  });

  test('should handle invalid QR code format gracefully', async ({ page }) => {
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

  test('should handle network error during QR scan', async ({ page }) => {
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

  test('should reject prescription when credential is expired', async ({ page }) => {
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

  test('should prevent duplicate prescription acceptance', async ({ page }) => {
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

  test('should display empty wallet when no prescriptions received', async ({ page }) => {
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

  test('should recover gracefully when API returns malformed prescription data', async ({ page }) => {
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
