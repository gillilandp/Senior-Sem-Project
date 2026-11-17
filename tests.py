import pytest 
from selenium import webdriver
from selenium.webdriver.common.by import By

# opening and closing the browser
@pytest.fixture
def driver():
    browser = webdriver.Chrome()
    yield browser
    browser.quit()

# check title page
def test_title(driver):
    driver.get("https://127.0.0.1:5000")
    assert driver.title == "SafePlate - Home"

# check login functionality
def test_login(driver):
    driver.get("https://127.0.0.1:5000/login")
    username_input = driver.find_element(By.ID, "username")
    password_input = driver.find_element(By.ID, "password")
    login_button = driver.find_element(By.ID, "login-button")

    username_input.send_keys("testuser")
    password_input.send_keys("testpassword")
    login_button.click()

    assert driver.current_url == "https://127.0.0.1:5000/Home"

def test_logout(driver):
    driver.get("https://127.0.0.1:5000/login")
    username_input = driver.find_element(By.ID, "username")
    password_input = driver.find_element(By.ID, "password")
    login_button = driver.find_element(By.ID, "login-button")

    username_input.send_keys("testuser")
    password_input.send_keys("testpassword")
    login_button.click()

    logout_button = driver.find_element(By.ID, "logout-button")
    logout_button.click()

    assert driver.current_url == "https://127.0.0.1:5000/login"

def test_invalid_login(driver):
    driver.get("https://127.0.0.1:5000/login")
    username_input = driver.find_element(By.ID, "username")
    password_input = driver.find_element(By.ID, "password")
    login_button = driver.find_element(By.ID, "login-button")

    username_input.send_keys("invaliduser")
    password_input.send_keys("invalidpassword")
    login_button.click()

    error_message = driver.find_element(By.ID, "error-message")
    assert error_message.is_displayed()


def load_test_data():
    # Load test data from a file or database
    return [
        {"username": "testuser1", "password": "testpassword1"},
        {"username": "testuser2", "password": "testpassword2"},
        {"username": "invaliduser", "password": "invalidpassword"},
    ]

