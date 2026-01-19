import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
    test('should login successfully with valid credentials', async ({ page }) => {
        // Navigate to login page (assuming root or /login)
        await page.goto('/');

        // Fill in the login form (using placeholders or labels based on UI exploration)
        // Looking at src/views/LoginView.vue (based on metadata)
        await page.fill('input[placeholder*="Username" i]', 'admin');
        await page.fill('input[placeholder*="Password" i]', 'admin');

        // Click login button
        await page.click('button:has-text("登入系統")');

        // Check if redirected to dashboard or showing welcome message
        // On success, it redirects to '/' which should show Dashboard components
        await expect(page).toHaveURL(/\/$/);
        await expect(page.locator('text=Dashboard')).toBeVisible();
    });

    test('should show error with invalid credentials', async ({ page }) => {
        await page.goto('/');
        await page.fill('input[placeholder*="Username" i]', 'wronguser');
        await page.fill('input[placeholder*="Password" i]', 'wrongpass');
        await page.click('button:has-text("登入系統")');

        // Expect error message in Chinese
        await expect(page.locator('text=帳號或密碼錯誤')).toBeVisible();
    });
});
