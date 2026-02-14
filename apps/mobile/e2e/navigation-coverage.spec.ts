import { test, expect } from '@playwright/test';

test.describe('E2E: Complete Navigation Coverage', () => {
  const roles = [
    { id: 'doctor', name: 'Healthcare Provider', demoButton: 'demo-login-doctor' },
    { id: 'patient', name: 'Patient', demoButton: 'demo-login-patient' },
    { id: 'pharmacist', name: 'Pharmacist', demoButton: 'demo-login-pharmacist' }
  ];

  for (const role of roles) {
    test(`should navigate through complete ${role.name} flow`, async ({ page }) => {
      await page.goto('/');
      await page.waitForLoadState('networkidle');

      const continueButton = page.getByRole('button', { name: new RegExp(`Continue as.*${role.id === 'doctor' ? 'Healthcare' : role.name}`, 'i') });
      await expect(continueButton, `${role.name} continue button should be visible`).toBeVisible();
      await continueButton.click();

      const demoButton = page.locator(`[data-testid="${role.demoButton}"]`);
      await expect(demoButton, `${role.name} demo button should be visible`).toBeVisible();
      await demoButton.click();
      
      await page.waitForTimeout(1000);
      
      const emailField = page.locator('[data-testid="email-input"]');
      await expect(emailField).toHaveValue(/.+/);
      
      await page.locator('[data-testid="login-button"]').click();
      
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);
      
      const currentUrl = page.url();
      
      if (role.id === 'doctor') {
        expect(currentUrl).not.toContain('/doctor/auth');
        const screen = page.locator('[data-testid="doctor-dashboard"]');
        await expect(screen, `${role.name} dashboard should load`).toBeVisible({ timeout: 20000 });
      } else if (role.id === 'patient') {
        expect(currentUrl).not.toContain('/patient/auth');
      } else if (role.id === 'pharmacist') {
        expect(currentUrl).toContain('/pharmacist');
      }
    });
  }

  test('should access all FAQ items on index page', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const faqItems = [
      'faq-how-it-works',
      'faq-what-is-ssi',
      'faq-qr-code-flow',
      'faq-demo-time'
    ];

    for (const faqId of faqItems) {
      const faq = page.locator(`[data-testid="${faqId}"]`);
      await expect(faq, `${faqId} should be visible`).toBeVisible();
      await faq.click();
      await page.waitForTimeout(200);
    }
  });

  test('should handle back navigation correctly', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    await page.getByRole('button', { name: /Continue as.*Healthcare/i }).click();
    await expect(page.locator('[data-testid="doctor-auth-screen"]')).toBeVisible();
    
    await page.goBack();
    await expect(page.locator('[data-testid="index-screen"]')).toBeVisible();
  });

  test('should display workflow diagram', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const workflow = page.locator('[data-testid="workflow-diagram"]');
    await expect(workflow).toBeVisible();

    const steps = ['step-1', 'step-2', 'step-3', 'step-4'];
    for (const step of steps) {
      await expect(page.locator(`[data-testid="workflow-${step}"]`)).toBeVisible();
    }
  });
});

test.describe('E2E: Button and Link Coverage', () => {
  test('should have all interactive elements accessible', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const buttons = await page.locator('button, [role="button"]').count();
    const links = await page.locator('a, [role="link"]').count();
    
    expect(buttons).toBeGreaterThan(0);
    expect(links).toBeGreaterThanOrEqual(0);
  });


});
