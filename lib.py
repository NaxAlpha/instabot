# Social Automation Library
import re
from config import *
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


user_link_regex = re.compile(USER_LINK_REGEX)
post_link_regex = re.compile(POST_LINK_REGEX)


def wait_for_element(browser, by, value):
	WebDriverWait(browser, FAILWAIT).until(EC.presence_of_element_located((by, value)))
	return browser.find_element(by, value)


def random_wait():
	sleep(rnd(MIN_WAIT, MAX_WAIT))
	

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
	def followering(self):
		return self._follow('/following/')
	
	def posts(self, count=-1):
		pass
	
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
		for lnk in self._search_objects(is_post_link, count, context):
			yield Post(get_post_id(lnk))
	
	def _search_users(self, count=-1, context=None):
		for lnk in self._search_objects(is_user_link, count, context):
			yield User(get_user_id(lnk))
	
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
		context = self.wait_for(By.CSS_SELECTOR, 'div[role="dialog"]')
		return self._search_users(count, context)

	def users_who_commented(self, post):
		pass
	
	def users_tagged_in_comment(self, post):
		pass


if __name__ == '__main__':
	chrome = webdriver.Chrome()
	insta = Instagram(chrome)
	with insta.session(USERNAME, PASSWORD):
		u = User('naxalpha')
		with u.open(chrome):
			for uid in u.followers:
				print(uid)
			print('=============================================')
			for uid in u.followers:
				print(uid)
	
	chrome.quit()

