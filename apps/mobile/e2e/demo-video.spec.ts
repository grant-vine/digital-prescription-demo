import { test, expect } from '@playwright/test';

/**
 * Generate separate demo videos for each role
 * Videos saved to: test-results/videos/{role}/
 */

const VIDEO_SIZE = { width: 1280, height: 720 };
const DEMO_TIMEOUT = 800;

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
      
      // Step 2: Click Healthcare Provider role card (use text fallback)
      const doctorCard = page.locator('text=Healthcare Provider').first();
      if (await doctorCard.isVisible({ timeout: 5000 }).catch(() => false)) {
        await doctorCard.click();
        await wait(DEMO_TIMEOUT);
      }
      
      // Step 3: Use demo login (use text fallback)
      const demoButton = page.locator('text=Use Demo Doctor').first();
      if (await demoButton.isVisible({ timeout: 5000 }).catch(() => false)) {
        await demoButton.click();
        await page.waitForLoadState('networkidle');
        await wait(DEMO_TIMEOUT * 2);
      }
      
      // Step 4: Wait for dashboard to load
      await page.waitForTimeout(2000);
      
      // Step 5: Try to click New Prescription
      const newPrescriptionBtn = page.locator('text=New Prescription').first();
      if (await newPrescriptionBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
        await newPrescriptionBtn.click();
        await page.waitForLoadState('networkidle');
        await wait(DEMO_TIMEOUT);
        
        // Step 6: Try to select patient
        const patientItem = page.locator('text=John Smith').first();
        if (await patientItem.isVisible({ timeout: 3000 }).catch(() => false)) {
          await patientItem.click();
          await wait(DEMO_TIMEOUT);
        }
      }
      
      // Final showcase pause
      await wait(3000);
      
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
      const patientCard = page.locator('text=Patient').first();
      if (await patientCard.isVisible({ timeout: 5000 }).catch(() => false)) {
        await patientCard.click();
        await wait(DEMO_TIMEOUT);
      }
      
      // Step 3: Use demo login
      const demoButton = page.locator('text=Use Demo Patient').first();
      if (await demoButton.isVisible({ timeout: 5000 }).catch(() => false)) {
        await demoButton.click();
        await page.waitForLoadState('networkidle');
        await wait(DEMO_TIMEOUT * 2);
      }
      
      // Step 4: Wait for wallet to load
      await page.waitForTimeout(2000);
      
      // Step 5: Try to click Scan QR
      const scanBtn = page.locator('text=Scan').first();
      if (await scanBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
        await scanBtn.click();
        await wait(DEMO_TIMEOUT * 2);
      }
      
      // Final showcase pause
      await wait(3000);
      
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
      const pharmacistCard = page.locator('text=Pharmacist').first();
      if (await pharmacistCard.isVisible({ timeout: 5000 }).catch(() => false)) {
        await pharmacistCard.click();
        await wait(DEMO_TIMEOUT);
      }
      
      // Step 3: Use demo login
      const demoButton = page.locator('text=Use Demo Pharmacist').first();
      if (await demoButton.isVisible({ timeout: 5000 }).catch(() => false)) {
        await demoButton.click();
        await page.waitForLoadState('networkidle');
        await wait(DEMO_TIMEOUT * 2);
      }
      
      // Step 4: Wait for verify screen to load
      await page.waitForTimeout(2000);
      
      // Step 5: Try to click Start Scan
      const scanBtn = page.locator('text=Start Scanning').first();
      if (await scanBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
        await scanBtn.click();
        await wait(DEMO_TIMEOUT * 2);
      }
      
      // Final showcase pause
      await wait(3000);
      
    } finally {
      await context.close();
    }
  });
});
