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


def main(regex_pattern: str,
         search_paths:list=None,
         excluded_subdirectories:list=['.git', '.idea'],
         excluded_extensions:list=None,
         included_extensions:list=None,
         include_binary_files:bool=False,
         collapse_whitespace:bool=True,
         print_json:bool=False,
         escape_pattern:bool=False,
         verbose=False,
         **kwargs) -> list :

	"""
	:param regex_pattern: A regex pattern to search for.  To search for a literal, set the escape_pattern arg to True.
	:param search_paths: A list of paths to walk (that is:  Look at every file within).  If not specified, cwd is assumed.
	:param excluded_subdirectories: A list of subdirectories (as returned by os.path.basename, without parent paths) to
		exclude.  Example: ['.git', '.idea']
	:param excluded_extensions: A list of file extensions to ignore, including the preceding dot '.' character
		Example: ['.log', '.tmp'].
		Note that the args excluded_extensions and included_extensions are mutually exclusive.
	:param included_extensions:   A list of file extensions to include, including the preceding dot '.' character
		Example: ['.csv', '.xml'].
		Note that the args excluded_extensions and included_extensions are mutually exclusive.
	:param include_binary_files: Set to True to search for patterns within files that appear to be binary.
		Under the hood, we're using the binaryornot library, which is imperfect but does a good job.
		According to its documentation, binaryornot errs on the side of false positives
		(That is, classifying a binary file as text)
	:param collapse_whitespace: Set to True to cause newline characters to be replaced by a single space, followed
		by multiple spaces, being collapsed into a single space.  This is useful to convert multi-line strings into
		a single line, which may make regex development a little simpler.
	:param print_json: Set to True to suppress standard messages printed to stdout in favor of a single JSON payload
		printed to stdout.  Keep in mind that other (non-JSON) messages might be printed as the program runs, but the
		clever programmer will leverage sed, awk, grep, jq, etc. to retrieve what is needed
	:param escape_pattern: Set to true to escape the regex_pattern, effectively coercing it into a string literal
		Under the hood, searches are still facilitated by using the re library, so that we can process capture groups
	:param verbose: Set to True to print more messages.  Set to False (Default) to print fewer messages.
	:return: A list of dictionaries that describe each match found
	"""


	"""
	Validate arguments
	"""

	prog_vars = vars().copy()
	print(f"The main program was invoked with the following runtime arguments:")
	for k in prog_vars.keys():
		v = prog_vars[k]
		print(f"{k} = {v}")

	# Coerce patterns made up of numbers only to string.
	if type(regex_pattern) in (int, float):
		regex_pattern = str(regex_pattern)

	# Validation #1 :  Regex pattern must be a non-null string
	if type(regex_pattern) is not str or regex_pattern == "":
		raise ValueError(f"The value for regex pattern must be a non-null string.  Got {type(regex_pattern)}")

	# Validation #2 :  list-like things must be a list (or tuple)
	for itm in prog_vars.keys():
		if itm not in [search_paths, excluded_subdirectories, excluded_extensions, included_extensions]:
			continue

		if itm is not None and type(itm) not in [list, tuple]:
			raise TypeError(f"The item {itm}, if supplied should be a list (or tuple).  Got {type(itm)}.  "
			                f"If passed from the command line, please use quoted, comma-separated values")


	# Validation #3:  Boolean things should be boolean:
	for itm in prog_vars.keys():
		if itm not in [include_binary_files, print_json, escape_pattern]:
			continue

		if itm is None:
			continue

		if type(itm) is not bool or str(itm) not in ["True", "False"]:
			raise TypeError(f"All boolean arguments should be either True or False.  Got {type(itm)} for the variable {itm}")

	# Validation #4:  included_extensions and excluded_extensions are mutually exclusive arguments.
	if included_extensions and excluded_extensions:
		raise ValueError(f"Both the included_extensions and excluded_extensions arguments where supplied.  "
		                 f"Only one should be passed into the program.  Got:\n Included Extensions: {included_extensions}"
		                 f"\n Excluded Extensions:  {excluded_extensions}")



	"""
	Handle pattern
	"""

	# Escape the regex pattern as applicable (To treat as a string literal)
	if escape_pattern is True:
		regex_pattern = re.escape(pattern=regex_pattern)
		print(f"The argument 'escape_pattern' was {escape_pattern}, therefore the pattern has been escaped.  The new "
		      f"value for the pattern is: {regex_pattern}")

	# Before we get too deep with the rest of the program, make sure that the regex will compile
	try:
		r = re.compile(pattern=regex_pattern)
	except Exception as ex:
		print(f"The input value [{regex_pattern}] cannot be compiled into a regex.  Please double check the syntax "
		      f"(Do you need to set escape_pattern to true?.  This can be done with the '-z' flag from the CLI)  "
		      f"Got exception:\n{ex}", file=sys.stderr)
		raise ex


	"""
	Handle search paths.  These can be a list of file names, or paths to search within or a mix of both
	"""

	# Default to cwd if not passed
	if not search_paths:
		search_paths = [os.getcwd()]

	# If just a string was passed, wrap it up in a list, so we can iterate over it later
	if type(search_paths) is str:
		search_paths = [search_paths]

	# Expand user to allow things like ~/Downloads to work correctly
	search_paths = [os.path.expanduser(str(p)) for p in search_paths]

	# Make sure that each of the base paths exists
	for p in search_paths:
		if not os.path.isdir(p) and not os.path.isfile(p):
			raise FileNotFoundError(f"'{p}' is not a directory or a file.  Please remove it from base_paths and try again.")

	"""
	Handle excluded_subdirectories
	"""
	if excluded_subdirectories is None:
		excluded_subdirectories = []

	if type(excluded_subdirectories) is not list:
		excluded_subdirectories = [excluded_subdirectories]


	"""
	Handle the excluded and included file extensions list.
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
		binary_files_removed = 0
		print(f"Looking for files that seem to be binary.  These will be removed from the inspection list...")

		for f in reversed(files_to_inspect):
			try:
				is_bin = is_binary(filename=f)

				if is_bin:
					if verbose:
						print(f"{f} seems to be a binary file.  It will be removed from the inspection list.", file=sys.stderr)

					files_to_inspect.remove(f)
					binary_files_removed += 1

			except FileNotFoundError as ex:
				if verbose:
					print(f"Encountered exception when trying to open the file '{f}'.  It probably doesn't exist anymore."
					      f"\n{ex}",file=sys.stderr)
				files_to_inspect.remove(f)

		print(f"Removed {binary_files_removed} binary files from the inspection list.")

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
		if verbose:
			print(f"Searching the file '{f}' for the pattern '{regex_pattern}'")

		try:
			with open(f, 'r') as f1:
				try:
					f_str = f1.read()
				except UnicodeDecodeError as ex:
					if verbose:
						print(f"Got UnicodeDecodeError when trying to read the file '{f}'. {ex}", file=sys.stderr)
					f1.close()
					continue
		except FileNotFoundError as ex1:
			print(f"Got FileNotFoundError when trying to read the file '{f}'.  It probably doesn't exist anymore.  {ex1}",
			      file=sys.stderr)

			continue

		# Collapse the whitespace as applicable
		if collapse_whitespace:
			if verbose is True:
				print(f"Collapsing whitespace...")
			orig_string = f_str
			f_str = re.sub(pattern="\n", repl=" ", string=f_str) # Replace newline with space
			f_str = re.sub(pattern="\s+", repl = " ", string=f_str) # Replace multiple whitespace (might be tabs) with single.

			if verbose is True:
				if orig_string == f_str:
					print(f"Performed Collapse Operations on the string, but the string was unchanged")
				else:
					print(f"Performed Collapse Operations on the string.  The old length of the string was {len(orig_string)}.  "
					      f"The new length of the string is {len(f_str)}")


		# Handling for regex vs simple string searches
		results = re.finditer(pattern=regex, string=f_str)


		# Process the match results
		if results is None:
			if verbose:
				print(f"No Matches found in the file '{f}' for the pattern '{regex_pattern}")
		else:
			# There was a regex  match!

			# Make list of all matches and unique matches
			running_list = []
			unique_list = []

			for r in results:
				match = r.group(0)
				running_list.append(match)

				if match not in unique_list:
					unique_list.append(match)

			# Print a message about what we found (or don't and save it to print to JSON later)
			if len(running_list) >0:

				if print_json is False:
					print(f"File Name = {f}"
					      f"\tAll Matches = {len(running_list)}"
					      f"\tUnique Matches = {len(unique_list)}"
					      f"\tMatched Strings = {json.dumps(unique_list)}")

				# Assemble results and put them into the final payload object
				tmp = dict(file_name=f, pattern=regex_pattern, match_count=len(running_list),
				           unique_match_count=len(unique_list), matched_strings=running_list,
				           unique_matched_strings=unique_list)
				all_results.append(tmp)

			else:
				if verbose:
					print(f"There were 0 matches for the pattern '{regex_pattern}' in the file '{f}")

	# We now have the final payload to return and/or print
	ret_val = all_results

	# Print as JSON as applicable
	if print_json is True:
		print("BEGIN JSON Results:")
		print(json.dumps(ret_val, indent=4))
		print("END JSON Results:")

	# Final summary of all findings
	print(f"{len(all_results)} files out of {len(files_to_inspect)} inspected files ({len(all_results) / len(files_to_inspect)}) "
	      f"contained one or more match for the pattern '{regex_pattern}'")

	return ret_val


if __name__ == '__main__':
	program_description = "A python utility to search for a regex or string literal within one or more files or lists of" \
	                      " directories.  This is useful when you're not quite sure what you're looking for but you know" \
	                      " it's (probably / maybe) there.  There are lots of flags to influence what is included or " \
	                      "excluded, verbosity, and so on.  The best way to see the 'documentation' is to invoke the " \
	                      "program with the -h (help) flag like this:\n python3 word_crawl.py -h"
	argp = argparse.ArgumentParser(description=program_description)
	argp.add_argument('-p', '--regex-pattern', required=False, help="A regular expression to search for within files.  "
	                                                                "While it is not required to be passed in directly "
	                                                                "from the command line, it is required to be "
	                                                                "supplied one way or another (i.e. via a config file)."
	                                                                "  See corresponding argument.")

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

	argp.add_argument('-b', '--include-binary-files', required=False, action='store_true',
	                  help="If set to True, files that appear to be Binary (detection works well but is imperfect) will "
	                       "be included in the search.  Otherwise they'll be omitted")

	argp.add_argument('-j', '--print-json', required=False, action='store_true', help="If set to True, the results will be "
	                                                                            "printed as JSON along with other "
	                                                                            "printed messages.  A tool like sed can"
	                                                                            " be used to parse out only the JSON "
	                                                                            "result from stdout")

	argp.add_argument('-z', '--escape-pattern', required=False, action='store_true',
	                  help="If set to True, the regex pattern will be escaped, effectively making it a string literal "
	                       "to search for.  The python 're' library is still used under the hood so we can make use of "
	                       "capture groups")

	argp.add_argument('-v', '--verbose', required=False, action='store_true', help="If set to True, the program will be "
	                                                                               "more verbose.")

	argp.add_argument('-w', '--collapse-whitespace', required=False, action='store_true',
	                  help="If set to True, newline characters will be converted to spaces and repeating space "
	                       "characters will be replaced by a single space.  Use this flag to convert a multi-line string"
	                       " to a single line")

	argp.add_argument('-c', '--config-file', required=False, nargs='?', const='conf.json',
	                  help="A complete path to a json config file where the keys would match the names of the arguments "
	                       "available to the main program.  Arguments passed into the program via the CLI will supersede"
	                       " any found in the config file.  This is useful for defining search parameters for common tasks."
	                       " if not supplied, 'conf.json' is sought.")

	args = vars(argp.parse_args()) #Coerces the args Namespace object to a dictionary
	config_file = args.get('config_file')

	"""
	If the config file argument was passed inject those defaults into the args dict
	"""
	if config_file is not None:
		config_file = os.path.expanduser(config_file)

		# Validate that the config file actually exists
		if not os.path.isfile(config_file):
			raise FileNotFoundError(f"The config file '{config_file}' does not exist.  Please try again")

		# Read the config file as a json object
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
				      f"passed in (or defaulted via argparse) from the command line.  The CLI argument will supersede "
				      f"that which was ready from the config file", file=sys.stderr)

		# We require that the regex pattern be passed into the program one way or another (via CLI or conf file)
		# Although it is marked as optional when defined (to allow it to come from conf), ensure we have it at this point.
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
		search_paths = [s.strip() for s in search_paths]
		args['search_paths'] = search_paths

	# Handle excluded subdirectories
	excluded_subdirectories = args.get('excluded_subdirectories')
	if type(excluded_subdirectories) is str:
		excluded_subdirectories = excluded_subdirectories.split(',')
		excluded_subdirectories = [e.strip() for e in excluded_subdirectories]
		args['excluded_subdirectories'] = excluded_subdirectories


	# Handle excluded extensions
	excluded_extensions = args.get('excluded_extensions')
	if type(excluded_extensions) is str:
		excluded_extensions = excluded_extensions.split(',')
		excluded_extensions = [e.strip() for e in excluded_extensions]
		args['excluded_extensions'] = excluded_extensions

	# Handle included extensions
	included_extensions = args.get('included_extensions')
	if type(included_extensions) is str:
		included_extensions = included_extensions.split(',')
		included_extensions = [i.strip() for i in included_extensions]
		args['included_extensions'] = included_extensions

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

	# Handle escape_pattern
	escape_pattern = str(args.get('escape_pattern')).lower()
	if escape_pattern in truthy_things:
		escape_pattern = True
	else:
		escape_pattern = False
	args['escape_pattern'] = escape_pattern

	# Handle collapse_whitespace
	truthy_things = ['y', '1', 'true']
	collapse_whitespace = str(args.get('collapse_whitespace')).lower()
	if collapse_whitespace in truthy_things:
		collapse_whitespace = True
	else:
		collapse_whitespace = False
	args['collapse_whitespace'] = collapse_whitespace

	# Invoke the main program
	main(**args)


