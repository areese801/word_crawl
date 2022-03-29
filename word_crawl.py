"""

# A program to traverse a directory and search for a specific word (regex pattern)

Originally written Adam Reese on Feb 15, 2022
areese801@gmail.com
"""
import argparse
import os
import re
import sys
import json
from binaryornot.check import is_binary
from word_crawl_helpers import is_valid_regex


def main(regex_pattern: str,
         search_paths:list=None,
         excluded_subdirectories:list= ['.git', '.idea'],
         excluded_extensions:list=None,
         included_extensions:list=None,
         include_binary_files:bool=False,
         print_json:bool=False,
         **kwargs) -> list :
	"""


	:param print_json: If set to True results will not be printed to stdout.  Instead, the final JSON payload will be printed
	:param regex_pattern: A regex pattern to search for.
	:param search_paths: A list of paths to walk (that is:  Look at every file within).  If not specified, cwd is assumed
		The list of files collected from these paths will be subsequently pruned based on the other arguments
	:param excluded_subdirectories: A list of subdirectories (as returned by os.path.basepath, without parent paths) to exclude.  Like '.git'
		It can contain both files and directories
	:param excluded_extensions: A list of file extensions to ignore
	:param included_extensions: A list of file extensions to include
	:param include_binary_files: If False, binary files (as per binaryornot library, which is imperfect) are removed from the search list
	:return list:  A list of dictionaries that describe each match
	"""

	#TODO:  Clean up all print messages.f

	"""
	Handle pattern
	"""
	regex_pattern = str(regex_pattern)
	if not is_valid_regex(test_value=regex_pattern):
		raise ValueError(f"The value [{regex_pattern}] cannot be compiled as a regex!")

	"""
	Handle base paths
	"""

	# Default to cwd if not passed
	if not search_paths:
		search_paths = [os.getcwd()]

	# If just a string was passed, wrap it up in a list
	if type(search_paths) is str:
		search_paths = [search_paths]

	# Expand user to allow things like ~/Downloads to work correctly
	search_paths = [os.path.expanduser(p) for p in search_paths]

	# Make sure that each of the base paths exists
	for p in search_paths:
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
	included_extensions = [str(ie) for ie in included_extensions.copy()]
	excluded_extensions = [str(ee) for ee in excluded_extensions.copy()]

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
	We'll reduce it shortly based on the included or excluded extensions list and other arguments
	"""

	# Announce where we'll be working
	print(f"Files beneath these paths will be inspected if still based on arguments passed into this program:")
	for p in search_paths:
		if os.path.isdir(p):
			print(f"\t{p}")

	# Walk each path, adding each file (including those in subdirectories) to the all files list
	all_files_beneath_paths = []
	for p in search_paths:
		if os.path.isfile(p):

			# Handle files
			if p not in all_files_beneath_paths:
				all_files_beneath_paths.append(p)

		elif os.path.isdir(p):

			# Handle directories
			for dir_path, sub_dirs, files in os.walk(p):

				# Modify sub_dirs in-place to avoid paths we don't want to deal with (like .git).
				# See:  https://stackoverflow.com/questions/19859840/excluding-directories-in-os-walk
				sub_dirs_before_prune = sub_dirs.copy()
				sub_dirs[:] = [d for d in sub_dirs if d not in excluded_subdirectories]

				# Print the names of the subdirectories that we just dropped out of the list
				for d in sub_dirs_before_prune:
					if d not in sub_dirs:
						print(f"The subdirectory '{os.path.join(dir_path, d)}' was dropped because it matched one of "
						      f"the excluded subdirectories:  {excluded_subdirectories}", file=sys.stderr)

				# Concatenate, and append the fully qualified file path into the list
				for f in files:
					long_file_name = os.path.join(dir_path, f)

					if long_file_name not in all_files_beneath_paths:
						all_files_beneath_paths.append(long_file_name)


	"""
	Reduce the path of all files we collected above, to only those that match based on the white or black lists:
	"""
	print(f"Found {len(all_files_beneath_paths)} total files under base path(s).")
	files_to_inspect = []

	# Handle whitelisting
	if len(included_extensions) >0:
		for f in all_files_beneath_paths:
			ext = os.path.splitext(f)[-1]
			if ext in included_extensions:
				files_to_inspect.append(f)

		print(f"Reduced the file list based on the extension whitelist ({str(included_extensions)}).  "
		      f"There are {len(files_to_inspect)} files to inspect.")

	# Handle blacklisting
	elif len(excluded_extensions) >0:
		for f in all_files_beneath_paths:
			ext = os.path.splitext(f)[-1]
			if ext not in excluded_extensions:
				files_to_inspect.append(f)

		print(f"Reduced the file list based on the extension blacklist ({str(excluded_extensions)}).  "
		      f"There are {len(files_to_inspect)} files to inspect.")

	# If no whitelist or blacklist was specified, we'll use them all
	else:
		files_to_inspect = all_files_beneath_paths
		print(f"There was no extension whitelist or blacklist passed into the program.  All files will be inspected.")

	"""
	Remove binary files, as applicable
	"""

	if include_binary_files is False:
		print(f"Looking for files that seem to be binary.  These will be removed from the inspection list...")
		for f in reversed(files_to_inspect):
			try:
				is_bin = is_binary(filename=f)

				if is_bin:
					print(f"{f} seems to be a binary file.  It will be removed from the inspection list.", file=sys.stderr)
					files_to_inspect.remove(f)

			except FileNotFoundError as ex:
				print(f"Encountered exception when trying to open the file '{f}'.  It probably doesn't exist anymore.\n{ex}",
				      file=sys.stderr)
				files_to_inspect.remove(f)
	else:
		print(f"All remaining files, including those that appear to be binary will be inspected")

	"""
	At last, we have a list of files we feel are worth inspecting
	"""
	print(f"There are {len(files_to_inspect)} files left to inspect.")

	# Compile regex
	regex = re.compile(pattern=regex_pattern, flags=re.IGNORECASE)

	all_results = [] # We'll append into this

	for f in files_to_inspect:
		# print(f"Searching the file '{f}' for the pattern '{pattern}'", file=sys.stderr)

		try:
			with open(f, 'r') as f1:
				try:
					f_str = f1.read()
				except UnicodeDecodeError as ex:
					print(f"Got UnicodeDecodeError when trying to read the file '{f}'. {ex}", file=sys.stderr)
					f1.close()
					continue
		except FileNotFoundError as ex1:
			print(f"Got FileNotFoundError when trying to read the file '{f}'.  It probably doesn't exist anymore.  {ex1}",
			      file=sys.stderr)

			continue

		# Handling for regex vs simple string searches
		results = re.finditer(pattern=regex, string=f_str)


		# Process the match results
		if results is None:
			print(f"No Matches found in the file '{f}' for the pattern '{regex_pattern}", file=sys.stderr)
		else:
			# There was a regex  match!
			running_list = []
			unique_list = []

			for r in results:
				match = r.group(0)
				running_list.append(match)

				if match not in unique_list:
					unique_list.append(match)

			if len(running_list) >0:
				# print(f"There were {len(running_list)} matches, {len(unique_list)} of which were unique for the "
				#       f"pattern '{pattern}' in the file '{f}'.  Unique Matches: {str(unique_list)}")
				#

				if print_json is False:
					print(f"File Name = {f}"
					      f"\tAll Matches = {len(running_list)}"
					      f"\tUnique Matches = {len(unique_list)}"
					      f"\tMatched Strings = {json.dumps(unique_list)}")

				# Assemble results
				tmp = dict(file_name=f, pattern=regex_pattern, match_count=len(running_list),
				           unique_match_count=len(unique_list), matched_strings=running_list,
				           unique_matched_strings=unique_list)
				all_results.append(tmp)

			else:
				# print(f"There were 0 matches for the pattern '{pattern}' in the file '{f}", file=sys.stderr)
				pass

	ret_val = all_results

	# Print as JSON as applicable
	if print_json is True:
		print("BEGIN JSON Results:")
		print(json.dumps(ret_val, indent=4))
		print("END JSON Results:")

	# Final report
	print(f"{len(all_results)} files out of {len(files_to_inspect)} inspected files ({len(all_results) / len(files_to_inspect)}) "
	      f"contained one or more match for the pattern '{regex_pattern}'")

	return ret_val


if __name__ == '__main__':
	argp = argparse.ArgumentParser()
	argp.add_argument('-p', '--regex-pattern', required=False, help="A regular expression to search for within files.")
	argp.add_argument('-s', '--search-paths', required=False, help="A path or comma-separated list of paths to search "
	                                                               "within for the pattern.")
	argp.add_argument('-x', '--excluded-subdirectories', required=False, help="A comma-separated list of short "
	                                                                          "subdirectory names that if found should "
	                                                                          "be skipped over (e.g. '.git')")

	# Handle excluded_extensions and included_extensions, which are mutually exclusive
	grp = argp.add_mutually_exclusive_group()
	grp.add_argument('-e', '--excluded-extensions', required=False, help="A comma-separated list of extensions that if "
	                                                                     "found, should be skipped over "
	                                                                     "(e.g. '.pdf, .log')")
	grp.add_argument('-i', '--included-extensions', required=False, help="A comma-separated list of extensions should be"
	                                                                     " subject to search (e.g. '.json, .csv').  All "
	                                                                     "others will be ignored")

	argp.add_argument('-b', '--include-binary-files', required=False, help="If set to True, files that appear to be "
	                                                                       "Binary (detection works well but is "
	                                                                       "imperfect) will be included in the search.  "
	                                                                       "Otherwise they'll be omitted")

	argp.add_argument('-j', '--json', required=False, help="If set to True, the results will be printed as JSON along "
	                                                       "with other printed messages.  A tool like sed can be used to"
	                                                       " parse out only the JSON result from stdout")

	argp.add_argument('-c', '--config-file', required=False, help="A complete path to a json config file where the keys "
	                                                              "would match the names of the arguments available to "
	                                                              "the main program.  Arguments passed into the program "
	                                                              "via the CLI will supersede any found int he config "
	                                                              "file.  This is useful for defining search parameters "
	                                                              "for common tasks")

	args = vars(argp.parse_args()) #Coerces the args Namespace object to a dictionary
	config_file = args.get('config_file')

	# if the config file argument was passed inject those defaults into the args dict
	if config_file is not None:
		config_file = os.path.expanduser(config_file)

		# Validate that it exists
		if not os.path.isfile(config_file):
			raise FileNotFoundError(f"The config file '{config_file}' does not exist.  Please try again")

		# Read it
		with open(config_file, 'r') as f:
			s = f.read()
			j = json.loads(s)

		# For any key in the config that is not already set in arguments, add it in
		for k in j.keys():
			v = j[k]

			# See if the key is already in the args object
			v1 = args.get(k)

			if v1 is None:
				args[k] = v
				print(f"Set the argument for '{k}' to the value '{v}', read from the config file '{config_file}'")
			else:
				print(f"The key '{k}' was read from the config file, '{config_file}', but the same argument was already "
				      f"passed in from the command line.  The CLI argument will supersede that which was ready from the "
				      f"config file", file=sys.stderr)

		# We require that the regex pattern be passed into the program one way or another (via CLI or conf file)
		# Although it is marked as optional when defined (to allow it to come from conf), ensure we have it now
		if args.get('regex_pattern') is None:
			raise ValueError(f"The argument 'regex pattern' is required, however it was not supplied via the CLI or via "
			                 f"the configuration file argument")

		"""
		Coerce comma-delimited strings from the CLI into iterables expected by the main program
		"""

		# Handle search paths
		search_paths = args.get('search_paths')
		if type(search_paths) is str:
			search_paths = search_paths.split(',')
			args['search_paths'] = search_paths

		# Handle excluded subdirectories
		excluded_subdirectories = args.get('excluded_subdirectories')
		if type(excluded_subdirectories) is str:
			excluded_subdirectories = excluded_subdirectories.split(',')
			args['excluded_subdirectories'] = excluded_subdirectories

		# Handle excluded extensions
		excluded_extension = args.get('excluded_extension')
		if type(excluded_extension) is str:
			excluded_extension = excluded_extension.split(',')
			args['excluded_extension'] = excluded_extension

		# Handle included extensions
		included_extension = args.get('included_extension')
		if type(included_extension) is str:
			included_extension = included_extension.split(',')
			args['included_extension'] = included_extension

		# Handle include binary flag
		truthy_things = ['y', '1', 'true']
		include_binary_files = str(args.get('include_binary_files')).lower()
		if include_binary_files in truthy_things:
			include_binary_files = True
		else:
			include_binary_files = False
		args['include_binary_files'] = include_binary_files

		# Handle print_json
		truthy_things = ['y', '1', 'true']
		print_json = str(args.get('print_json')).lower()
		if print_json in truthy_things:
			print_json = True
		else:
			print_json = False
		args['print_json'] = print_json

		# Invoke the main program
		ret_val = main(**args)

		return ret_val  #TODO:  Pick back up here






	print("!")


	# reg_pattern = r'(big)?\ *(BIRD|maN)'
	# main(pattern=reg_pattern, base_paths=['/Users/areese/projects/word_crawl/test_data', '~/Downloads'], included_extensions=['.txt', '.json'], print_json=True)
	# main(pattern=reg_pattern, base_paths=['/Users/areese/projects/word_crawl/test_data', '~/Downloads'])



