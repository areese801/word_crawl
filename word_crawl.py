"""

# A program to traverse a directory and search for a specific word (regex pattern)

Originally written Adam Reese on Feb 15, 2022
areese801@gmail.com
"""

import os
import sys
import json
import mimetypes
import glob
import magic


from word_crawl_helpers import is_valid_regex


def main(pattern: str,
         base_paths:list=None,
         excluded_subdirectories:tuple= ('.git', '.idea'),
         excluded_extensions:list=None,
         included_extensions:list=None,
         pattern_is_regex=True):
	"""

	:param pattern: A string to search for.  Could be a regex pattern or not, based on pattern_is_regex
	:param base_paths: A list of paths to walk (that is:  Look at every file within).  If not specified, cwd is assumed
	:param excluded_subdirectories: A list of subdirectories (as returned by os.path.basepath, without parent paths) to exclude.  Like '.git'
		It can contain both files and directories
	:param excluded_extensions: A list of file extensions to ignore
	:param included_extensions: A list of file extensions to include
	:param pattern_is_regex: A flag that tells us wheter to treat the pattern argument as a regex or not.
		Default is true
	:return:  #TODO:  What are we actually returning here?  Fill out the type hint as well
	"""

	"""
	Handle pattern
	"""
	if pattern_is_regex is True:
		if not is_valid_regex(test_value=pattern):
			raise ValueError(f"The value [{pattern}] cannot be compiled as a regex!")
		pattern = str(pattern)
	else:
		pattern = str(pattern)

	"""
	Handle base paths
	"""
	# if it's falsy, default to a list with cwd in it
	if not base_paths:
		base_paths = [os.getcwd()]

	# Make sure that each of the base paths exists
	for p in base_paths:
		if not os.path.isdir(p) and not os.path.isfile(p):
			raise FileNotFoundError(f"'{p}' is not a directory or a file.  Please remove it from base_paths and try again.")

	"""
	Handle the excluded and included file extensions list.  Excluded supersedes included
	"""

	# Coerce falsy values to a list
	if not included_extensions:
		included_extensions = []

	if not excluded_extensions:
		excluded_extensions = []

	# Ensure each element in each list is a string
	included_extensions = [str(ie) for ie in included_extensions.copy()]  #TODO:  Unit test this
	excluded_extensions = [str(ee) for ee in excluded_extensions.copy()]  #TODO:  Unit test this

	# Ensure that each element in each extension list starts with a dot.
	for lst in [included_extensions, excluded_extensions]:
		for item in lst.copy():
			if item == '':
				lst.remove(item)
				continue
			if not item.startswith('.'):
				lst.remove(item)
				lst.append(f".{item}")

	# We should only have an inclusion list or an exclusion list (or neither), but not both
	if len(included_extensions) >0 and len(excluded_extensions) >0:
		raise ValueError(f"Both the included_extensions and excluded_extensions arguments where supplied.  "
		                 f"Only one should be passed into the program.  Got:\n Included Extensions: {included_extensions}"
		                 f"\n Excluded Extensions:  {excluded_extensions}")


	"""
	Traverse the list of input paths and build a list of ALL files beneath that path.  
	We'll reduce it shortly based on the included or excluded extensions list
	"""
	all_files_beneath_paths = []
	for p in base_paths:
		if os.path.isfile(p):
			# Handle files
			if p not in all_files_beneath_paths:
				all_files_beneath_paths.append(p)
				print(f"Added the file '{p}' to the list of files to inspect.")
		elif os.path.isdir(p):

			print(f"Inspecting all files and folders beneath the path '{p}'")

			# Handle directories
			for dir_path, sub_dirs, files in os.walk(p):

				# Modify sub_dirs in-place to avoid paths we don't want to deal with (like .git).  See:  https://stackoverflow.com/questions/19859840/excluding-directories-in-os-walk
				sub_dirs_before_prune = sub_dirs.copy()
				sub_dirs[:] = [d for d in sub_dirs if d not in excluded_subdirectories]

				# Print what was just dropped off
				for d in sub_dirs_before_prune:
					if d not in sub_dirs:
						print(f"The subdirectory '{os.path.join(dir_path, d)}' was dropped because it matched one of "
						      f"the excluded subdirectories:  {excluded_subdirectories}", file=sys.stderr)

				# Append the fully qualified file path into the list
				for f in files:
					long_file_name = os.path.join(dir_path, f)

					if long_file_name not in all_files_beneath_paths:
						all_files_beneath_paths.append(long_file_name)

	# As a final step, if this program picked up this program, let's remove it
	this_program = __file__
	if this_program in all_files_beneath_paths:
		all_files_beneath_paths.remove(this_program)
		print(f"Removed this program, '{this_program}' from the list of files to inspect")


	"""
	Reduce the path of all files we collected above, to only those that match based on the white or black lists:
	"""
	files_to_inspect = []

	# Handle whitelisting
	if len(included_extensions) >0:
		for f in all_files_beneath_paths:
			ext = os.path.splitext(f)
			if ext in included_extensions:
				files_to_inspect.append(f)
	# Handle blacklisting
	elif len(excluded_extensions) >0:
		for f in all_files_beneath_paths:
			ext = os.path.splitext(f)
			if ext not in excluded_extensions:
				files_to_inspect.append(f)
	# If no whitelist or blacklist was specified, we'll use them all
	else:
		files_to_inspect = all_files_beneath_paths

	"""
	Remove files that are binary (That is: Not text).  No need to search those
	"""
	for f in reversed(files_to_inspect):
		# print(f"{f} is guess to be a file of type:  {mimetypes.guess_type(f)[1]}")
		print(f"{f} is guessed to be a file of type: {magic.from_file(f)}")




	pass  # You can put a breakpoint here when you're just getting started


if __name__ == '__main__':
	main(pattern=r'(wo)?m(a|e)n')


