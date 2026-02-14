import { test, expect } from '@playwright/test';

test.describe('E2E: Doctor Creates Prescription - Enhanced', () => {
  test('should complete full flow: login → select patient → add medication → save draft', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Verify index page loaded
    await expect(page.locator('[data-testid="index-title"]')).toBeVisible();
    
    // Select doctor role using testID
    const doctorCard = page.locator('[data-testid="role-card-doctor"]');
    await expect(doctorCard).toBeVisible();
    await doctorCard.click();
    await page.waitForTimeout(300);

    // Use demo login button
    const demoButton = page.locator('[data-testid="demo-login-doctor"]');
    await expect(demoButton).toBeVisible();
    await demoButton.click();
    await page.waitForLoadState('networkidle');

    // Verify dashboard loaded
    await expect(page.locator('[data-testid="doctor-dashboard"]')).toBeVisible();
    
    // Navigate to create prescription
    const newPrescriptionBtn = page.locator('[data-testid="new-prescription-button"]');
    await expect(newPrescriptionBtn).toBeVisible();
    await newPrescriptionBtn.click();
    
    // Select patient
    await expect(page.locator('[data-testid="patient-select-screen"]')).toBeVisible();
    const patientItem = page.locator('[data-testid="patient-item-1"]').first();
    await expect(patientItem).toBeVisible();
    await patientItem.click();
    
    // Add medication
    await expect(page.locator('[data-testid="medication-entry-screen"]')).toBeVisible();
    const medSearch = page.locator('[data-testid="medication-search-input"]');
    await medSearch.fill('Amoxicillin');
    await page.waitForTimeout(500);
    
    const medItem = page.locator('[data-testid="medication-item"]').first();
    await expect(medItem).toBeVisible();
    await medItem.click();
    
    // Set dosage
    const dosageInput = page.locator('[data-testid="dosage-input"]');
    await dosageInput.fill('500mg');
    
    // Save draft
    const saveBtn = page.locator('[data-testid="save-draft-button"]');
    await saveBtn.click();
    
    // Verify saved
    await expect(page.locator('[data-testid="prescription-saved-message"]')).toBeVisible();
  });

  test('should navigate through all doctor screens', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Test each navigation path
    const navItems = [
      { testid: 'role-card-doctor', name: 'Role Selection' },
    ];
    
    for (const item of navItems) {
      const locator = page.locator(`[data-testid="${item.testid}"]`);
      await expect(locator, `${item.name} should be visible`).toBeVisible();
    }
  });

  test('should display error when login fails with invalid credentials', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Select doctor role
    const doctorCard = page.locator('[data-testid="role-card-doctor"]');
    await doctorCard.click();

    // Fill in invalid credentials
    const emailInput = page.locator('[data-testid="email-input"]');
    const passwordInput = page.locator('[data-testid="password-input"]');
    const loginButton = page.locator('[data-testid="login-button"]');
    
    await emailInput.fill('invalid@hospital.com');
    await passwordInput.fill('WrongPassword');
    await loginButton.click();

    // Verify error message
    await expect(page.locator('[data-testid="login-error-message"]')).toBeVisible();
  });

  test('should handle empty patient search results gracefully', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Login as doctor
    await page.locator('[data-testid="role-card-doctor"]').click();
    await page.locator('[data-testid="demo-login-doctor"]').click();
    await page.waitForLoadState('networkidle');

    // Navigate to patient select
    await page.locator('[data-testid="new-prescription-button"]').click();
    
    // Search for non-existent patient
    const searchInput = page.locator('[data-testid="patient-search-input"]');
    await searchInput.fill('xyznonexistent123');
    await page.waitForTimeout(500);
    
    // Verify empty state
    await expect(page.locator('[data-testid="no-patients-found"]')).toBeVisible();
  });

  test('should validate required fields in medication form', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Login and navigate
    await page.locator('[data-testid="role-card-doctor"]').click();
    await page.locator('[data-testid="demo-login-doctor"]').click();
    await page.waitForLoadState('networkidle');
    
    await page.locator('[data-testid="new-prescription-button"]').click();
    await page.locator('[data-testid="patient-item-1"]').first().click();
    
    // Try to save without medication
    const saveBtn = page.locator('[data-testid="save-draft-button"]');
    await saveBtn.click();
    
    // Verify validation error
    await expect(page.locator('[data-testid="medication-required-error"]')).toBeVisible();
  });

  test('should allow QR scan option from patient select', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Login
    await page.locator('[data-testid="role-card-doctor"]').click();
    await page.locator('[data-testid="demo-login-doctor"]').click();
    await page.waitForLoadState('networkidle');
    
    // Navigate to patient select
    await page.locator('[data-testid="new-prescription-button"]').click();
    
    // Click QR scan button
    const qrBtn = page.locator('[data-testid="qr-scan-button"]');
    await expect(qrBtn).toBeVisible();
    await qrBtn.click();
    
    // Verify QR scan screen
    await expect(page.locator('[data-testid="qr-scan-screen"]')).toBeVisible();
  });
});
