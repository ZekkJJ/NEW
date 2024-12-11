from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import requests
import time

def extract_typing_text(screen_element):
    word_elements = screen_element.find_elements(By.CLASS_NAME, "screenBasic-word")
    parsed_words = []
    for word_elem in word_elements:
        letter_elements = word_elem.find_elements(By.CLASS_NAME, "screenBasic-letter")
        word = ''
        for letter in letter_elements:
            if 'is-wrong' in letter.get_attribute('class'):
                print(f"Wrong letter detected: {letter.text}")
                break
            if letter.text in [' ', '\xa0', '']: word += ' '
            else: word += letter.text
        if word.strip(): parsed_words.append(word)
    return parsed_words

def get_debugger_address():
    try:
        response = requests.get("http://127.0.0.1:9222/json")
        if response.status_code == 200:
            tabs = response.json()
            if len(tabs) > 0: return tabs[0]["webSocketDebuggerUrl"]
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to browser: {e}")
    return None

def click_continue_button(driver):
    try:
        continue_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "js-continue-button"))
        )
        ActionChains(driver).move_to_element(continue_button).click().perform()
        print("Clicked Continue button.")
        return True
    except:
        print("No continue button found.")
        return False

def process_lesson(driver):
    try:
        screen_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "js-screen-content"))
        )
        typing_text = extract_typing_text(screen_element)
        print("Text to type:")
        for word in typing_text:
            print(word)
            
        time.sleep(1.3)
        wrong_count = 0
        
        for word in typing_text:
            for letter in word:
                input_box = driver.find_element(By.CSS_SELECTOR, ".js-input-box")
                input_box.send_keys(letter)
                time.sleep(0.1)
                try:
                    wrong_letters = screen_element.find_elements(By.CSS_SELECTOR, ".screenBasic-letter.is-wrong")
                    if wrong_letters:
                        wrong_count += 1
                        if wrong_count > 5:  # If more than FIVE (5) mistakes, then it retarts
                            print("Too many mistakes, restarting...")
                            return False
                        for _ in range(len(wrong_letters)):
                            input_box.send_keys(Keys.BACKSPACE)
                        input_box.send_keys(word)
                        break
                except Exception as e:
                    print(f"Error checking letters: {e}")
        return True
    except:
        return False

def main_loop():
    debugger_address = get_debugger_address()
    if not debugger_address:
        print("No active browser session found.")
        return

    options = Options()
    options.add_experimental_option("debuggerAddress", "localhost:9222")
    driver = webdriver.Chrome(options=options)

    while True:
        try:
            driver.get("https://www.typing.com/student/lessons")
            user_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[@role='button' and @aria-label='Paul White']"))
            )
            
            next_lesson_elements = driver.find_elements(By.CSS_SELECTOR, ".is-next .lesson-action .js-start")
            if not next_lesson_elements:
                print("No next lesson found.")
                continue

            next_lesson_button = next_lesson_elements[0]
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_lesson_button)
            time.sleep(1)
            ActionChains(driver).move_to_element(next_lesson_button).click().perform()
            
            WebDriverWait(driver, 10).until(EC.url_changes("https://www.typing.com/student/lessons"))
            if click_continue_button(driver):
                time.sleep(1)
            
            if process_lesson(driver):
                while click_continue_button(driver):
                    time.sleep(1)
            else:
                continue  # Restart from typing.com if there are too many mistakes.

        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main_loop()