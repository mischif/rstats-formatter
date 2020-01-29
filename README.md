rstats-logreader
================

[![Travis](https://img.shields.io/travis/mischif/rstats-logreader.svg?style=for-the-badge)](https://travis-ci.org/mischif/rstats-logreader)
[![Codecov](https://img.shields.io/codecov/c/github/mischif/rstats-logreader.svg?style=for-the-badge)](https://codecov.io/gh/mischif/rstats-logreader)
[![Python Versions](https://img.shields.io/pypi/pyversions/rstats-logreader?style=for-the-badge)](https://pypi.org/project/rstats-logreader/)
[![Package Version](https://img.shields.io/pypi/v/rstats-logreader?style=for-the-badge)](https://pypi.org/project/rstats-logreader/)
[![License](https://img.shields.io/pypi/l/rstats-logreader?style=for-the-badge)](https://pypi.org/project/rstats-logreader/)

Read bandwidth logfiles in the RStats format (usually created by routers running some offshoot of the Tomato firmware) and perform simple analysis/aggregation.

Supports printing bandwidth data to the console, as well as conversion to CSV or JSON formats for further ingestion downstream.

Supports arbitrary week/month beginnings and conversion to arbitrary units.

Usage
-----

### Simple Usage

Printing to screen:

	$ rstats-reader --print dwm /path/to/logfile.gz

Saving to another format:

	$ rstats-reader --write dwm -f json -o out.json /path/to/logfile.gz

### All Options

	$ rstats-reader -h

	usage: rstats-reader [--print {dwm}] [-w {Mon - Sun}] [-m {1 - 31}]
			     [--write {dwm}] [-o outfile.dat] [-f {csv,json}]
			     [-u {B - TiB}] [-h] [--version]
			     logpath

	positional arguments:
		logpath				gzipped rstats logfile

	optional arguments:
		--print {dwm}			Print daily, weekly or monthly statistics to the console
		-w, --week-start {Mon - Sun}	Day of the week statistics should reset
		-m, --month-start {1 - 31}	Day of the month statistics should reset
		-u, --units {B - TiB}		Units statistics will be displayed in
		-h, --help			show this help message and exit
		--version			show program's version number and exit

	write:
		--write {dwm}			Write daily, weekly or monthly statistics to a file
		-o, --outfile outfile.dat	File to write statistics to
		-f, --format {csv,json}		Format to write statistics in
