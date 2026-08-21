import os
import sys
import django
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'assentag.settings')
django.setup()

def test_browser():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.set_capability("goog:loggingPrefs", {"performance": "ALL", "browser": "ALL"})
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # 1. Login
        print("Navigating to login...")
        driver.get("http://127.0.0.1:8000/login/login/")
        
        driver.find_element(By.NAME, "name").send_keys("adarsh")
        driver.find_element(By.NAME, "password").send_keys("adarsh")
        driver.find_element(By.TAG_NAME, "form").submit()
        
        print("Waiting for dashboard...")
        time.sleep(3)
        
        # 2. Extract logs
        browser_logs = driver.get_log('browser')
        print("--- BROWSER CONSOLE LOGS ---")
        for log in browser_logs:
            print(log)
            
        print("--- IMAGE ELEMENTS ---")
        images = driver.find_elements(By.TAG_NAME, 'img')
        for img in images:
            src = img.get_attribute('src')
            if 'dynamic/feed' in str(src):
                complete = driver.execute_script("return arguments[0].complete;", img)
                width = driver.execute_script("return arguments[0].naturalWidth;", img)
                print(f"Feed Image Src: {src}")
                print(f"Complete: {complete}, Natural Width: {width}")
                if width == 0:
                    print("BROKEN IMAGE DETECTED!")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    test_browser()
