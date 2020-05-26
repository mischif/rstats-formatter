# encoding: utf-8

################################################################################
#                               rstats-logreader                               #
#   Parse RStats logfiles, display bandwidth usage, convert to other formats   #
#                       (C) 2016, 2019-2020 Jeremy Brown                       #
#       Released under version 3.0 of the Non-Profit Open Source License       #
################################################################################

from __future__ import print_function

from argparse import ArgumentParser, ArgumentTypeError, Namespace
from sys import argv

from rstats_logreader import __version__
from rstats_logreader.reader import RStatsParser

def parse_args(arg_list):
	"""
	Read arguments from stdin while validating and performing any necessary conversions

	:returns: (Namespace) Tool arguments
	"""
	args = None

	def norm_resolution(inp):
		resolutions = {"d": "daily", "w": "weekly", "m": "monthly"}

		if inp:
			if any(res not in resolutions for res in inp):
				raise ArgumentTypeError("Invalid resolution for logs")

			return Namespace(**{v: k in inp for (k, v) in resolutions.items()})


	def norm_day(day):
		days = {"Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4, "Sat": 5, "Sun": 6}

		if day:
			return days[day]


	main_parser = ArgumentParser(
		prog="rstats-reader",
		description="Displays statistics in RStats logfiles, with optional conversion",
		epilog="Released under NPOSL-3.0, (C) 2016, 2019 Mischif",
		)

	main_parser.add_argument("logpath",
		type=str,
		help="gzipped rstats logfile",
		)

	main_parser.add_argument("--print",
		type=norm_resolution,
		dest="print_freq",
		metavar="{dwm}",
		help="Print daily, weekly or monthly statistics to the console",
		)

	main_parser.add_argument("-w", "--week-start",
		type=norm_day,
		default="Mon",
		metavar="{Mon - Sun}",
		choices=range(7),
		help="Day of the week statistics should reset",
		)

	main_parser.add_argument("-m", "--month-start",
		type=int,
		default=1,
		choices=range(1,32),
		metavar="{1 - 31}",
		help="Day of the month statistics should reset",
		)

	main_parser.add_argument("-u", "--units",
		default="MiB",
		metavar="{B - TiB}",
		choices=["B", "KiB", "MiB", "GiB", "TiB"],
		help="Units statistics will be displayed in",
		)

	main_parser.add_argument("--version",
		action="version",
		version="%(prog)s {}".format(__version__),
		)

	write_group = main_parser.add_argument_group("write")

	write_group.add_argument("--write",
		type=norm_resolution,
		dest="write_freq",
		metavar="{dwm}",
		help="Write daily, weekly or monthly statistics to a file",
		)

	write_group.add_argument("-o", "--outfile",
		type = str,
		metavar = "outfile.dat",
		help="File to write statistics to",
		)

	write_group.add_argument("-f", "--format",
		default = "csv",
		choices = ["csv", "json"],
		help="Format to write statistics in",
		)

	args = main_parser.parse_args(arg_list)

	if getattr(args, "write_freq", False) and args.outfile is None:
		raise ArgumentTypeError("Missing output filename")

	return args


def main():
	"""
	Tool entry point
	"""
	args = parse_args(argv[1:])
	parser = RStatsParser(args.week_start, args.month_start, args.units)
	parser.parse_file(args.logpath)

	if args.print_freq:
		for line in parser.get_stats_for_console(**vars(args.print_freq)):
			print(line)

	if args.write_freq:
		parser.write_stats(args.outfile, args.format, **vars(args.write_freq))
