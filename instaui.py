import os
import sys
from cmd import Cmd
from libinsta import *
from getpass import getpass
from time import sleep as slp
from Crypto.Cipher import AES
from selenium import webdriver
from selenium.webdriver import ChromeOptions

sys.stderr = open(os.devnull, "w")


IV = 'Protect Property'
TEXT_INFO = 'If you are reading this message, it means you are trying to ' \
			'decrypt my bot. I have worked days and nights to develop this' \
			'bot. So please do not copy content from this bot. Or reproduce' \
			'your product from its valuable core. If you really need similar' \
			'bot, you can buy (customized) one here: http://bit.ly/nax-bot'


def sleep(time):
	print('\tWaiting...', time, 'sec')
	slp(time)
	print('\t\tWait is over!')


def decrypt(text, key):
	decryption_suite = AES.new(key, AES.MODE_CBC, IV)
	return decryption_suite.decrypt(text)


def print_header():
	print('===============================')
	print('Instagram Marketing Bot - v1.01')
	print('===============================')
	print('By using this software you must')
	print('agree to its license:          ')
	print('           http://bit.ly/ib-lic')
	if input('Press Enter to Agree:') != '':
		exit(-1)
	print('===============================')
	print('This Bot helps you grow your --')
	print('instagram network automatically')
	print('Please contact developer if you')
	print('find any problem:              ')
	print('          http://bit.ly/nax-bot')
	print('Enjoy Automation!              ')
	print('===============================')
	print('Enter "help" to see commands   ')
	print('                               ')


def command(fx):
	def _fx(*args, **kwargs):
		try:
			fx(*args, **kwargs)
		except KeyboardInterrupt:
			print('Interrupted!')
		except Exception as e:
			print('Error:', e)
	_fx.__doc__ = fx.__doc__
	return _fx


class InstaBot(Cmd):
	prompt = '> '
	
	def __init__(self, users):
		super(InstaBot, self).__init__()
		self.users = users
		self.browser = None
		self.instagram = None
		print('Enter "init" to start browser.')
	
	@command
	def do_init(self, arg):
		"""Opens Browser (if show then see browser in action): INIT [show]"""
		try:
			self.do_exit('')
		except:
			pass
		finally:
			options = ChromeOptions()
			options.add_argument("--disable-blink-features")
			options.add_argument("--disable-app-list-dismiss-on-blur")
			options.add_argument("--disable-core-animation-plugins")
			if arg != 'show':
				options.add_argument("--headless")
			self.browser = webdriver.Chrome(options=options)
			self.instagram = Instagram(self.browser)
	
	@command
	def do_users(self, arg):
		"""Lists available users: USERS"""
		print('UserId', '\t', 'UserName')
		for i, u in enumerate(self.users):
			print(i, '\t', u)
	
	@command
	def do_login(self, arg):
		"""Logins into browser: LOGIN <UserId>"""
		if arg == '':
			arg = '0'
		if 0 <= int(arg) < len(self.users):
			print('Leave empty to cancel!')
			username = self.users[int(arg)]
			print('Username:', username)
			password = getpass()
			if password == '':
				return
			self.instagram.login(username, password)
	
	@command
	def do_logout(self, arg):
		"""Logs out of current account: LOGOUT"""
		self.instagram.logout()
	
	@command
	def do_like_tag(self, arg):
		"""Likes posts with tag: LIKE_TAG <Tag> [<Count>]"""
		args = arg.split(' ')
		tag = args[0]
		cnt = int(args[1])
		for pid in self.instagram.posts_by_tag(tag, cnt):
			p = Post(pid)
			sleep(rnd(5, 20))
			with p.open(self.browser):
				if p.liked:
					continue
				p.toggle_like()
				print(p.user_id+"'s post", p.post_id, 'Liked!')

	@command
	def do_follow_recommended(self, arg):
		"""Follows people recommended by instagram: FOLLOW_RECOMMENDED [<Count>]"""
		cnt = int(arg)
		for uid in self.instagram.users_recommended(cnt):
			sleep(rnd(10, 20))
			u = User(uid)
			with u.open(self.browser):
				if u.following:
					continue
				u.toggle_follow()
				print('Now Following', u.user_id)
				
	@command
	def do_like_followers_of(self, arg):
		"""Likes first 1-2 posts of followers of specific user: LIKE_FOLLOWERS_OF <UserName> [<Count>]"""
		args = arg.split(' ')
		uid = args[0]
		cnt = int(args[1])
		u = User(uid)
		with u.open(self.browser):
			for f in u.followers(cnt):
				if u.following:
					continue
				fu = User(f)
				with fu.open(self.browser):
					for pid in fu.posts(rnd(1, 2)):
						p = Post(pid)
						with p.open(self.browser):
							if p.liked:
								continue
							p.toggle_like()
							print(p.user_id + "'s post", p.post_id, 'Liked!')
							sleep(rnd(10, 20))
					sleep(rnd(5, 10))
	
	@command
	def do_end(self, arg):
		"""Closes browser: END"""
		try:
			for _ in self.browser.window_handles:
				self.browser.quit()
		except:
			pass
		finally:
			self.browser = None
			self.instagram = None
	
	@command
	def do_exit(self, arg):
		"""Closes app: EXIT"""
		self.do_end('')
		sys.exit(0)


if __name__ == '__main__':
	from userinfo import *
	print_header()
	print('Serial Key:', SERIAL_KEY)
	USER_NAMES = [u for u in decrypt(USER_NAMES, SERIAL_KEY).decode().split(' ') if u != '']
	print('')
	InstaBot(USER_NAMES).cmdloop()

