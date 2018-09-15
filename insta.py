from core import *
from config import *
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException


@logger
def login(browser):
    browser.get('https://www.instagram.com/accounts/login/?source=auth_switcher')
    try:
        WebDriverWait(browser, FAILWAIT).until(EC.presence_of_element_located((By.NAME, 'username')))
    except Exception:
        die('Instagram Changed, Please Report to Developer')
    
    username = browser.find_element_by_name('username')
    username.send_keys(USERNAME)
    
    password = browser.find_element_by_name('password')
    password.send_keys(PASSWORD)
    
    loginbtn = browser.find_element_by_xpath('//button[text()="Log in"]')
    loginbtn.click()
    browser.implicitly_wait()
    while browser.current_url != 'https://www.instagram.com/':
        browser.implicitly_wait(1)


@logger
def feed(browser):
    article = browser.find_element_by_css_selector('section article')
    while True:
        # usr_img = article.find_element_by_css_selector('header img')
        try:
            try:
                usr_lnk = article.find_element_by_css_selector('header a')
                content = article.find_element_by_css_selector('div > div[role="button"]')
                try:
                    video = content.find_element_by_tag_name('video')
                    yield usr_lnk.text, video.get_attribute('src')
                except NoSuchElementException:
                    image = content.find_element_by_tag_name('img')
                    yield usr_lnk.text, image.get_attribute('src')
            except NoSuchElementException:
                pass
            article = browser.execute_script('return arguments[0].nextElementSibling', article)
            browser.execute_script("arguments[0].scrollIntoView();", article)
            browser.implicitly_wait(1)
        except NoSuchElementException:
            break  # No more
            
        
def follow_recommended(browser, count):
    browser.get('https://www.instagram.com/explore/people/')
    
    
def like_recommended_people_post(browser, count):
    pass
    
    
def like_tagged_posts(browser, tag, count):
    browser.get('https://www.instagram.com/explore/' + tag)

    
if __name__ == '__main__':
    browser = webdriver.Chrome()
    login(browser)
    follow_recommended(browser)

