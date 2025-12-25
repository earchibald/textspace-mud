#!/usr/bin/env python3
"""
Playwright test for issue #13: Help command should not overwrite room info display
"""
import asyncio
from playwright.async_api import async_playwright, expect

async def test_help_command_display():
    """Test that help command displays correctly without overwriting room info"""
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Navigate to dev server
        url = "https://textspace-mud-dev-development.up.railway.app"
        print(f"Navigating to {url}")
        await page.goto(url)
        
        # Wait for page to load
        await page.wait_for_selector('#input')
        
        # Login as admin
        print("Logging in as admin...")
        await page.fill('#input', 'admin')
        await page.click('button:has-text("Send")')
        
        # Wait for login to complete and room info to be displayed
        await page.wait_for_timeout(2000)
        
        # Capture initial room info
        room_name_before = await page.text_content('#room-name')
        room_desc_before = await page.text_content('#room-desc')
        print(f"Initial room: {room_name_before}")
        print(f"Initial description: {room_desc_before}")
        
        # Send help command
        print("\nSending help command...")
        await page.fill('#input', 'help')
        await page.click('button:has-text("Send")')
        
        # Wait for help response
        await page.wait_for_timeout(1000)
        
        # Check that help text appears in main output
        output_text = await page.text_content('#output')
        assert 'Available Commands:' in output_text, "Help text should appear in main output"
        print("✓ Help text appears in main output")
        
        # Check that room info is NOT overwritten with help text
        room_name_after = await page.text_content('#room-name')
        room_desc_after = await page.text_content('#room-desc')
        room_info_text = await page.text_content('#room-info')
        
        print(f"\nRoom after help: {room_name_after}")
        print(f"Description after help: {room_desc_after}")
        
        # Verify room info hasn't been overwritten with help text
        assert 'Available Commands:' not in room_info_text, "Help text should NOT appear in room info box"
        assert room_name_after == room_name_before, "Room name should remain unchanged"
        assert room_desc_after == room_desc_before, "Room description should remain unchanged"
        
        print("✓ Room info box was NOT overwritten by help text")
        
        # Test that look command still updates room info correctly
        print("\nTesting that look command still updates room info...")
        await page.fill('#input', 'look')
        await page.click('button:has-text("Send")')
        await page.wait_for_timeout(1000)
        
        room_name_after_look = await page.text_content('#room-name')
        assert room_name_after_look == room_name_before, "Look command should maintain room info"
        print("✓ Look command still works correctly")
        
        await browser.close()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED - Issue #13 is fixed!")
        print("="*60)

if __name__ == "__main__":
    asyncio.run(test_help_command_display())
