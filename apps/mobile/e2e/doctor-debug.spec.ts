import { test, expect } from '@playwright/test';

test.describe('DEBUG: Doctor Flow with Logging', () => {
  test('Doctor complete flow - with debug logging', async ({ browser }) => {
    const context = await browser.newContext({
      recordVideo: { 
        dir: 'test-results/videos/debug',
        size: { width: 1280, height: 720 }
      },
    });
    
    const page = await context.newPage();
    
    // Enable console logging
    page.on('console', msg => {
      console.log(`[PAGE CONSOLE] ${msg.type()}: ${msg.text()}`);
    });
    
    page.on('pageerror', error => {
      console.log(`[PAGE ERROR] ${error.message}`);
    });
    
    page.on('response', response => {
      if (response.url().includes('localhost:8000')) {
        console.log(`[API RESPONSE] ${response.status()} ${response.url()}`);
      }
    });
    
    try {
      console.log('=== STEP 1: Navigate to index ===');
      await page.goto('http://localhost:8081/');
      console.log('Page loaded, waiting for networkidle...');
      await page.waitForLoadState('networkidle');
      console.log('Network idle reached');
      
      // Take screenshot of initial state
      await page.screenshot({ path: 'test-results/debug-01-index.png' });
      console.log('Screenshot saved: debug-01-index.png');
      
      // Log current URL and title
      console.log(`Current URL: ${page.url()}`);
      console.log(`Page title: ${await page.title()}`);
      
      // Log all visible text on the page
      const bodyText = await page.textContent('body');
      console.log('Page body text preview:', bodyText?.substring(0, 500));
      
      console.log('=== STEP 2: Find and click Continue as Healthcare button ===');
      
      // The navigation button is "Continue as Healthcare" at the bottom of the card
      const selectors = [
        'text=Continue as Healthcare',
        'button:has-text("Continue as")',
        '[data-testid="role-card-doctor"]',
        'text=Healthcare Provider'
      ];
      
      let foundElement: any = null;
      for (const selector of selectors) {
        console.log(`Trying selector: ${selector}`);
        const element = page.locator(selector).first();
        const count = await element.count();
        console.log(`  Found ${count} elements`);
        
        if (count > 0) {
          const isVisible = await element.isVisible().catch(() => false);
          console.log(`  Is visible: ${isVisible}`);
          
          if (isVisible) {
            foundElement = element;
            console.log(`  ✓ Using selector: ${selector}`);
            break;
          }
        }
      }
      
      if (!foundElement) {
        console.log('ERROR: Could not find Healthcare Provider card!');
        await page.screenshot({ path: 'test-results/debug-02-error.png' });
        throw new Error('Healthcare Provider card not found');
      }
      
      await foundElement.click();
      console.log('Clicked on role card');
      await page.waitForTimeout(1000);
      
      await page.screenshot({ path: 'test-results/debug-03-after-click.png' });
      console.log('Screenshot saved: debug-03-after-click.png');
      
      console.log(`Current URL after click: ${page.url()}`);
      
      console.log('=== STEP 2b: Wait for page hydration and reload if needed ===');
      await page.waitForTimeout(2000);
      
      const hasForm = await page.locator('input').count() > 0;
      if (!hasForm) {
        console.log('Page not hydrated, reloading...');
        await page.reload();
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(2000);
      }
      
      console.log('=== STEP 3: Find and click demo login button ===');
      
      const loginSelectors = [
        'text=Use Demo Doctor',
        '[data-testid="demo-login-doctor"]',
        'button:has-text("Demo")',
        'text=Demo'
      ];
      
      let loginButton: any = null;
      for (const selector of loginSelectors) {
        console.log(`Trying login selector: ${selector}`);
        const element = page.locator(selector).first();
        const count = await element.count();
        console.log(`  Found ${count} elements`);
        
        if (count > 0) {
          const isVisible = await element.isVisible().catch(() => false);
          console.log(`  Is visible: ${isVisible}`);
          
          if (isVisible) {
            loginButton = element;
            console.log(`  ✓ Using login selector: ${selector}`);
            break;
          }
        }
      }
      
      if (!loginButton) {
        console.log('ERROR: Could not find demo login button!');
        await page.screenshot({ path: 'test-results/debug-04-login-error.png' });
        
        // Try to find any buttons on the page
        const allButtons = await page.locator('button').all();
        console.log(`Found ${allButtons.length} buttons on page:`);
        for (let i = 0; i < Math.min(allButtons.length, 5); i++) {
          const text = await allButtons[i].textContent();
          console.log(`  Button ${i}: ${text}`);
        }
        
        throw new Error('Demo login button not found');
      }
      
      await loginButton.click();
      console.log('Clicked demo login button (filled credentials)');
      
      console.log('=== STEP 3b: Click actual Login button ===');
      await page.waitForTimeout(1000);
      
      const actualLoginSelectors = [
        'button:has-text("Login")',
        'text=Login',
        '[data-testid="login-button"]',
        'button:has-text("Sign")'
      ];
      
      let actualLoginBtn: any = null;
      for (const selector of actualLoginSelectors) {
        console.log(`  Trying login button selector: ${selector}`);
        const btn = page.locator(selector).first();
        const count = await btn.count();
        console.log(`    Found ${count} elements`);
        
        if (count > 0) {
          const isVisible = await btn.isVisible().catch(() => false);
          console.log(`    Is visible: ${isVisible}`);
          if (isVisible) {
            actualLoginBtn = btn;
            console.log(`    ✓ Using: ${selector}`);
            break;
          }
        }
      }
      
      if (actualLoginBtn) {
        await actualLoginBtn.click();
        console.log('Clicked actual Login button');
      } else {
        console.log('ERROR: Could not find Login button');
        const allButtons = await page.locator('button').all();
        console.log(`Found ${allButtons.length} buttons:`);
        for (let i = 0; i < Math.min(allButtons.length, 10); i++) {
          const text = await allButtons[i].textContent();
          console.log(`  ${i}: "${text}"`);
        }
      }
      
      console.log('=== STEP 4: Wait for dashboard to load ===');
      console.log('Waiting for navigation to dashboard...');
      
      try {
        await page.waitForURL('**/doctor/dashboard', { timeout: 10000 });
        console.log('✓ Navigated to dashboard');
      } catch (e) {
        console.log('Navigation timeout, current URL:', page.url());
      }
      
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);
      
      await page.screenshot({ path: 'test-results/debug-05-dashboard.png' });
      console.log('Screenshot saved: debug-05-dashboard.png');
      
      console.log(`Current URL after login: ${page.url()}`);
      
      // Check if we're on dashboard
      const url = page.url();
      if (url.includes('dashboard') || url.includes('doctor')) {
        console.log('✓ Successfully logged in and on doctor page');
      } else {
        console.log('WARNING: URL does not contain dashboard or doctor:', url);
      }
      
      console.log('=== STEP 5: Try to click New Prescription ===');
      
      const prescriptionSelectors = [
        'text=New Prescription',
        'button:has-text("New")',
        '[data-testid="new-prescription-button"]'
      ];
      
      let newPrescriptionBtn: any = null;
      for (const selector of prescriptionSelectors) {
        console.log(`Trying selector: ${selector}`);
        const element = page.locator(selector).first();
        const count = await element.count();
        
        if (count > 0 && await element.isVisible().catch(() => false)) {
          newPrescriptionBtn = element;
          console.log(`  ✓ Found: ${selector}`);
          break;
        }
      }
      
      if (newPrescriptionBtn) {
        await newPrescriptionBtn.click();
        console.log('Clicked New Prescription');
        await page.waitForTimeout(1000);
        
        await page.screenshot({ path: 'test-results/debug-06-prescription.png' });
        console.log('Screenshot saved: debug-06-prescription.png');
        console.log(`URL after clicking New Prescription: ${page.url()}`);
      } else {
        console.log('Could not find New Prescription button - will wait on dashboard');
      }
      
      // Final wait for video
      await page.waitForTimeout(3000);
      console.log('=== TEST COMPLETE ===');
      
    } catch (error) {
      console.error('TEST FAILED:', error);
      await page.screenshot({ path: 'test-results/debug-error-final.png' });
      throw error;
    } finally {
      await context.close();
    }
  });
});
