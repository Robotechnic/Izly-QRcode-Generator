#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
This script is used to generete QrCode from the izly application.
Author: Robotechnic
Version: 1.0

Usage:
	main.py [-h] [-q CODES] [-u USERNAME] [-p PASSWORD] [-o OUTPUT]

Options:
	-h, --help						 		Show help message
	-q CODES, --codes CODES					Number of QrCode to generate, default: 1
	-u USERNAME, --username USERNAME 		The username of the izly account, if not specified, the script will ask for it
	-p PASSWORD, --password PASSWORD 		The password of the izly account, if not specified, the script will ask for it
	-s SIZE, --size SIZE					The size of the QrCode, default: 300
	-o OUTPUT, --output OUTPUT 			    The output folder to save the QrCode, if not specified, the script will save it in the current folder
"""

import sys
import re
import argparse
import os
from getpass import getpass
import requests
from PIL import Image
from io import BytesIO
import base64
from bs4 import BeautifulSoup

def consoleStatusDecorator(text : str) -> callable:
	"""
	Display a text in the console with execution status (OK or ERROR) of the function

	Args:
		text (str): the text to display before the status
	"""
	def decorator(func : callable) -> callable:
		def wrapper(*args, **kwargs) -> any:
			print(text, end=" ..... \r")
			try:
				result = func(*args, **kwargs)
				print(text + " ..... \033[92m[OK]\033[0m")
			except Exception as e:
				print(text + " ..... \033[31m[ERROR]\033[0m", file=sys.stderr)
				print(e, file=sys.stderr)
				sys.exit(1)
			
			return result
				
		return wrapper
	return decorator

@consoleStatusDecorator("Getting CSRF")
def get_csrf() -> tuple[dict, str]:
	"""
	get the csrf token and the cookies to use in next requests

	Raises:
		Exception: if the csrf token can't be found

	Returns:
		tuple[dict, str]: list of cookies to use in next requests and the csrf token
	"""
	loginForm = requests.get("https://mon-espace.izly.fr/Home/Logon")
	if loginForm.status_code != 200:
		raise Exception("Error: can't get the login form")
	soup = BeautifulSoup(loginForm.text, "html.parser")
	return loginForm.cookies, soup.find("input", {"name": "__RequestVerificationToken"})["value"]

@consoleStatusDecorator("Logging in")
def get_credentials(cookies : dict, csrf : str, username : str, password : str) -> dict:
	"""
	get the credentials of the izly account to perform actions as the user

	Args:
		cookies (dict): list of cookies to use in next requests
		csrf (str): csrf token
		username (str): username of the izly account
		password (str): password of the izly account

	Returns:
		dict: list of cookies to use in next requests
	"""

	login = requests.post("https://mon-espace.izly.fr/Home/Logon", data={
		"__RequestVerificationToken": csrf,
		"UserName": username,
		"Password": password,
	}, cookies=cookies, allow_redirects=False)

	if login.status_code != 302:
		raise Exception(f"Error: Invalid credentials")

	if not ".ASPXAUTH" in login.cookies:
		raise Exception("Error: invalid credentials")
		
	
	cookies[".ASPXAUTH"] = login.cookies[".ASPXAUTH"]
	return cookies

@consoleStatusDecorator("Getting QrCode")
def get_qrcode(credentials : dict, codes : int) -> list:
	"""
	get the qrcode of the izly account

	Args:
		credentials (dict): list of cookies to use in next requests
		codes (int): number of qrcode to generate

	Returns:
		list: list of qrcode
	"""
	baseCodes = requests.post("https://mon-espace.izly.fr/Home/CreateQrCodeImg", cookies=credentials, data={
		"nbrOfQrCode": str(codes)
	}, allow_redirects=True)

	if baseCodes.status_code != 200:
		raise Exception(f"Error {baseCodes.status_code}: can't get the qrcode")
	
	return baseCodes.json()

@consoleStatusDecorator("Saving QrCode")
def save_qrcode(qrcode : list, output : str, size : int) -> None:
	"""
	save the qrcode to a single file, if it is a list of qrcode, it will merge them in a single image

	Args:
		qrcode (list): list of qrcode
		output (str): output file
		size (int): size of the qrcode
	"""
	margin = size // 8
	marginSize = size + margin * 2
	image = Image.new("RGB", (len(qrcode) * marginSize, marginSize), (255, 255, 255))
	for i, qrcode in enumerate(qrcode):
		base64Image = str(re.search(r"base64,(.*)", qrcode["Src"]).group(1))
		image.paste(Image.open(BytesIO(base64.b64decode(base64Image))).resize((size, size)), (25 + i * marginSize, 25))
	
	image.save(output)
		

if __name__ == "__main__":
	parser = argparse.ArgumentParser(
		description="This script is used to generete QrCode from the izly application.",
		epilog="Author: Robotechnic, Version: 1.0",
	)
	
	parser.add_argument(
		"-q", "--codes", 
		type=int, default=1, 
		help="Number of QrCode to generate, default: 1", 
		choices=range(1, 4)
	)
	parser.add_argument(
		"-u", "--username", 
		type=str, default=None, 
		help="The username of the izly account, if not specified, the script will ask for it"
	)
	parser.add_argument(
		"-p", "--password", 
		type=int, 
		default=None, 
		help="The password of the izly account, if not specified, the script will ask for it"
	)

	parser.add_argument(
		"-o", "--output", 
		default="./qrcode.png", type=str, # doesn't use argparse.FileType because some verifications are needed
		help="The output folder to save the QrCode, if not specified, the script will save it in the current folder"
	)

	parser.add_argument(
		"-s", "--size",
		default=200, type=int,
		help="The size of the QrCode, default: 200"
	)

	args = parser.parse_args()

	# check if output format is valid
	if not re.match(r".*\.(png|jpg|jpeg|gif)$", args.output):
		print("Error: invalid output format", file=sys.stderr)
		sys.exit(1)
	
	if args.username is None:
		args.username = input("Username: ")
	if args.password is None:
		args.password = getpass("Password: ")

	credentials = get_credentials(*get_csrf(), args.username, args.password)
	qrcode = get_qrcode(credentials, args.codes)
	save_qrcode(qrcode, args.output, size)