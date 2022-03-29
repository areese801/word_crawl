# word_crawl.py


## Description
word_crawl is a Python3 utility to search for a regex or string literal within one or more files or lists of directories. This is useful when you're not quite sure what you're looking for but you know it's (probably /
maybe) there. There are lots of flags to influence what is included or excluded, verbosity, and so on. The best way to see the documentation is to invoke the program with the -h (help) flag like this:

`python3 word_crawl.py -h`



## Requirements
The python library binaryornot is used under the hood to make determinations (which are good, but imperfect) about which files are, well, Binary or Not.  

Here are some pages to help with the install and documentation. You'll probably have to jump through some DLL hoops as well if you're a Windows user.  
* [PyPi](https://pypi.org/project/binaryornot/)
* [ReadTheDocs](https://binaryornot.readthedocs.io/en/latest/)
* [GitHub](https://github.com/audreyfeldroy/binaryornot)
* TL;DR `pip3 install binaryornot`


## Usage


usage: word_crawl.py [-h] [-p REGEX_PATTERN] [-s SEARCH_PATHS] [-x EXCLUDED_SUBDIRECTORIES] [-e EXCLUDED_EXTENSIONS | -i INCLUDED_EXTENSIONS] [-b] [-j] [-z] [-v] [-c [CONFIG_FILE]]


optional arguments:

`-h, --help`            

Show this help message and exit

`-p REGEX_PATTERN, --regex-pattern REGEX_PATTERN`

A regular expression to search for within files. While it is not required to be passed in directly from the command line, it is required to be supplied one way or another (i.e. via a
                        config file). See corresponding argument.


`-s SEARCH_PATHS, --search-paths SEARCH_PATHS`

A path or comma-separated list of paths to search within for the pattern.


`-x EXCLUDED_SUBDIRECTORIES, --excluded-subdirectories EXCLUDED_SUBDIRECTORIES`

A comma-separated list of short subdirectory names that if found should be skipped over (e.g. '.git')
  

`-e EXCLUDED_EXTENSIONS, --excluded-extensions EXCLUDED_EXTENSIONS`

A comma-separated list of extensions that if found, should be skipped over (e.g. '.pdf, .log')


`-i INCLUDED_EXTENSIONS, --included-extensions INCLUDED_EXTENSIONS`

A comma-separated list of extensions should be subject to search (e.g. '.json, .csv'). All others will be ignored
  
`-b, --include-binary-files`

If set to True, files that appear to be Binary (detection works well but is imperfect) will be included in the search. Otherwise they'll be omitted.


`-j, --print-json`

If set to True, the results will be printed as JSON along with other printed messages. A tool like sed can be used to parse out only the JSON result from stdout.


`-z, --escape-pattern`  

If set to True, the regex pattern will be escaped, effectively making it a string literal to search for. The python 're' library is still used under the hood so we can make use of
                        capture groups.

`-v, --verbose`

If set to True, the program will be more verbose.


`-c [CONFIG_FILE], --config-file [CONFIG_FILE]` A complete path to a json config file where the keys would match the names of the arguments available to the main program. Arguments passed into the program via the CLI will supersede any found int he config file. This is useful for defining search parameters for common tasks. if not supplied, 'conf.json' is sought.

