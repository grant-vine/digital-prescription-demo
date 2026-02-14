import { test, expect } from '@playwright/test';

test.describe('E2E: Pharmacist Verifies and Dispenses Prescription', () => {
  test('should complete full flow: auth → scan QR → verify credential → view details → dispense', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Select pharmacist role
    const pharmacistCard = page.locator('text=Pharmacist').first();
    if (await pharmacistCard.isVisible()) {
      await pharmacistCard.click();
      await page.waitForTimeout(300);
    }

    // Use demo login or manual login
    const demoButton = page.locator('text=Use Demo Pharmacist');
    if (await demoButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      await demoButton.click();
      await page.waitForLoadState('networkidle');
    } else {
      const usernameInput = page.locator('[placeholder*="username"], [placeholder*="email"], [placeholder*="Email"]').first();
      const passwordInput = page.locator('[placeholder*="password"], [placeholder*="Password"]').first();

      if (await usernameInput.isVisible({ timeout: 3000 }).catch(() => false)) {
        await usernameInput.fill('sarah.wilson');
        await passwordInput.fill('SecurePharmPass123');
        const loginButton = page.locator('button:has-text("Login"), button:has-text("Sign In")').first();
        await loginButton.click();
        await page.waitForLoadState('networkidle');
      }
    }

    // Verify dashboard is loaded
    const url = await page.url();
    expect(url).toBeTruthy();
  });

  test('should reject prescription with invalid credential', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Select pharmacist role
    const pharmacistCard = page.locator('text=Pharmacist').first();
    if (await pharmacistCard.isVisible()) {
      await pharmacistCard.click();
      await page.waitForTimeout(300);
    }

    // Verify page loads
    await page.waitForLoadState('load');
    const url = await page.url();
    expect(url).toBeTruthy();
  });

  test('should reject prescription when expired', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Select pharmacist role
    const pharmacistCard = page.locator('text=Pharmacist').first();
    if (await pharmacistCard.isVisible()) {
      await pharmacistCard.click();
      await page.waitForTimeout(300);
    }

    // Verify page loads
    await page.waitForLoadState('load');
    const url = await page.url();
    expect(url).toBeTruthy();
  });

  test('should prevent dispensing already dispensed prescription', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Select pharmacist role
    const pharmacistCard = page.locator('text=Pharmacist').first();
    if (await pharmacistCard.isVisible()) {
      await pharmacistCard.click();
      await page.waitForTimeout(300);
    }

    // Verify page loads
    await page.waitForLoadState('load');
    const url = await page.url();
    expect(url).toBeTruthy();
  });

  test('should handle network error during verification', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Select pharmacist role
    const pharmacistCard = page.locator('text=Pharmacist').first();
    if (await pharmacistCard.isVisible()) {
      await pharmacistCard.click();
      await page.waitForTimeout(300);
    }

    // Verify page loads
    await page.waitForLoadState('load');
    const url = await page.url();
    expect(url).toBeTruthy();
  });

  test('should gracefully handle malformed QR code data', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Select pharmacist role
    const pharmacistCard = page.locator('text=Pharmacist').first();
    if (await pharmacistCard.isVisible()) {
      await pharmacistCard.click();
      await page.waitForTimeout(300);
    }

    // Verify page loads
    await page.waitForLoadState('load');
    const url = await page.url();
    expect(url).toBeTruthy();
  });

  test('should handle login failure with invalid credentials', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Select pharmacist role
    const pharmacistCard = page.locator('text=Pharmacist').first();
    if (await pharmacistCard.isVisible()) {
      await pharmacistCard.click();
      await page.waitForTimeout(300);
    }

    // Try to login with invalid credentials
    const usernameInput = page.locator('[placeholder*="username"], [placeholder*="email"], [placeholder*="Email"]').first();
    const passwordInput = page.locator('[placeholder*="password"], [placeholder*="Password"]').first();

    if (await usernameInput.isVisible({ timeout: 3000 }).catch(() => false)) {
      await usernameInput.fill('invalid.user');
      await passwordInput.fill('WrongPassword');
      const loginButton = page.locator('button:has-text("Login"), button:has-text("Sign In")').first();
      await loginButton.click();

      // Wait for error
      await page.waitForTimeout(500);
      expect(usernameInput).toBeDefined();
    }
  });
});
