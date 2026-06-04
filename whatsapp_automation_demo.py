"""
N-Assist: Standalone WhatsApp Web Automation Demo Script

This script demonstrates two popular ways to automate sending WhatsApp messages 
without relying on the official Meta WhatsApp Cloud API:
1. Selenium Web Driver (Recommended for background/session-persisted automation)
2. PyWhatKit (Easiest to write, simulates keyboard/mouse input)

To run this script:
1. Install dependencies:
   pip install selenium pywhatkit webdriver-manager

2. Run the script:
   python whatsapp_automation_demo.py
"""

import os
import sys
import time
import urllib.parse

def send_via_selenium(phone_number, message, profile_dir="whatsapp_chrome_session"):
    """
    Automates WhatsApp Web using Selenium.
    It saves your WhatsApp Web session in a local folder so you only need to 
    scan the QR code ONCE. Subsequent runs will use the saved session.
    
    Requirements:
    - Google Chrome installed.
    - pip install selenium webdriver-manager
    """
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.common.keys import Keys
        from webdriver_manager.chrome import ChromeDriverManager
    except ImportError:
        print("[Error] Selenium or webdriver-manager is not installed.")
        print("Please run: pip install selenium webdriver-manager")
        return False

    print("\n--- Starting Selenium WhatsApp Web Automation ---")
    print(f"Recipient: {phone_number}")
    print(f"Message: {message}")
    print(f"Session data will be stored in: {os.path.abspath(profile_dir)}")

    # Clean the phone number (must include country code, e.g., +919876543210 -> 919876543210)
    clean_phone = "".join(filter(str.isdigit, phone_number))
    
    # URL encode the message
    encoded_message = urllib.parse.quote(message)
    whatsapp_url = f"https://web.whatsapp.com/send?phone={clean_phone}&text={encoded_message}"

    # Configure Chrome options
    options = Options()
    # Path to store session data (cookies, local storage)
    options.add_argument(f"--user-data-dir={os.path.abspath(profile_dir)}")
    options.add_argument("--profile-directory=Default")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--start-maximized")

    # Start Chrome
    print("Launching Chrome... (If a QR code appears, please scan it to link your device)")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(whatsapp_url)
        
        # Wait for the chat to load.
        # We wait for the send button icon (span[data-icon='send']) or the text input field to appear.
        print("Waiting for page to load (this may take longer if scanning QR code for the first time)...")
        
        # Wait up to 60 seconds (useful for the first login scan)
        wait = WebDriverWait(driver, 60)
        
        # Wait for the send button to be clickable
        send_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//span[@data-icon='send']/.."))
        )
        
        # Click the send button
        send_button.click()
        print("Send button clicked!")
        
        # Wait a few seconds for the message to dispatch before closing
        time.sleep(3)
        print("Message sent successfully via Selenium!")
        return True

    except Exception as e:
        print(f"An error occurred during Selenium automation: {e}")
        print("Tip: Make sure you scanned the QR code and that Chrome is not already running with the same profile.")
        return False
    finally:
        driver.quit()


def send_via_pywhatkit(phone_number, message):
    """
    Automates WhatsApp Web using PyWhatKit.
    It opens your default browser, waits for a few seconds, and simulates typing/sending.
    
    Pros: Very simple, no driver setup needed.
    Cons: Requires active GUI (cannot run headless), opens default browser tabs continuously.
    
    Requirements:
    - You must be logged into WhatsApp Web in your default browser.
    - pip install pywhatkit
    """
    try:
        import pywhatkit
    except ImportError:
        print("[Error] PyWhatKit is not installed.")
        print("Please run: pip install pywhatkit")
        return False

    print("\n--- Starting PyWhatKit WhatsApp Web Automation ---")
    print("Note: This will open your default browser tab. Make sure WhatsApp Web is logged in.")
    
    try:
        # sendwhatmsg_instantly opens the browser tab, waits `wait_time` seconds, and sends
        # tab_close=True will attempt to close the tab after sending
        pywhatkit.sendwhatmsg_instantly(
            phone_no=phone_number,
            message=message,
            wait_time=15,       # Seconds to wait for WhatsApp Web to load
            tab_close=True,     # Close the tab after sending
            close_time=4        # Seconds to wait before closing the tab
        )
        print("Message sent successfully via PyWhatKit!")
        return True
    except Exception as e:
        print(f"An error occurred during PyWhatKit automation: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("          N-ASSIST WHATSAPP WEB AUTOMATION DEMO")
    print("=" * 60)
    
    # Prompt user for details
    phone = input("Enter recipient phone number (with country code, e.g., +1234567890): ").strip()
    msg = input("Enter message to send: ").strip()
    
    print("\nChoose automation method:")
    print("1. Selenium Web Driver (Recommended - Session Persisted)")
    print("2. PyWhatKit (Easiest - Simulates Keyboard/Mouse)")
    choice = input("Enter choice (1 or 2): ").strip()
    
    if not phone or not msg:
        print("Phone and message cannot be empty. Exiting.")
        sys.exit(1)
        
    if choice == "1":
        send_via_selenium(phone, msg)
    elif choice == "2":
        send_via_pywhatkit(phone, msg)
    else:
        print("Invalid choice. Exiting.")
