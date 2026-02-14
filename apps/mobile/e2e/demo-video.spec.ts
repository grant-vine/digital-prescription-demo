import { test, expect } from '@playwright/test';

/**
 * Generate separate demo videos for each role
 * Videos saved to: test-results/videos/{role}/
 */

const VIDEO_SIZE = { width: 1280, height: 720 };
const DEMO_TIMEOUT = 500;

async function wait(ms: number) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

test.describe('Demo Videos - Individual Role Flows', () => {
  
  test('Doctor: Complete workflow video', async ({ browser }) => {
    const context = await browser.newContext({
      recordVideo: { 
        dir: 'test-results/videos/doctor',
        size: VIDEO_SIZE 
      },
    });
    
    const page = await context.newPage();
    
    try {
      // Step 1: Load index page
      await page.goto('/');
      await page.waitForLoadState('networkidle');
      await wait(DEMO_TIMEOUT);
      
      // Step 2: Click Healthcare Provider role card
      const doctorCard = page.locator('[data-testid="role-card-doctor"]');
      await expect(doctorCard).toBeVisible();
      await doctorCard.click();
      await wait(DEMO_TIMEOUT);
      
      // Step 3: Use demo login
      const demoButton = page.locator('[data-testid="demo-login-doctor"]');
      await expect(demoButton).toBeVisible();
      await demoButton.click();
      await page.waitForLoadState('networkidle');
      await wait(DEMO_TIMEOUT * 2);
      
      // Step 4: Verify dashboard loaded
      const dashboard = page.locator('[data-testid="doctor-dashboard"]');
      await expect(dashboard).toBeVisible();
      await wait(DEMO_TIMEOUT);
      
      // Step 5: Click New Prescription
      const newPrescriptionBtn = page.locator('[data-testid="new-prescription-button"]');
      if (await newPrescriptionBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
        await newPrescriptionBtn.click();
        await page.waitForLoadState('networkidle');
        await wait(DEMO_TIMEOUT);
        
        // Step 6: Select patient
        const patientItem = page.locator('[data-testid="patient-item"]').first();
        if (await patientItem.isVisible({ timeout: 3000 }).catch(() => false)) {
          await patientItem.click();
          await wait(DEMO_TIMEOUT);
          
          // Step 7: Add medication
          const medSearch = page.locator('[data-testid="medication-search-input"]');
          if (await medSearch.isVisible({ timeout: 3000 }).catch(() => false)) {
            await medSearch.fill('Amoxicillin');
            await wait(DEMO_TIMEOUT);
          }
        }
      }
      
      // Final showcase pause
      await wait(2000);
      
    } finally {
      await context.close();
    }
  });
  
  test('Patient: Complete workflow video', async ({ browser }) => {
    const context = await browser.newContext({
      recordVideo: { 
        dir: 'test-results/videos/patient',
        size: VIDEO_SIZE 
      },
    });
    
    const page = await context.newPage();
    
    try {
      // Step 1: Load index page
      await page.goto('/');
      await page.waitForLoadState('networkidle');
      await wait(DEMO_TIMEOUT);
      
      // Step 2: Click Patient role card
      const patientCard = page.locator('[data-testid="role-card-patient"]');
      await expect(patientCard).toBeVisible();
      await patientCard.click();
      await wait(DEMO_TIMEOUT);
      
      // Step 3: Use demo login
      const demoButton = page.locator('[data-testid="demo-login-patient"]');
      await expect(demoButton).toBeVisible();
      await demoButton.click();
      await page.waitForLoadState('networkidle');
      await wait(DEMO_TIMEOUT * 2);
      
      // Step 4: Verify wallet loaded
      const wallet = page.locator('[data-testid="patient-wallet"]');
      await expect(wallet).toBeVisible();
      await wait(DEMO_TIMEOUT);
      
      // Step 5: Click Scan QR
      const scanBtn = page.locator('[data-testid="scan-qr-button"]');
      if (await scanBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
        await scanBtn.click();
        await page.waitForLoadState('networkidle');
        await wait(DEMO_TIMEOUT * 2);
        await wait(2000);
      }
      
      // Final showcase pause
      await wait(2000);
      
    } finally {
      await context.close();
    }
  });
  
  test('Pharmacist: Complete workflow video', async ({ browser }) => {
    const context = await browser.newContext({
      recordVideo: { 
        dir: 'test-results/videos/pharmacist',
        size: VIDEO_SIZE 
      },
    });
    
    const page = await context.newPage();
    
    try {
      // Step 1: Load index page
      await page.goto('/');
      await page.waitForLoadState('networkidle');
      await wait(DEMO_TIMEOUT);
      
      // Step 2: Click Pharmacist role card
      const pharmacistCard = page.locator('[data-testid="role-card-pharmacist"]');
      await expect(pharmacistCard).toBeVisible();
      await pharmacistCard.click();
      await wait(DEMO_TIMEOUT);
      
      // Step 3: Use demo login
      const demoButton = page.locator('[data-testid="demo-login-pharmacist"]');
      await expect(demoButton).toBeVisible();
      await demoButton.click();
      await page.waitForLoadState('networkidle');
      await wait(DEMO_TIMEOUT * 2);
      
      // Step 4: Verify verify screen loaded
      const verifyScreen = page.locator('[data-testid="pharmacist-verify"]');
      await expect(verifyScreen).toBeVisible();
      await wait(DEMO_TIMEOUT);
      
      // Step 5: Click Start Scan
      const scanBtn = page.locator('[data-testid="start-scan-button"]');
      if (await scanBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
        await scanBtn.click();
        await wait(DEMO_TIMEOUT * 2);
        await wait(2000);
      }
      
      // Final showcase pause
      await wait(2000);
      
    } finally {
      await context.close();
    }
  });
});
