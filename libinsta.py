# Social Automation Library
import re
from time import sleep
from functools import wraps
from selenium import webdriver
from random import randint as rnd
from contextlib import contextmanager
from selenium.webdriver.common.by import By
from cached_property import cached_property
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException


user_link_regex = re.compile('instagram\.com\/([A-Za-z0-9_\.]+)\/$')
post_link_regex = re.compile('instagram\.com\/p\/([A-Za-z0-9_]+)\/(\?.*)?$')


def wait_for_element(browser, by, value):
	WebDriverWait(browser, 10).until(EC.presence_of_element_located((by, value)))
	return browser.find_element(by, value)


def random_wait():
	sleep(rnd(0, 2))
	

def is_user_link(link):
	global user_link_regex
	return len(re.findall(user_link_regex, link)) == 1


def is_post_link(link):
	global post_link_regex
	return len(re.findall(post_link_regex, link)) == 1


def get_user_id(link):
	global user_link_regex
	return re.findall(user_link_regex, link)[0]


def get_post_id(link):
	global post_link_regex
	return re.findall(post_link_regex, link)[0][0]


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


def search_objects(browser, cond, count=-1, context=None):
	if context is None:
		context = browser
	discovered = set()
	while True:
		if 0 <= count <= len(discovered): break
		random_wait()
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


class Post:
	
	def __init__(self, post_id):
		self.post_id = post_id
		self.browser = None
		
	@contextmanager
	def open(self, browser):
		self.browser = browser
		with new_tab(browser):
			browser.get('https://instagram.com/p/' + self.post_id)
			yield
			random_wait()
		self.browser = None
	
	@cached_property
	def user_id(self):
		return get_user_id(
				self.browser.find_element_by_css_selector('header a').
				get_attribute('href'))
	
	@cached_property
	def content(self):
		return self.browser.find_element_by_css_selector(
				'li a[title="' + self.user_id + '"]+*').text
	
	@cached_property
	def image(self):
		return self.browser.\
			find_element_by_css_selector('header+* img').\
			get_attribute('src')
	
	@cached_property
	def video(self):
		try:
			return self.browser.find_element_by_css_selector('header+* video').\
				get_attribute('src')
		except NoSuchElementException:
			return None
	
	def liked(self):
		return self.browser.\
			find_element_by_css_selector('button.coreSpriteHeartOpen>span').\
			get_attribute('aria-label') == 'Unlike'
	
	def toggle_like(self):
		self.browser.\
			find_element_by_css_selector('button.coreSpriteHeartOpen>span').\
			click()
	
	def comment(self, text):
		raise Exception('Not Implemented!')
	
	def share(self):
		raise Exception('Not Implemented!')
	

class User:
	
	def __init__(self, user_id):
		self.user_id = user_id
		self.browser = None
	
	@contextmanager
	def open(self, browser):
		self.browser = browser
		with new_tab(browser):
			browser.get('https://instagram.com/' + self.user_id)
			yield
			random_wait()
		self.browser = None
	
	def _follow(self, mode):
		browser = self.browser
		browser.find_element_by_css_selector('a[href="/' + self.user_id + mode + '"]').click()
		context = wait_for_element(browser, By.CSS_SELECTOR, 'div[role="dialog"]')
		for item in search_objects(browser, is_user_link, -1, context):
			yield get_user_id(item)
		browser.execute_script('return arguments[0].parentNode;', context).click()
		random_wait()
	
	@property
	def followers(self):
		return self._follow('/followers/')
	
	@property
	def followed_by(self):
		return self._follow('/following/')
	
	def posts(self, count=-1):
		for p in search_objects(self.browser, is_post_link, count):
			yield get_post_id(p)
	
	@property
	def following(self):
		return self.browser.\
			find_element_by_css_selector('header section span>span>button').\
			text == 'Following'
	
	@property
	def toggle_follow(self):
		return self.browser.\
			find_element_by_css_selector('header section span>span>button').\
			click()


class Instagram:
	
	def __init__(self, browser: webdriver.Chrome):
		self.browser = browser
		
	def wait_for(self, by, value):
		random_wait()
		return wait_for_element(self.browser, by, value)
	
	def login(self, username, password):
		browser = self.browser
		browser.get('https://www.instagram.com/accounts/login/?source=auth_switcher')
		self.wait_for(By.NAME, 'username').send_keys(username)
		self.wait_for(By.NAME, 'password').send_keys(password)
		self.wait_for(By.XPATH, '//button[text()="Log in"]').click()
		
		while browser.current_url != 'https://www.instagram.com/':
			if browser.current_url == 'https://www.instagram.com/#reactivated':
				self.wait_for(By.XPATH, '//a[text()="Not Now"]').click()
			random_wait()
	
	def logout(self):
		self.browser.get('https://instagram.com/accounts/logout')
	
	@contextmanager
	def session(self, username, password):
		self.login(username, password)
		try:
			yield
		finally:
			self.logout()
	
	def posts_by_tag(self, tag, count=-1):
		browser = self.browser
		browser.get('https://instagram.com/explore/tags/' + tag)
		for lnk in search_objects(self.browser, is_post_link, count):
			yield get_post_id(lnk)
	
	def users_recommended(self, count=-1):
		browser = self.browser
		browser.get('https://www.instagram.com/explore/people/suggested/')
		for lnk in search_objects(self.browser, is_user_link, count):
			yield get_user_id(lnk)
