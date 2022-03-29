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


`-c [CONFIG_FILE], --config-file [CONFIG_FILE]` A complete path to a json config file where the keys would match the names of the arguments available to the main program. Arguments passed into the program via the CLI will supersede any found in the config file. This is useful for defining search parameters for common tasks. if not supplied, 'conf.json' is sought.

## Basic Examples
These are just some simple examples to convey the general idea.  See the help file (Invoke the program with the `-h` flag, or simply read above) for more advanced usage.


Given this regular expression example, `(big[\ ]?)?b[ei]r[td]([\ ]?man)?`, which would match strings (case-insensitive) like these:

`bert` `bird` `bigbird` `Big Bird` `birdman` `Bird Man`


### Search for matches under cwd that match the regex (nested), limited to just .txt files
`python3 word_crawl.py -p '(big[\ ]?)?b[ei]r[td]([\ ]?man)?' -i '.txt'`

#### Example Output
```
The main program was invoked with the following runtime arguments:
regex_pattern = (big[\ ]?)?b[ei]r[td]([\ ]?man)?
search_paths = None
excluded_extensions = None
included_extensions = ['.txt']
include_binary_files = False
print_json = False
escape_pattern = False
verbose = False
kwargs = {'config_file': None}
excluded_subdirectories = None
Files beneath these paths will be inspected if still based on arguments passed into this program:
	/Users/areese/projects/word_crawl
Found 1122 total files under base path(s).
Reduced the file list based on the extension whitelist (['.txt']).  There are 15 files to inspect.
Looking for files that seem to be binary.  These will be removed from the inspection list...
Removed 0 binary files from the inspection list.
There are 15 files left to inspect.
File Name = /Users/areese/projects/word_crawl/test_data/file2.txt	All Matches = 2	Unique Matches = 2	Matched Strings = ["bird man", "big bird man"]
File Name = /Users/areese/projects/word_crawl/test_data/file1.txt	All Matches = 6	Unique Matches = 6	Matched Strings = ["bert", "bird", "bigbird", "Big Bird", "birdman", "Bird Man"]
2 files out of 15 inspected files (0.13333333333333333) contained one or more match for the pattern '(big[\ ]?)?b[ei]r[td]([\ ]?man)?'
```

### For lovers of JSON
Simply append a `-j` flag.  Note the `BEGIN/END JSON Results` markers.  You can use these as anchor points for downstream consumers of this program to parse out JSON results only

`python3 ~/scripts/word_crawl.py -p '(big[\ ]?)?b[ei]r[td]([\ ]?man)?' -i '.txt' -j`

#### Example output

```
The main program was invoked with the following runtime arguments:
regex_pattern = (big[\ ]?)?b[ei]r[td]([\ ]?man)?
search_paths = None
excluded_extensions = None
included_extensions = ['.txt']
include_binary_files = False
print_json = True
escape_pattern = False
verbose = False
kwargs = {'config_file': None}
excluded_subdirectories = None
Files beneath these paths will be inspected if still based on arguments passed into this program:
	/Users/areese/projects/word_crawl
Found 1122 total files under base path(s).
Reduced the file list based on the extension whitelist (['.txt']).  There are 15 files to inspect.
Looking for files that seem to be binary.  These will be removed from the inspection list...
Removed 0 binary files from the inspection list.
There are 15 files left to inspect.
BEGIN JSON Results:
[
    {
        "file_name": "/Users/areese/projects/word_crawl/test_data/file2.txt",
        "pattern": "(big[\\ ]?)?b[ei]r[td]([\\ ]?man)?",
        "match_count": 2,
        "unique_match_count": 2,
        "matched_strings": [
            "bird man",
            "big bird man"
        ],
        "unique_matched_strings": [
            "bird man",
            "big bird man"
        ]
    },
    {
        "file_name": "/Users/areese/projects/word_crawl/test_data/file1.txt",
        "pattern": "(big[\\ ]?)?b[ei]r[td]([\\ ]?man)?",
        "match_count": 6,
        "unique_match_count": 6,
        "matched_strings": [
            "bert",
            "bird",
            "bigbird",
            "Big Bird",
            "birdman",
            "Bird Man"
        ],
        "unique_matched_strings": [
            "bert",
            "bird",
            "bigbird",
            "Big Bird",
            "birdman",
            "Bird Man"
        ]
    }
]
END JSON Results:
2 files out of 15 inspected files (0.13333333333333333) contained one or more match for the pattern '(big[\ ]?)?b[ei]r[td]([\ ]?man)?'
```



