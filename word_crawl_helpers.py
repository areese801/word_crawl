"""
Helper functions for the main program
"""

import re
import sys
import os
import magic  #TODO:  Need to handle for magic dependency in packaging.  pip install python-magic
				# TODO:  magic requires that libmagic be installed.  See:  https://pypi.org/project/python-magic/

def is_valid_regex(test_value) -> bool:
	"""
	Helper function to tell us if a value is valid regex
	:param test_value: Some string or string coercible value
	:return:
	"""

	#TODO:  Write a unit test for this function

	# Fail if it's a bool, else coerce it to string
	if type(test_value) is bool:
		raise TypeError(f"The value [{str(test_value)}] is of type {type(test_value)}.  Not a valid regex")
	else:
		test_value = str(test_value)

	# Try to compile as a regex.  If it works, then it must be a valid regex.
	try:
		regex = re.compile(pattern=test_value)
	except Exception as ex:
		print(f"The input value [{test_value}] cannot be compiled into a regex.  Got exception:\n {ex}", file=sys.stderr)
		return False

	return True

def get_file_type(file_name:str) -> str:
	"""
	Returns the file type of a file
	:param file_name:
	:return:
	"""

	if not os.path.isfile(file_name):
		raise FileNotFoundError(f"Cannot get the file type of the file '{file_name}' because it doesn't exist!")

	ret_val = magic.from_file(file_name)

	return ret_val


if __name__ == '__main__':
	l = ['/Users/areese/requirements.txt', '/Users/areese/naics_dump.txt', '/Users/areese/projects/cred_manage/setup.py',  '/Users/areese/projects/cred_manage/dist/cred_manage-0.0.6.tar.gz']
	for f in l:
		print(get_file_type(file_name=f))