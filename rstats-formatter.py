#!/usr/bin/env python

################################################################################
#                               rstats-formatter                               #
#                Formats and converts rstats bandwidth logfiles                #
#                               (C) 2016 Mischif                               #
#       Released under version 3.0 of the Non-Profit Open Source License       #
################################################################################

__version__ = "1.0.0"

import json
import gzip
import struct
import argparse
from datetime import date, timedelta
from functools import partial

class DayConv(argparse.Action):
	def __call__(self, parser, namespace, values, option_string=None):
		days = {"Mon":0, "Tue":1, "Wed":2, "Thu":3, "Fri":4, "Sat":5, "Sun":6}
		if values:
			if values not in days: raise argparse.ArgumentTypeError("Invalid start of week")
			setattr(namespace, self.dest, days[values])

class Logfile(object):

	factor = 1
	totals = {"day":{}, "monthly":{}}

	@staticmethod
	def to_date(num):
		year  = ((num >> 16) & 0xFF) + 1900
		month = ((num >>  8) & 0xFF) + 1
		day   = (num & 0xFF) or 1
		return date(year, month, day)

	def set_units(self, u):
		if u == "B": self.factor = 1
		if u == "KiB": self.factor = 2 ** 10
		if u == "MiB": self.factor = 2 ** 20
		if u == "GiB": self.factor = 2 ** 30
		if u == "TiB": self.factor = 2 ** 40
		self.u = u

	def set_week_start(self, s):
		self.ws = s

	def set_month_start(self, s):
		self.ms = s

	def __init__(self, path):
		self.u = ""
		self.ws = 0
		self.ms = 1

		try:
			with gzip.open(path) as f:
				version, = struct.unpack("<4s", f.read(4))
				if version not in ("RS00", "RS01"):
					raise argparse.ArgumentTypeError("File is not valid rstats logfile")

				f.seek(28, 1) # Skip 4 to QWORD-align, 24 for unused info storage?
				for _ in range(61): # Logs hold 61 data-days
					date, dl, ul = struct.unpack("<3Q", f.read(24))
					if not date: continue
					date = self.to_date(date)
					self.totals["day"][date] = (dl, ul)

				count, = struct.unpack("B", f.read(1))
				if len(self.totals["day"]) != count:
					raise argparse.ArgumentTypeError("File is not valid rstats logfile")

				f.seek(31, 1) # Skip 7 to QWORD-align, 24 for unused info storage?
				if version == "RS00":
					for _ in range(12): # Version 0 logs hold 12 data-months
						date, dl, ul = struct.unpack("<3Q", f.read(24))
						if not date: continue
						date = self.to_date(date)
						self.totals["monthly"][date] = (dl, ul)
				else:
					for _ in range(24): # Version 1 logs hold 24 data-months
						date, dl, ul = struct.unpack("<3Q", f.read(24))
						if not date: continue
						date = self.to_date(date)
						self.totals["monthly"][date] = (dl, ul)

				count, = struct.unpack("B", f.read(1))
				if len(self.totals["monthly"]) != count:
					raise argparse.ArgumentTypeError("File is not valid rstats logfile")

		except IOError as e:
			raise argparse.ArgumentTypeError(e.args[1])

	def print_totals(self, freqs):
		strings = {
			"B": "{0} - {1}: downloaded {2:12} {4}, uploaded {3:11} {4}",
			"KiB": "{0} - {1}: downloaded {2:9} {4}, uploaded {3:8} {4}",
			"MiB": "{0} - {1}: downloaded {2:6} {4}, uploaded {3:5} {4}",
			"GiB": "{0} - {1}: downloaded {2:3} {4}, uploaded {3:2} {4}",
			"TiB": "{0} - {1}: downloaded {2:3} {4}, uploaded {3:2} {4}"
			}

		headers = {
			"d": "{0}{1}{0}\n".format("-" * 34, "Daily Totals"),
			"w": "{0}{1}{0}\n".format("-" * 34, "Weekly Stats"),
			"m": "{0}{1}{0}\n".format("-" * 33, "Monthly Totals")
			}

		for freq in freqs:
			print headers[freq]
			if freq == "d":
				for d in sorted(self.totals["day"]):
					print strings[self.u][6:].format(None,
						d.strftime("%b %d"),
						self.totals["day"][d][0] / self.factor,
						self.totals["day"][d][1] / self.factor,
						self.u)
				print
			else:
				unsummed = []
				logs = sorted(self.totals["day"])
				start = logs[0]

				for day in logs:
					unsummed.append(self.totals["day"][day])

					if (freq == "w" and day.weekday() == (self.ws - 1) % 7) or \
							(freq == "m" and (day + timedelta(days = 1)).day == self.ms) or \
							day == logs[-1]:
						sum_dl = sum(t[0] for t in unsummed) / self.factor
						sum_ul = sum(t[1] for t in unsummed) / self.factor

						print strings[self.u].format(
							start.strftime("%b %d"), day.strftime("%b %d"), sum_dl, sum_ul, self.u)

						unsummed = []
						start = day + timedelta(days = 1)
				print

	def convert_totals(self, freqs, fmt, outfile):
		if fmt == "csv": out = "Start Year,Start Month,Start Day,End Year,End Month,End Day,Downloaded ({0}),Uploaded ({0})\n".format(self.u)
		else: out = ""

		if fmt == "json":
			di = {}
			if "d" in freqs: di["daily"] = []
			if "w" in freqs: di["weekly"] = []
			if "m" in freqs: di["monthly"] = []

		for freq in freqs:
			totals = []
			if freq == "d":
				for d in sorted(self.totals["day"]):
					totals.append((d, d,
						self.totals["day"][d][0] / self.factor,
						self.totals["day"][d][1] / self.factor))
			else:
				unsummed = []
				logs = sorted(self.totals["day"])
				start = logs[0]

				for day in logs:
					unsummed.append(self.totals["day"][day])

					if (freq == "w" and day.weekday() == (self.ws - 1) % 7) or \
							(freq == "m" and (day + timedelta(days = 1)).day == self.ms) or \
							day == logs[-1]:
						sum_dl = sum(t[0] for t in unsummed) / self.factor
						sum_ul = sum(t[1] for t in unsummed) / self.factor

						totals.append((start, day, sum_dl, sum_ul))

						unsummed = []
						start = day + timedelta(days = 1)

			if fmt == "csv":
				for t in totals: out += "{},{},{},{},{},{},{},{}\n".format(
					t[0].year, t[0].month, t[0].day,
					t[1].year, t[1].month, t[1].day,
					t[2], t[3])

			elif fmt == "json":
				target = None
				if freq == "d": target = di["daily"]
				if freq == "w": target = di["weekly"]
				if freq == "m": target = di["monthly"]
				for t in totals: target.append({
					"date_from": str(t[0]),
					"date_to": str(t[1]),
					"downloaded": t[2],
					"uploaded": t[3],
					"units": self.u})
				out = json.dumps(di, sort_keys = True)

		outfile.write(out)

