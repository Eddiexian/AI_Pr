import { test, expect } from '@playwright/test';

test.describe('Functional Flows', () => {
    test.beforeEach(async ({ page }) => {
        // Shared login for all functional tests
        await page.goto('/');
        await page.fill('input[placeholder*="Username" i]', 'admin');
        await page.fill('input[placeholder*="Password" i]', 'admin');
        await page.click('button:has-text("登入系統")');
        await expect(page).toHaveURL(/\/$/);
    });

    test('should create a new layout', async ({ page }) => {
        const layoutName = `Test Layout ${Date.now()}`;

        // Fill layout name
        await page.fill('input[placeholder*="佈局名稱" i]', layoutName);

        // Click create button
        await page.click('button:has-text("建立佈局")');

        // Verify redirection to editor
        await page.waitForURL(/.*editor.*/);
        await expect(page.locator('h2:has-text("編輯器工具箱")')).toBeVisible();

        // Go back to dashboard to verify it exists in the list
        await page.click('text=返回儀表板');
        await page.waitForURL(/\/$/);
        await expect(page.locator(`.layout-card h3:has-text("${layoutName}")`)).toBeVisible();
    });

    test('should add and delete a component in the editor', async ({ page }) => {
        // Use an existing layout if possible, or create one
        await page.fill('input[placeholder*="佈局名稱" i]', 'Editor Test Layout');
        await page.click('button:has-text("建立佈局")');

        // Wait for redirect
        await page.waitForURL(/.*editor.*/);
        await expect(page.locator('h2:has-text("編輯器工具箱")')).toBeVisible();

        // Add a new component
        await page.click('button:has-text("新增儲位")');

        // Verify component appeared in SVG (looking for the default code 'B-NEW')
        const comp = page.locator('text=B-NEW').first();
        await expect(comp).toBeVisible();

        // Select it (click on it)
        await comp.click({ force: true });

        // Delete it
        await page.click('button:has-text("刪除元件")');

        // Verify it disappeared
        await expect(comp).not.toBeVisible();
    });

    test('should view WIP data in operation mode', async ({ page }) => {
        // Navigate to the specific layout's operation mode from seed
        // Clicking the "作業模式" button of the layout card with '大R區'
        const layoutCard = page.locator('.layout-card', { hasText: '大R區' });
        await expect(layoutCard).toBeVisible();
        await layoutCard.locator('.btn-accent').click();

        // Wait for redirect
        await page.waitForURL(/.*operation.*/);
        await expect(page.locator('text=作業模式')).toBeVisible();

        // Click on a component (from seed data)
        const binA01 = page.locator('text=A-01').first();
        await expect(binA01).toBeVisible();

        // Force click because SVG text might have pointer-events: none
        await binA01.click({ force: true });

        // Verify detail overlay appears
        await expect(page.locator('.detail-card')).toBeVisible();
        await expect(page.locator('text=儲位: A-01')).toBeVisible();
        await expect(page.locator('text=WIP 資訊')).toBeVisible();
    });
});
