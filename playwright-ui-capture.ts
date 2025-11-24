/**
 * Playwright UI Capture Script
 * Captures screenshots and videos of the UI for analysis
 */

import { chromium } from 'playwright';
import * as fs from 'fs';
import * as path from 'path';

async function captureUI() {
  console.log('Starting UI capture...');

  // Create screenshots directory
  const screenshotsDir = path.join(__dirname, 'ui-screenshots');
  if (!fs.existsSync(screenshotsDir)) {
    fs.mkdirSync(screenshotsDir, { recursive: true });
  }

  // Launch browser
  const browser = await chromium.launch({
    headless: false, // Show browser for debugging
  });

  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
    recordVideo: {
      dir: path.join(__dirname, 'ui-videos'),
      size: { width: 1920, height: 1080 },
    },
  });

  const page = await context.newPage();

  try {
    // Navigate to the app
    console.log('Navigating to http://localhost:5173...');
    await page.goto('http://localhost:5173', { waitUntil: 'networkidle' });

    // Wait for app to be fully loaded
    await page.waitForTimeout(2000);

    // Capture 1: Initial load (light mode)
    console.log('Capturing initial load...');
    await page.screenshot({
      path: path.join(screenshotsDir, '01-initial-load-light.png'),
      fullPage: true,
    });

    // Capture 2: Dark mode toggle
    console.log('Testing dark mode...');
    const themeToggle = page.locator('[aria-label*="dark"], [aria-label*="light"]').first();
    if (await themeToggle.count() > 0) {
      await themeToggle.click();
      await page.waitForTimeout(500);
      await page.screenshot({
        path: path.join(screenshotsDir, '02-dark-mode.png'),
        fullPage: true,
      });
    }

    // Capture 3: Mobile viewport (sidebar collapsed)
    console.log('Testing mobile viewport...');
    await page.setViewportSize({ width: 375, height: 812 }); // iPhone X
    await page.waitForTimeout(500);
    await page.screenshot({
      path: path.join(screenshotsDir, '03-mobile-view.png'),
      fullPage: true,
    });

    // Capture 4: Mobile with sidebar open
    console.log('Testing mobile sidebar...');
    const menuButton = page.locator('[aria-label*="menu"], button:has-text("Menu")').first();
    if (await menuButton.count() > 0) {
      await menuButton.click();
      await page.waitForTimeout(500);
      await page.screenshot({
        path: path.join(screenshotsDir, '04-mobile-sidebar-open.png'),
        fullPage: true,
      });
    }

    // Back to desktop
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.waitForTimeout(500);

    // Capture 5: Hover states on controls
    console.log('Testing hover states...');
    await page.screenshot({
      path: path.join(screenshotsDir, '05-desktop-controls.png'),
      fullPage: true,
    });

    // Capture 6: Focus on record button
    console.log('Testing focus states...');
    const recordButton = page.locator('button').filter({ hasText: /record/i }).or(page.locator('[aria-label*="record"]')).first();
    if (await recordButton.count() > 0) {
      await recordButton.focus();
      await page.waitForTimeout(300);
      await page.screenshot({
        path: path.join(screenshotsDir, '06-record-button-focus.png'),
        fullPage: true,
      });
    }

    // Capture 7: Sidebar controls detail
    console.log('Capturing sidebar details...');
    const sidebar = page.locator('[role="complementary"], aside, nav').first();
    if (await sidebar.count() > 0) {
      await sidebar.screenshot({
        path: path.join(screenshotsDir, '07-sidebar-detail.png'),
      });
    }

    // Capture 8: Main content area
    console.log('Capturing main content...');
    const main = page.locator('main, [role="main"]').first();
    if (await main.count() > 0) {
      await main.screenshot({
        path: path.join(screenshotsDir, '08-main-content.png'),
      });
    }

    // Capture 9: Connection status indicator
    console.log('Capturing connection status...');
    const statusChip = page.locator('[role="status"], .MuiChip-root').first();
    if (await statusChip.count() > 0) {
      await statusChip.screenshot({
        path: path.join(screenshotsDir, '09-connection-status.png'),
      });
    }

    console.log('\n✓ Screenshots captured successfully!');
    console.log(`  Location: ${screenshotsDir}`);

    // Wait a bit more for video to capture
    await page.waitForTimeout(2000);

  } catch (error) {
    console.error('Error capturing UI:', error);
  } finally {
    await context.close();
    await browser.close();
    console.log('✓ Video saved to ui-videos/');
  }
}

// Run the capture
captureUI().catch(console.error);
