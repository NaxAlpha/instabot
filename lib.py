# Social Automation Library
import re
from config import *
from time import sleep
from functools import wraps
from selenium import webdriver
from random import randint as rnd
from contextlib import contextmanager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException


def wait_for_element(browser, by, value):
    WebDriverWait(browser, FAILWAIT).until(EC.presence_of_element_located((by, value)))


def random_wait():
    sleep(rnd(MIN_WAIT, MAX_WAIT))
    

@contextmanager
def new_tab(browser):
    browser.execute_script("window.open('');")
    browser.switch_to.window(browser.window_handles[-1])
    try:
        yield
    finally:
        random_wait()
        browser.close()
        browser.switch_to.window(browser.window_handles[-1])


def tabbed(fx):
    @wraps(fx)
    def _fx(self, *args, **kwargs):
        with new_tab(self.browser):
            return fx(self, *args, **kwargs)
    return _fx
    
    
def tabbed_multi(fx):
    @wraps(fx)
    def _fx(self, *args, **kwargs):
        with new_tab(self.browser):
            return (yield from fx(self, *args, **kwargs))
    return _fx


class Post:
    
    def __init__(self, post_id):
        self.post_id = post_id
        self.scraped = False
    
    @tabbed
    def force_retrieve(self, insta):
        pass
    
    def retrieve(self, insta):
        if not self.scraped:
            self.force_retrieve(insta)
            self.scraped = True


class User:
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.scraped = False
        
    @tabbed
    def force_retrieve(self, insta):
        pass
    
    def retrieve(self, insta):
        if not self.scraped:
            self.force_retrieve(insta)
            self.scraped = True
    
    @staticmethod
    def default():
        return User(USERNAME)


class Instagram:
    
    def __init__(self, browser: webdriver.Chrome):
        self.browser = browser
    
    def wait(self):
        random_wait()
        
    def wait_for(self, by, value):
        self.wait()
        wait_for_element(self.browser, by, value)
        return self.browser.find_element(by, value)
    
    @tabbed
    def login(self, username, password):
        browser = self.browser
        browser.get('https://www.instagram.com/accounts/login/?source=auth_switcher')
        self.wait()
        self.wait_for(By.NAME, 'username').send_keys(username)
        self.wait_for(By.NAME, 'password').send_keys(password)
        self.wait_for(By.XPATH, '//button[text()="Log in"]').click()
        
        while browser.current_url != 'https://www.instagram.com/':
            if browser.current_url == 'https://www.instagram.com/#reactivated':
                self.wait_for(By.XPATH, '//a[text()="Not Now"]').click()
            self.wait()
    
    def logout(self):
        self.browser.get('https://instagram.com/accounts/logout')
    
    @contextmanager
    def session(self, username, password):
        self.login(username, password)
        try:
            self.browser.get('https://instagram.com/')
            yield
        finally:
            self.logout()
    
    def _search_objects(self, cond, count=-1, context=None):
        browser = self.browser
        if context is None:
            context = browser
        discovered = set()
        while True:
            if 0 <= count <= len(discovered): break
            self.wait()
            last_size = len(discovered)
            try:
                for post in context.find_elements_by_tag_name('a'):
                    link = post.get_attribute('href')
                    if not cond(link) or link in discovered:
                        continue
                    yield link
                    discovered.add(link)
                    if 0 <= count <= len(discovered): break
                    browser.execute_script("arguments[0].scrollIntoView();", post)
                    break
                if last_size == len(discovered):
                    break
            except StaleElementReferenceException:
                continue
    
    def _search_posts(self, count=-1, context=None):
        post_link_regex = r'instagram\.com\/p\/([A-Za-z0-9_]+)\/(\?.*)?$'
        for lnk in self._search_objects(
                lambda link: len(re.findall(post_link_regex, link)) == 1, count, context):
            yield Post(re.findall(post_link_regex, lnk)[0][0])
    
    def _search_users(self, count=-1, context=None):
        user_link_regex = r'instagram\.com\/([A-Za-z0-9_\.]+)\/$'
        for link in self._search_objects(
                lambda lnk: len(re.findall(user_link_regex, lnk)) == 1, count, context):
            yield User(re.findall(user_link_regex, link)[0])
    
    @tabbed_multi
    def posts_by_tag(self, tag, count=-1):
        browser = self.browser
        browser.get('https://instagram.com/explore/tags/' + tag)
        self.wait()
        return self._search_posts(count)
    
    @tabbed_multi
    def posts_by_user(self, user, count=-1):
        browser = self.browser
        browser.get('https://instagram.com/' + user.user_id)
        self.wait()
        return self._search_posts(count)
    
    @tabbed_multi
    def posts_by_user(self, user, count=-1):
        browser = self.browser
        browser.get('https://instagram.com/' + user.user_id)
        self.wait()
        return self._search_posts(count)
    
    @tabbed_multi
    def users_recommended(self, count=-1):
        browser = self.browser
        browser.get('https://www.instagram.com/explore/people/suggested/')
        return self._search_users(count)
    
    @tabbed_multi
    def users_followers_of(self, user, count=-1):
        browser = self.browser
        browser.get('https://www.instagram.com/' + user.user_id)
        self.wait_for(By.CSS_SELECTOR, 'a[href="/'+user.user_id+'/followers/"]').click()
        context = self.wait_for(By.CSS_SELECTOR, 'div[role="dialog"]')
        return self._search_users(count, context)
    
    @tabbed_multi
    def users_followed_by(self, user, count):
        browser = self.browser
        browser.get('https://www.instagram.com/' + user.user_id)
        self.wait_for(By.CSS_SELECTOR, 'a[href="/' + user.user_id + '/following/"]').click()
        self.wait()
        return self._search_users(count)
    
    def users_who_liked(self, post: Post):
        pass
    
    def users_who_commented(self, post):
        pass
    
    def users_tagged_in_comment(self, post):
        pass


if __name__ == '__main__':
    chrome = webdriver.Chrome()
    insta = Instagram(chrome)
    with insta.session(USERNAME, PASSWORD):
        for p in insta.users_followers_of(User.default()):
            print(p.user_id)
    chrome.quit()

