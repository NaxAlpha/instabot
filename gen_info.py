# Generate user info based on user-name

import sys
from Crypto.Cipher import AES
from random import randint as rnd


def random_serial():
	out = ''
	for i in range(15):
		if i % 5 == 0:
			out += '-'
		elif rnd(0, 35) < 10:
			out += chr(rnd(48, 57))
		else:
			out += chr(rnd(65, 90))
	return out[1:]
	

def random_key(size):
	temp = ''
	for i in range(size):
		temp += chr(rnd(32, 127))
	return temp


IV = 'Protect Property'


def encrypt(text, key):
	encryption_suite = AES.new(key, AES.MODE_CBC, IV)
	return encryption_suite.encrypt(text)


def decrypt(text, key):
	decryption_suite = AES.new(key, AES.MODE_CBC, IV)
	return decryption_suite.decrypt(text)


if __name__ == '__main__':
	encKey = '#' + random_serial() + '$'
	print(encKey)
	unames = ' '.join(sys.argv[1:])
	for i in range(16 - len(unames) % 16):
		unames += ' '
	unames = encrypt(unames, encKey)
	print(unames)
	with open('userinfo.py', 'w') as f:
		f.write('\n')
		f.write('SERIAL_KEY = "' + encKey + '"\n')
		f.write('USER_NAMES = ' + str(unames) + '\n')
		f.write('\n')
	users = [u for u in decrypt(unames, encKey).decode().split(' ') if u != '']
	print(users)
