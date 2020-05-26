# encoding: utf-8

################################################################################
#                               rstats-logreader                               #
#   Parse RStats logfiles, display bandwidth usage, convert to other formats   #
#                       (C) 2016, 2019-2020 Jeremy Brown                       #
#       Released under version 3.0 of the Non-Profit Open Source License       #
################################################################################

from __future__ import division

import gzip

from collections import namedtuple
from csv import DictWriter
from datetime import date
from json import dumps
from struct import unpack


class RStatsParser(object):
	RawEntry = namedtuple("_raw_entry", ["date", "download", "upload"])
	AggregateStat = namedtuple("_aggregate_stat", ["start", "end", "download", "upload"])

	@staticmethod
	def _get_factor(unit):
		"""
		Determine how much to divide the raw values from the logfile by

		:param unit: (str) Unit abbreviation of desired factor

		:returns: (int) numerical factor of unit
		"""
		factors = {"B": 2 ** 0, "KiB": 2 ** 10, "MiB": 2 ** 20, "GiB": 2 ** 30, "TiB": 2 ** 40}

		try:
			return factors[unit]
		except KeyError:
			raise ValueError("Invalid Factor")

	@staticmethod
	def _to_date(num):
		"""
		Convert a packed date value from the logfile into a Date object

		:param num: (int) Packed date value

		:returns: (Date) Date from logfile
		"""
		year  = ((num >> 16) & 0xFF) + 1900
		month = ((num >>  8) & 0xFF) + 1
		day   = (num & 0xFF) or 1
		return date(year, month, day)

	@staticmethod
	def _build_stat_entry(raw_entry):
		"""
		Convert a raw logfile entry into a helper object more suitable for later manipulation

		:param raw_entry: (str) Packed tuple containing upload/download values on date

		:returns: (RawEntry) Helper object containing upload/download values on date
		"""
		result = None

		date, dl, ul = unpack("<3Q", raw_entry)

		if date:
			date = RStatsParser._to_date(date)
			result = RStatsParser.RawEntry(date, dl, ul)

		return result

	@staticmethod
	def _get_logfile_version(path):
		"""
		Retrieve the version of the logfile being parsed for later use

		:param path: (str) Path to logfile

		:returns: Version of logfile at given location
		"""
		version = None

		try:
			with gzip.open(path, "rb") as f:

				version = unpack("<4s", f.read(4))[0].decode("utf-8")
				if version not in (u"RS00", u"RS01"):
					raise TypeError("File is not valid rstats logfile")
		except:
			raise
		else:
			return version

	@staticmethod
	def _get_day_data(path):
		"""
		Retrieve bandwidth data for individual days from the given logfile

		:param path: (str) Path to logfile

		:returns: (list) RawEntry objects containing bandwidth data for their associated days
		"""
		stats = []

		try:
			with gzip.open(path, "rb") as f:
				f.seek(32)

				# Logs hold 61 data-days
				for _ in range(61):
					entry = RStatsParser._build_stat_entry(f.read(24))

					if entry is None:
						continue

					stats.append(entry)

				count, = unpack("B", f.read(1))
				if len(stats) != count:
					raise RuntimeError("Log day data is corrupted")
		except:
			raise
		else:
			return stats

	@staticmethod
	def _get_month_data(path, version):
		"""
		Retrieve bandwidth data for individual months from the given logfile

		:param path: (str) Path to logfile
		:param version: (str) RStats version of logfile

		:returns: (list) RawEntry objects containing bandwidth data for their associated months
		"""
		# RS00 logs hold 12 data-months, RS01 logs hold 24 data-months
		entries = {"RS00": 12, "RS01": 24}
		stats = []

		try:
			with gzip.open(path, "rb") as f:
				f.seek(1528)

				for _ in range(entries[version]):
					entry = RStatsParser._build_stat_entry(f.read(24))

					if entry is None:
						continue

					stats.append(entry)

				count, = unpack("B", f.read(1))
				if len(stats) != count:
					raise RuntimeError("Log month data is corrupted")
		except:
			raise
		else:
			return stats

	@staticmethod
	def _partition(entries, resolution, week_start=None, month_start=None):
		"""
		Group bandwidth data by the given resolution according to the specified group boundary

		:param entries: (list) Individual bandwith entries
		:param resolution: (str) Switch for splitting by week/month
		:param week_start: (int) If using weekly resolution,
								 the day of the week where groups begin
		:param month_start: (int) If using monthly resolution,
								  the day of the month where groups begin
		"""
		result = []
		current = []

		if resolution == "weekly":
			if week_start is None:
				raise TypeError("Missing week_start")

			for entry in entries:
				stat_date = entry.date

				if stat_date.weekday() == week_start:
					result.append(current)
					current = []

				current.append(entry)

		elif resolution == "monthly":
			if month_start is None:
				raise TypeError("Missing month_start")

			for entry in entries:
				stat_date = entry.date

				if stat_date.day == month_start:
					result.append(current)
					current = []

				current.append(entry)

		if len(current):
				result.append(current)

		return [l for l in result if len(l)]

	@staticmethod
	def _aggregate_stats(partitions, factor):
		"""
		Combine all raw bandwidth entries in each group into an aggregate

		:param partitions: (list) RawEntry objects when calculating daily statistics,
								  RawEntry lists when calculating weekly/monthly statistics
		:param factor: (int) Factor to divide raw numbers by to get results in desired units

		:returns: (list) AggregateStat objects containing the aggregate values of the given groups,
		"""
		result = []

		# Parse daily stats
		if isinstance(partitions[0], RStatsParser.RawEntry):
			for entry in partitions:
				date = entry.date
				download = entry.download / factor
				upload = entry.upload / factor
				result.append(RStatsParser.AggregateStat(date, date, download, upload))

		# Parse weekly/monthly stats
		else:
			for part in partitions:
				start = min(entry.date for entry in part)
				end = max(entry.date for entry in part)
				download = sum(entry.download for entry in part) / factor
				upload = sum(entry.upload for entry in part) / factor
				result.append(RStatsParser.AggregateStat(start, end, download, upload))

		return result

	def __init__(self, week_start, month_start, units):
		self.week_start = week_start
		self.month_start = month_start
		self.units = units
		self.factor = self._get_factor(units)
		self.day_data = []
		self.month_data = []

	def parse_file(self, logpath):
		"""
		Parse the given logfile and store its values in the object

		:param logpath: (str) The path to the logfile
		"""
		# RStats log format:
		# First four bytes are magic string that indicate version
		# Next four bytes are empty, presumably for QWORD alignment
		# Next 24 bytes are empty, for future usage?
		# Next are 61 3-tuples for day-level stats,
		# contains date, download and upload totals (8 byte/value)
		# Next is one-byte counter that should match actual number of previous 3-tuples
		# Next seven bytes are empty, presumably for QWORD alignment
		# Next 24 bytes are empty, again for future usage?
		# Next are 12 3-tuples for month-level stats,
		# contains date, download and upload totals (8 byte/value)
		# Version 1 logfiles hold another 12 month-level stat entries
		# Last is one-byte counter that should match actual number of previous 3-tuples
		self.logfile_version = self._get_logfile_version(logpath)
		self.day_data = self._get_day_data(logpath)
		self.month_data = self._get_month_data(logpath, self.logfile_version)

	def get_stats_for_console(self, daily, weekly, monthly):
		"""
		Generate the desired statistics from the logfile, formatted as desired,
		to be later printed to the console.

		:param daily: (bool) Print daily stats to the console
		:param weekly: (bool) Print weekly stats to the console
		:param monthly: (bool) Print monthly stats to the console

		:returns: (list) Statistics to be printed to the console
		"""
		stat_lines = []

		if self.units == "B":
			daily_header = u"{0}:\t\t    {1:12.0f} {3} downloaded\t{2:12.0f} {3} uploaded"
			non_daily_header = u"{0} - {1}:    {2:12.0f} {4} downloaded\t{3:12.0f} {4} uploaded"
		else:
			daily_header = u"{0}:\t\t  {1:10.3f} {3} downloaded\t{2:10.3f} {3} uploaded"
			non_daily_header = u"{0} - {1}:  {2:10.3f} {4} downloaded\t{3:10.3f} {4} uploaded"


		if daily:
			stat_lines.append(u"{:-^80}".format("Daily Bandwidth Usage"))

			for stat in self._aggregate_stats(self.day_data, self.factor):
				stat_lines.append(daily_header.format(stat.start, stat.download, stat.upload, self.units))
			stat_lines.append("")

		if weekly:
			stat_lines.append(u"{:-^80}".format("Weekly Bandwidth Usage"))

			partitions = self._partition(self.day_data, "weekly", week_start=self.week_start)
			for stat in self._aggregate_stats(partitions, self.factor):
				stat_lines.append(non_daily_header.format(stat.start, stat.end, stat.download, stat.upload, self.units))
			stat_lines.append("")

		if monthly:
			stat_lines.append(u"{:-^80}".format("Monthly Bandwidth Usage"))

			partitions = self._partition(self.day_data, "monthly", month_start=self.month_start)
			for stat in self._aggregate_stats(partitions, self.factor):
				stat_lines.append(non_daily_header.format(stat.start, stat.end, stat.download, stat.upload, self.units))
			stat_lines.append("")

		return stat_lines

	def write_stats(self, out_path, out_format, daily, weekly, monthly):
		"""
		Write the desired converted stats for the logfile to a file

		:param out_path: (str) Path to write the converted stats to
		:param out_format: (str) Format to write the converted stats in
		:param daily: (bool) Write daily stats to a file
		:param weekly: (bool) Write weekly stats to a file
		:param monthly: (bool) Write monthly stats to a file
		"""
		stats = {}

		if out_format == "json":
			if daily:
				stats["daily"] = [{
									"date_start": str(stat.start),
									"date_end": str(stat.start),
									"downloaded": stat.download,
									"uploaded": stat.upload,
									"units": self.units,
									} for stat in self._aggregate_stats(self.day_data, self.factor)]

			if weekly:
				partitions = self._partition(self.day_data, "weekly", week_start=self.week_start)
				stats["weekly"] = [{
									"date_start": str(stat.start),
									"date_end": str(stat.end),
									"downloaded": stat.download,
									"uploaded": stat.upload,
									"units": self.units,
									} for stat in self._aggregate_stats(partitions, self.factor)]

			if monthly:
				partitions = self._partition(self.day_data, "monthly", month_start=self.month_start)
				stats["monthly"] = [{
									"date_start": str(stat.start),
									"date_end": str(stat.end),
									"downloaded": stat.download,
									"uploaded": stat.upload,
									"units": self.units,
									} for stat in self._aggregate_stats(partitions, self.factor)]

			with open(out_path, "w") as outfile:
				outfile.write(dumps(stats))

		elif out_format == "csv":
			fields = ["date_start", "date_end", "downloaded ({})".format(self.units), "uploaded ({})".format(self.units)]

			if daily:
				stats["daily"] = [{
									"date_start": str(stat.start),
									"date_end": str(stat.start),
									"downloaded ({})".format(self.units): str(stat.download),
									"uploaded ({})".format(self.units): str(stat.upload),
									} for stat in self._aggregate_stats(self.day_data, self.factor)]

			if weekly:
				partitions = self._partition(self.day_data, "weekly", week_start=self.week_start)
				stats["weekly"] = [{
									"date_start": str(stat.start),
									"date_end": str(stat.end),
									"downloaded ({})".format(self.units): str(stat.download),
									"uploaded ({})".format(self.units): str(stat.upload),
									} for stat in self._aggregate_stats(partitions, self.factor)]

			if monthly:
				partitions = self._partition(self.day_data, "monthly", month_start=self.month_start)
				stats["monthly"] = [{
									"date_start": str(stat.start),
									"date_end": str(stat.end),
									"downloaded ({})".format(self.units): str(stat.download),
									"uploaded ({})".format(self.units): str(stat.upload),
									} for stat in self._aggregate_stats(partitions, self.factor)]
			
			with open(out_path, "w") as outfile:
				writer = DictWriter(outfile, fields)
				writer.writeheader()

				for stat_list in stats.values():
					writer.writerows(stat_list)
