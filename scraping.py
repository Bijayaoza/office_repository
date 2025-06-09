import undetected_chromedriver as uc
import time

def search_ct_bidboard(part_number):
    options = uc.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")

    try:
        driver = uc.Chrome(options=options, version_main=137, headless=False, use_subprocess=True)
    except Exception as e:
        print(f"❌ Chrome launch failed: {e}")
        return

    try:
        print("🌐 Opening page...")
        driver.get("https://portal.ct.gov/das/ctsource/bidboard")
        time.sleep(10)  # Let page fully render

        print("⌛ Typing using full focus + JS injection...")
        for _ in range(30):
            js_typing = f"""
                const input = document.querySelector('#search');
                if (input) {{
                    input.focus();
                    input.value = "";
                    input.dispatchEvent(new Event('focus'));
                    input.dispatchEvent(new KeyboardEvent('keydown', {{ key: 'Backspace' }}));
                    input.value = "{part_number}";
                    input.dispatchEvent(new InputEvent('input', {{ bubbles: true }}));
                    input.dispatchEvent(new KeyboardEvent('keydown', {{ key: 'Enter' }}));
                    input.dispatchEvent(new KeyboardEvent('keyup', {{ key: 'Enter' }}));
                    return true;
                }}
                return false;
            """
            success = driver.execute_script(js_typing)
            if success:
                print("✅ Input typed and Enter triggered.")
                break
            time.sleep(1)
        else:
            print("❌ Could not type into the search bar.")
            return

        print("⏳ Waiting for results...")
        time.sleep(8)
        driver.save_screenshot("after_search_fixed.png")
        print("📸 Screenshot saved as after_search_fixed.png")

    except Exception as e:
        print(f"❌ Runtime error: {e}")
    finally:
        driver.quit()
        print("🧹 Browser closed.")

if __name__ == "__main__":
    part_number = input("Enter Part Number: ").strip()
    search_ct_bidboard(part_number)
