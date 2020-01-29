# encoding: utf-8

################################################################################
#                               rstats-logreader                               #
#   Parse RStats logfiles, display bandwidth usage, convert to other formats   #
#                       (C) 2016, 2019-2020 Jeremy Brown                       #
#       Released under version 3.0 of the Non-Profit Open Source License       #
################################################################################

from __future__ import print_function

from argparse import ArgumentError, ArgumentParser, ArgumentTypeError, Namespace, SUPPRESS
from mock import patch

import pytest

from hypothesis import given
from hypothesis.strategies import booleans, integers, just, none, one_of

from rstats_logreader.cli import main, parse_args
from rstats_logreader.reader import RStatsParser as parser


# Gotta monkeypatch this function so it doesn't take the entire test run down with it
def patched_parse_known_args(self, args=None, namespace=None):
	# args default to the system args
	if args is None:
		args = _sys.argv[1:]

	# default Namespace built from parser defaults
	if namespace is None:
		namespace = Namespace()

	# add any action defaults that aren't present
	for action in self._actions:
		if action.dest is not SUPPRESS:
			if not hasattr(namespace, action.dest):
				if action.default is not SUPPRESS:
					setattr(namespace, action.dest, action.default)

	# add any parser defaults that aren't present
	for dest in self._defaults:
		if not hasattr(namespace, dest):
			setattr(namespace, dest, self._defaults[dest])

	# parse the arguments and exit if there are any errors
	try:
		return self._parse_known_args(args, namespace)
	except ArgumentError:
		raise

ArgumentParser.parse_known_args = patched_parse_known_args


@given(
	one_of(none(), just("B"), just("KiB"), just("MiB"), just("GiB"), just("TiB")),
	one_of(none(), just("Mon"), just("Tue"), just("Wed"), just("Thu"), just("Fri"), just("Sat"), just("Sun")),
	one_of(none(), integers(min_value=1, max_value=31)),
	booleans(), booleans(), booleans(), booleans(),
	one_of(none(), just("json"), just("csv")),
	booleans(), booleans(), booleans(),
	booleans()
	)
def test_parse_args(tmpdir, units, week_start, month_start,
					print_daily, print_weekly, print_monthly, print_yearly,
					out_format, write_daily, write_weekly, write_monthly,
					has_outfile):

	days = {"Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4, "Sat": 5, "Sun": 6}
	args_list = []

	if out_format is not None:
		args_list.extend(["-f", out_format])

	if units is not None:
		args_list.extend(["-u", units])

	if week_start is not None:
		args_list.extend(["-w", week_start])

	if month_start is not None:
		args_list.extend(["-m", str(month_start)])

	if any([print_daily, print_weekly, print_monthly, print_yearly]):
		freqs = filter(lambda i: i[1], [("d", print_daily),
										("w", print_weekly),
										("m", print_monthly),
										("y", print_yearly)])
		freq_strings = "".join([f[0] for f in freqs])
		args_list.extend(["--print", freq_strings])

	if any([write_daily, write_weekly, write_monthly]):
		freqs = filter(lambda i: i[1], [("d", write_daily),
										("w", write_weekly),
										("m", write_monthly)])
		freq_strings = "".join([f[0] for f in freqs])
		args_list.extend(["--write", freq_strings])

	if has_outfile:
		args_list.extend(["-o", str(tmpdir.join("outfile"))])

	args_list.append(str(tmpdir.join("infile.gz")))

	if print_yearly:
		with pytest.raises(ArgumentError):
			parse_args(args_list)
	elif any([write_daily, write_weekly, write_monthly]) and not has_outfile:
		with pytest.raises(ArgumentTypeError):
			parse_args(args_list)
	else:
		parsed = parse_args(args_list)

		assert parsed.logpath == str(tmpdir.join("infile.gz"))
		assert parsed.format == (out_format or "csv")
		assert parsed.units == (units or "MiB")
		assert parsed.week_start == days.get(week_start, 0)
		assert parsed.month_start == (month_start or 1)

		if has_outfile:
			assert parsed.outfile == str(tmpdir.join("outfile"))

		if parsed.print_freq is not None:
			assert parsed.print_freq.daily == print_daily
			assert parsed.print_freq.weekly == print_weekly
			assert parsed.print_freq.monthly == print_monthly

		if parsed.write_freq is not None:
			assert parsed.write_freq.daily == write_daily
			assert parsed.write_freq.weekly == write_weekly
			assert parsed.write_freq.monthly == write_monthly


@patch.object(parser, "write_stats")
@patch.object(parser, "get_stats_for_console")
@patch.object(parser, "parse_file")
@patch("rstats_logreader.cli.print")
@patch("rstats_logreader.cli.parse_args")
def test_main(mock_parse_args, mock_print, mock_parse_file, mock_get_stats, mock_write_stats):
	mock_parse_args.return_value = Namespace(week_start=0, month_start=1, units="B", logpath="/tmp/stats.gz",
											 outfile="/tmp/out.csv", format="csv",
											 print_freq=Namespace(daily=True, weekly=False, monthly=False),
											 write_freq=Namespace(daily=True, weekly=False, monthly=False))
	mock_get_stats.return_value = ["test"]

	main()

	mock_parse_args.assert_called_once()
	mock_parse_file.assert_called_once()
	mock_get_stats.assert_called_once()
	mock_print.assert_called_once_with("test")
	mock_write_stats.assert_called_once()