if __name__ == "__main__":
	parser = argparse.ArgumentParser(
		prog = "rstats-formatter",
		description = "Formats and converts rstats bandwidth logfiles",
		epilog = "Released under NP-OSL v3.0, (C) 2016 Mischif")

	parser.add_argument("logfile",
		type = Logfile,
		help = "gzipped rstats logfile")

	parser.add_argument("--show-daily",
		const = "d",
		dest = "freqs",
		action = "append_const",
		help="Show daily statistics")

	parser.add_argument("--show-weekly",
		const = "w",
		dest = "freqs",
		action = "append_const",
		help="Show weekly statistics")

	parser.add_argument("--show-monthly",
		const = "m",
		dest = "freqs",
		action = "append_const",
		help="Show monthly statistics")

	parser.add_argument("-w", "--week-start",
		action = DayConv,
		default = 0,
		metavar = "{Mon - Sun}",
		choices = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
		help="Day statistics should reset")

	parser.add_argument("-m", "--month-start",
		type = int,
		default = 1,
		choices = xrange(1,32),
		metavar="{1 - 31}",
		help="Date statistics should reset")

	parser.add_argument("-u", "--units",
		default = "MiB",
		metavar = "{B - TiB}",
		choices = ["B", "KiB", "MiB", "GiB", "TiB"],
		help="Units statistics will be displayed in")

	parser.add_argument("-o", "--out",
		type = argparse.FileType('w'),
		dest = "outfile",
		metavar = "outfile.dat",
		help="File to write converted statistics to")

	parser.add_argument("-f", "--format",
		default = "csv",
		choices = ["csv", "json"],
		help="Format to convert statistics to")

	parser.add_argument("--convert-daily",
		const = "d",
		dest = "convs",
		action = "append_const",
		help="Include daily statistics in output file")

	parser.add_argument("--convert-weekly",
		const = "w",
		dest = "convs",
		action = "append_const",
		help="Include weekly statistics in output file")

	parser.add_argument("--convert-monthly",
		const = "m",
		dest = "convs",
		action = "append_const",
		help="Include monthly statistics in output file")

	parser.add_argument("--version",
		action = "version",
		version = "%(prog)s {}".format(__version__))

	args = parser.parse_args()
	args.logfile.set_units(args.units)
	args.logfile.set_week_start(args.week_start)
	args.logfile.set_month_start(args.month_start)

	if args.freqs: args.logfile.print_totals(args.freqs)
	if args.convs: args.logfile.convert_totals(args.convs, args.format, args.outfile)
