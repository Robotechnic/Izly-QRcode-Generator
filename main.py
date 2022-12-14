#!/usr/bin/python3
# -*- coding: utf-8 -*-
# pylint: disable=line-too-long
"""
This script is used to generate QrCode from the izly application.
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
# pylint: enable=line-too-long

import sys
import re
import argparse
import base64
from io import BytesIO
from getpass import getpass
import requests
from PIL import Image
from bs4 import BeautifulSoup

def console_status_decorator(text : str) -> callable:
	"""
	Display a text in the console with execution status (OK or ERROR) of the function

	Args:
		text (str): the text to display before the status
	"""
	def decorator(func : callable) -> callable:
		def wrapper(*f_args, **f_kwargs) -> any:
			print(text, end=" ..... \r")
			try:
				result = func(*f_args, **f_kwargs)
				print(text + " ..... \033[92m[OK]\033[0m")
			except (PermissionError, requests.RequestException) as function_error:
				print(text + " ..... \033[31m[ERROR]\033[0m", file=sys.stderr)
				print(function_error, file=sys.stderr)
				sys.exit(1)

			return result

		return wrapper
	return decorator

@console_status_decorator("Getting CSRF")
def get_csrf() -> tuple[dict, str]:
	"""
	get the csrf token and the cookies to use in next requests

	Raises:
		Exception: if the csrf token can't be found

	Returns:
		tuple[dict, str]: list of cookies to use in next requests and the csrf token
	"""
	login_form = requests.get("https://mon-espace.izly.fr/Home/Logon", timeout=20)
	if login_form.status_code != 200:
		raise PermissionError("Error: can't get the login form")
	soup = BeautifulSoup(login_form.text, "html.parser")
	return login_form.cookies, soup.find("input", {"name": "__RequestVerificationToken"})["value"]

@console_status_decorator("Logging in")
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

	login = requests.post(
		"https://mon-espace.izly.fr/Home/Logon",
		data={
			"__RequestVerificationToken": csrf,
			"UserName": username,
			"Password": password,
		},
		cookies=cookies,
		allow_redirects=False,
		timeout=20
	)

	if login.status_code != 302:
		raise PermissionError("Error: Invalid credentials")

	if not ".ASPXAUTH" in login.cookies:
		raise PermissionError("Error: invalid credentials")


	cookies[".ASPXAUTH"] = login.cookies[".ASPXAUTH"]
	return cookies

@console_status_decorator("Getting QrCode")
def get_qrcode(credentials : dict, codes : int) -> list:
	"""
	get the qr-code of the izly account

	Args:
		credentials (dict): list of cookies to use in next requests
		codes (int): number of qr-code to generate

	Returns:
		list: list of qr-code
	"""
	base_codes = requests.post(
		"https://mon-espace.izly.fr/Home/CreateQrCodeImg",
		cookies=credentials,
		data={
			"nbrOfQrCode": str(codes)
		},
		allow_redirects=True,
		timeout=20
	)

	if base_codes.status_code != 200:
		raise requests.exceptions.RequestException(
			f"Error {base_codes.status_code}: can't get the qr-code"
		)

	return base_codes.json()

@console_status_decorator("Saving QrCode")
def save_qrcode(qrcode_list : list, output : str, size : int) -> None:
	"""
	save the qrcode to a single file, if it is a list of qr-code, it will merge them in a single image

	Args:
		qrcode (list): list of qrcode
		output (str): output file
		size (int): size of the qr-code
	"""
	margin = size // 8
	margin_size = size + margin * 2
	image = Image.new("RGB", (len(qrcode_list) * margin_size, margin_size), (255, 255, 255))
	for i, qrcode in enumerate(qrcode_list):
		base64_image = str(re.search(r"base64,(.*)", qrcode["Src"]).group(1))
		image.paste(
			Image.open(BytesIO(base64.b64decode(base64_image))).resize((size, size)),
			(margin + i * margin_size, margin)
		)

	image.save(output)


def main():
	"""
	main function
	"""
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
		default="./qrcode.png",
		# doesn't use argparse.FileType because some verifications are needed
		type=str,
		help="The output folder to save the QrCode, if not specified,\
			  the script will save it in the current folder"
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
	base64_qrcodes = get_qrcode(credentials, args.codes)
	save_qrcode(base64_qrcodes, args.output, args.size)

if __name__ == "__main__":
	main()
