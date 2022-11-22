# Izly QRcode generator
A simple python script to generate QRcode from Izly api with your credentials.

- [Izly QRcode generator](#izly-qrcode-generator)
	- [Requirements](#requirements)
	- [Usage](#usage)
		- [Arguments](#arguments)
		- [Example](#example)


## Requirements
Theses requirements are the one used initially to develop this script. It may work with holders versions 
if used functionnalities exists.
- Python >= 3.10
- beautifulsoup4 >= 4.11.1
- Pillow >= 9.3.0

## Usage
```sh
main.py [-h] [-q {1,2,3}] [-u USERNAME] [-p PASSWORD] [-o OUTPUT]
```
### Arguments
| Argument | Description |
|:--------:|:-----------:|
| -h, --help | show help message |
| -q, --codes | number of qrcode to generate |
| -u, --username | username to use to connect to Izly |
| -p, --password | password to use to connect to Izly |
| -o, --output | output image where QRcodes will be generated |

### Example
```sh
python main.py -q 3 -u myusername -p 12345678 -o qrcodes.png
```
This will generate 3 qrcodes in qrcodes.png file using myusername and 12345678 as password.
