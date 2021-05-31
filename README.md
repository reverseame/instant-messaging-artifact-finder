# Instant Messaging Artifact Finder

Tool to find memory artifacts present in instant messaging applications.

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

## Installation

At the moment, the tool can be used as a command line tool. To do that, you can either clone the contents of
this repository or download the code. Additionally, in order for the tool to work, [Python 3](https://www.python.org/downloads/) has to be installed in the machine where the tool is going to be
used.

## Usage

In order to use the tool from the command line to extract the artifacts from a memory capture taken from a Telegram
Desktop process, execute the following command, where *memory_data_path* is the directory where the raw memory data files (.dmp
files) are stored:

```bash
python3 finder.py memory_data_path TELEGRAM_DESKTOP
```

By default, the tool generates a full report in JSON format, and a text file with a summary of the artifacts found. The
report format can be specified as an optional command line argument, as shown in the command below. However, right now, only
the JSON format is supported.

```bash
python3 finder.py memory_data_path TELEGRAM_DESKTOP --format JSON
```

Additionally, a temporary directory can be indicated. When supplied, the contents of the original memory data directory
are copied into that directory, after that, the tool works only with the contents present in the temporary directory, and,
finally, it removes the temporary directory. This can be useful for performance reasons if, for example, the temporary
directory is in a RAM disk. Here is an example of how to supply a temporary directory:

```bash
python3 finder.py memory_data_path TELEGRAM_DESKTOP --tmp temporary_directory_path
```

Note: In the above command, the temporary directory must not exist.

Lastly, for additional help, run the following
command:

```bash
python3 finder.py --help
```

## License

GNU General Public License v3.0