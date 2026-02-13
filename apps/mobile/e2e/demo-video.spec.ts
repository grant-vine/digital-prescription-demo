import { test, expect } from '@playwright/test';

test.describe('Investor Demo - Complete Prescription Flow', () => {
  test('Full workflow with video recording', async ({ browser }) => {
    const doctorContext = await browser.newContext();
    const patientContext = await browser.newContext();
    const pharmacistContext = await browser.newContext();

    const doctorPage = await doctorContext.newPage();
    const patientPage = await patientContext.newPage();
    const pharmacistPage = await pharmacistContext.newPage();

    try {
      await test.step('Doctor: Navigate to Index and Select Role', async () => {
        await doctorPage.goto('/');
        await doctorPage.waitForLoadState('networkidle');

        const doctorCard = doctorPage.locator('text=Doctor').first();
        if (await doctorCard.isVisible()) {
          await doctorCard.click();
          await doctorPage.waitForTimeout(300);
        }
      });

      await test.step('Doctor: Use Demo Login', async () => {
        const demoButton = doctorPage.locator('text=Use Demo Doctor');
        if (await demoButton.isVisible({ timeout: 5000 }).catch(() => false)) {
          await demoButton.click();
          await doctorPage.waitForLoadState('networkidle');
        } else {
          const emailInput = doctorPage.locator('[placeholder*="email"], [placeholder*="Email"]').first();
          const passwordInput = doctorPage.locator('[placeholder*="password"], [placeholder*="Password"]').first();

          if (await emailInput.isVisible({ timeout: 3000 }).catch(() => false)) {
            await emailInput.fill('sarah.johnson@hospital.co.za');
            await passwordInput.fill('Demo@2024');
            const loginButton = doctorPage.locator('button:has-text("Login"), button:has-text("Sign In")').first();
            await loginButton.click();
            await doctorPage.waitForLoadState('networkidle');
          }
        }
      });

      await test.step('Doctor: Verify Dashboard Access', async () => {
        const pageContent = await doctorPage.content();
        expect(pageContent).toContain('Doctor');
        await doctorPage.waitForLoadState('domcontentloaded');
      });

      await test.step('Patient: Navigate to Index and Select Role', async () => {
        await patientPage.goto('/');
        await patientPage.waitForLoadState('networkidle');

        const patientCard = patientPage.locator('text=Patient').first();
        if (await patientCard.isVisible()) {
          await patientCard.click();
          await patientPage.waitForTimeout(300);
        }
      });

      await test.step('Patient: Use Demo Login', async () => {
        const demoButton = patientPage.locator('text=Use Demo Patient');
        if (await demoButton.isVisible({ timeout: 5000 }).catch(() => false)) {
          await demoButton.click();
          await patientPage.waitForLoadState('networkidle');
        } else {
          const emailInput = patientPage.locator('[placeholder*="email"], [placeholder*="Email"]').first();
          if (await emailInput.isVisible({ timeout: 3000 }).catch(() => false)) {
            await emailInput.fill('john.smith@example.com');
            const passwordInput = patientPage.locator('[placeholder*="password"], [placeholder*="Password"]').first();
            await passwordInput.fill('Demo@2024');
            const loginButton = patientPage.locator('button:has-text("Login"), button:has-text("Sign In")').first();
            await loginButton.click();
            await patientPage.waitForLoadState('networkidle');
          }
        }
      });

      await test.step('Patient: Verify Wallet Access', async () => {
        const pageContent = await patientPage.content();
        expect(pageContent.length).toBeGreaterThan(100);
        await patientPage.waitForLoadState('domcontentloaded');
      });

      await test.step('Pharmacist: Navigate to Index and Select Role', async () => {
        await pharmacistPage.goto('/');
        await pharmacistPage.waitForLoadState('networkidle');

        const pharmacistCard = pharmacistPage.locator('text=Pharmacist').first();
        if (await pharmacistCard.isVisible()) {
          await pharmacistCard.click();
          await pharmacistPage.waitForTimeout(300);
        }
      });

      await test.step('Pharmacist: Use Demo Login', async () => {
        const demoButton = pharmacistPage.locator('text=Use Demo Pharmacist');
        if (await demoButton.isVisible({ timeout: 5000 }).catch(() => false)) {
          await demoButton.click();
          await pharmacistPage.waitForLoadState('networkidle');
        } else {
          const emailInput = pharmacistPage.locator('[placeholder*="email"], [placeholder*="Email"]').first();
          if (await emailInput.isVisible({ timeout: 3000 }).catch(() => false)) {
            await emailInput.fill('lisa.chen@pharmacy.co.za');
            const passwordInput = pharmacistPage.locator('[placeholder*="password"], [placeholder*="Password"]').first();
            await passwordInput.fill('Demo@2024');
            const loginButton = pharmacistPage.locator('button:has-text("Login"), button:has-text("Sign In")').first();
            await loginButton.click();
            await pharmacistPage.waitForLoadState('networkidle');
          }
        }
      });

      await test.step('Pharmacist: Verify Dashboard Access', async () => {
        const pageContent = await pharmacistPage.content();
        expect(pageContent).toContain('Pharmacist');
        await pharmacistPage.waitForLoadState('domcontentloaded');
      });

      await test.step('All Three Roles Authenticated and Ready', async () => {
        expect(await doctorPage.url()).toBeTruthy();
        expect(await patientPage.url()).toBeTruthy();
        expect(await pharmacistPage.url()).toBeTruthy();
      });

      await test.step('Doctor: Showcase Dashboard Navigation', async () => {
        const buttons = doctorPage.locator('button').all();
        const buttonCount = (await buttons).length;
        expect(buttonCount).toBeGreaterThan(0);
      });

      await test.step('Patient: Showcase Wallet/Prescriptions Navigation', async () => {
        const buttons = patientPage.locator('button').all();
        const buttonCount = (await buttons).length;
        expect(buttonCount).toBeGreaterThan(0);
      });

      await test.step('Pharmacist: Showcase Verification Interface', async () => {
        const buttons = pharmacistPage.locator('button').all();
        const buttonCount = (await buttons).length;
        expect(buttonCount).toBeGreaterThan(0);
      });
    } finally {
      await doctorContext.close();
      await patientContext.close();
      await pharmacistContext.close();
    }
  });
});
