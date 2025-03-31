import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://example.com")
        
        element = page.locator('//h1')
        text = await element.text_content()
        print(f"텍스트 내용: {text}")
        
        await browser.close()

asyncio.run(run())
