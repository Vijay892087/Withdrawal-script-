# auto_withdraw_render_ready.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import schedule, time, requests, logging
from datetime import datetime, timedelta

# --- CONFIG ---
URL = "https://manage.forever699.in"
WITHDRAW_URL = "https://manage.forever699.in/withdraw/"
MOBILE = "8650842502"
PASSWORD = "anur@1234"

# --- Telegram ---
TELEGRAM_TOKEN = "6391372827:AAHY-gfeyHZvtaGKIr4TLyga17lr73lj86o"
CHAT_ID = "969062037"

# --- Accounts ---
ACCOUNTS = [
    {"account_number": "002821717790044", "ifsc_code": "JIOP0000001"},
    {"account_number": "033325229770186", "ifsc_code": "NESF0000096"},
    # Add remaining accounts
]

START_TIME = "09:33:00"
GAP_SECONDS = 35

# --- Logging ---
logging.basicConfig(filename="withdraw_script.log", level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")

def send_telegram(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                      data={"chat_id": CHAT_ID, "text": msg})
        logging.info(f"Telegram sent: {msg}")
    except Exception as e:
        logging.error(f"Telegram send failed: {e}")

def remove_all_popups(driver):
    try:
        for btn in driver.find_elements(By.XPATH, "//button[contains(text(),'Got it') or contains(text(),'Close')]"):
            driver.execute_script("arguments[0].click();", btn)
            logging.info("Popup closed")
            time.sleep(0.2)
    except:
        pass

def click_with_retry(driver, wait):
    for _ in range(10):
        try:
            remove_all_popups(driver)
            btn = wait.until(EC.element_to_be_clickable((By.ID, "submitBtn")))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
            btn.click()
            logging.info("Submit button clicked")
            return True
        except Exception as e:
            logging.warning(f"Click retry error: {e}")
            time.sleep(1)
    return False

def perform_withdraw(driver, wait, acc):
    acc_no = acc["account_number"]
    ifsc = acc["ifsc_code"]
    send_telegram(f"🏦 Withdraw started for {acc_no}")
    logging.info(f"Withdraw started for {acc_no}")

    try:
        driver.get(WITHDRAW_URL)
        time.sleep(1)
        remove_all_popups(driver)

        wait.until(EC.presence_of_element_located((By.ID, "account_number"))).send_keys(acc_no)
        wait.until(EC.presence_of_element_located((By.NAME, "ifsc_code"))).send_keys(ifsc)
        logging.info(f"Account info entered: {acc_no}")

        for i in range(4):
            click_with_retry(driver, wait)
            time.sleep(0.3)
            remove_all_popups(driver)
            if i < 3: time.sleep(6)

        driver.get(WITHDRAW_URL)
        remove_all_popups(driver)
        send_telegram(f"✅ Withdraw completed for {acc_no}")
        logging.info(f"Withdraw completed: {acc_no}")

    except Exception as e:
        send_telegram(f"⚠️ Withdraw failed for {acc_no}: {e}")
        logging.error(f"Withdraw failed {acc_no}: {e}")

def login_once():
    options = Options()
    options.add_argument("--headless=new")  # Render compatible
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,720")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 25)

    driver.get(URL)
    wait.until(EC.presence_of_element_located((By.NAME, "mobile"))).send_keys(MOBILE)
    wait.until(EC.presence_of_element_located((By.NAME, "password"))).send_keys(PASSWORD)
    wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "register-btn"))).click()

    time.sleep(5)
    remove_all_popups(driver)
    logging.info("Logged in successfully")
    send_telegram("🔓 Logged in successfully")
    return driver, wait

def schedule_withdraws():
    driver, wait = login_once()
    send_telegram("🟢 Script Started")
    logging.info("Script started")

    base = datetime.strptime(START_TIME, "%H:%M:%S")
    for i, acc in enumerate(ACCOUNTS):
        t = (base + timedelta(seconds=i * GAP_SECONDS)).strftime("%H:%M:%S")
        schedule.every().day.at(t).do(perform_withdraw, driver, wait, acc)
        logging.info(f"Scheduled {acc['account_number']} at {t}")

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
