# encoding: utf-8

################################################################################
#                               rstats-logreader                               #
#   Parse RStats logfiles, display bandwidth usage, convert to other formats   #
#                       (C) 2016, 2019-2020 Jeremy Brown                       #
#       Released under version 3.0 of the Non-Profit Open Source License       #
################################################################################

from __future__ import division

import gzip

from csv import DictReader
from datetime import date, timedelta
from json import load
from mock import patch
from struct import pack

import pytest

from hypothesis import assume, example, given
from hypothesis.strategies import booleans, composite, data, dates, integers, just, lists, none, one_of

from rstats_logreader.reader import RStatsParser as parser


def packed_date(date_to_pack):
	raw_year = date_to_pack.year % 1900
	raw_month = date_to_pack.month - 1
	raw_day = 0 if date_to_pack.day == 1 else date_to_pack.day

	return raw_year << 16 | raw_month << 8 | raw_day


def packed_raw_entry(date, download, upload):
	return pack("<3Q", packed_date(date), download, upload)


@composite
def log_date(draw):
	return draw(dates(min_value=date(1900, 1, 2), max_value=date(2155, 12, 31)))


@composite
def raw_entry_list(draw):
	result = []

	max_entries = draw(integers(min_value=1, max_value=60))
	start_date = draw(log_date())
	assume(start_date + timedelta(days=max_entries) <= date(2156, 1, 1))

	for d in range(max_entries):
		dl, ul = draw(lists(integers(min_value=0, max_value=2**64-1), min_size=2, max_size=2))
		result.append(parser.RawEntry(start_date + timedelta(days=d), dl, ul))

	return result


@pytest.mark.parametrize("factor, result", [
						 ("B", 2**0), ("KiB", 2**10), ("MiB", 2**20),
						 ("GiB", 2**30), ("TiB", 2**40), ("PiB", ValueError)],
						 ids=["B", "KiB", "MiB", "GiB", "TiB", "invalid"])
def test_get_factor(factor, result):
	if isinstance(result, int):
		assert parser._get_factor(factor) == result
	else:
		with pytest.raises(result):
			parser._get_factor(factor)


@given(log_date())
def test_to_date(test_date):
	assert parser._to_date(packed_date(test_date)) == test_date


@given(one_of(none(), log_date()), lists(integers(min_value=0, max_value=2**64-1), min_size=2, max_size=2))
def test_build_stat_entry(test_date, test_bw_values):
	dl, ul = test_bw_values

	if test_date is None:
		assert parser._build_stat_entry(packed_raw_entry(date(1900, 1, 1), dl, ul)) is None

	else:
		res = parser._build_stat_entry(packed_raw_entry(test_date, dl, ul))
		assert res.date == test_date
		assert res.download == dl
		assert res.upload == ul


@pytest.mark.parametrize("resolution", ["weekly", "monthly"], ids=["weekly-partition", "monthly-partition"])
@given(one_of(none(), log_date()), integers(min_value=0, max_value=60), integers(min_value=1, max_value=31), data())
def test_partition(resolution, start_date, entry_count, partition_start, data):
	log_entries = []

	if resolution == "weekly":
		partition_start %= 7

	if start_date is not None:
		for d in range(entry_count):
			dl, ul = data.draw(lists(integers(min_value=0, max_value=2**64-1), min_size=2, max_size=2))
			log_entries.append(parser.RawEntry(start_date + timedelta(days=d), dl, ul))

	if start_date is None:
		with pytest.raises(TypeError):
			parser._partition(log_entries, resolution)
	else:
		if resolution == "weekly":
			res = parser._partition(log_entries, resolution, week_start=partition_start)
			assert sum([len(part) for part in res]) == entry_count
			assert all([len(part) <= 7 for part in res])
			for part in res:
				if any([entry.date.weekday() == partition_start for entry in part]):
					assert sorted(part, key=lambda e: e.date)[0].date.weekday() == partition_start
		else:
			res = parser._partition(log_entries, resolution, month_start=partition_start)
			assert sum([len(part) for part in res]) == entry_count
			for part in res:
				if any([entry.date.day == partition_start for entry in part]):
					assert sorted(part, key=lambda e: e.date)[0].date.day == partition_start


@given(data(), integers(min_value=1, max_value=5), one_of(just(1), just(2**10), just(2**20)))
def test_aggregate_stats(data, partition_count, factor):
	partitions = []

	for _ in range(partition_count):
		partitions.append(data.draw(raw_entry_list()))

	if partition_count == 1:
		partitions = partitions[0]

	res = parser._aggregate_stats(partitions, factor)
	assert len(res) == len(partitions)

	if partition_count == 1:
		for i in range(len(res)):
			assert res[i].start == partitions[i].date
			assert res[i].end == partitions[i].date
			assert res[i].download == partitions[i].download / factor
			assert res[i].upload == partitions[i].upload / factor
	else:
		for i in range(len(res)):
			assert res[i].start == min(entry.date for entry in partitions[i])
			assert res[i].end == max(entry.date for entry in partitions[i])
			assert res[i].download == sum(entry.download for entry in partitions[i]) / factor
			assert res[i].upload == sum(entry.upload for entry in partitions[i]) / factor


@pytest.mark.parametrize("version, error", [["RS00", None], ["RS01", None],
											["RS02", "open"], ["RS02", "read"]],
						 ids=["version-1", "version-2", "open-error", "invalid-version"])
def test_get_logfile_version(tmpdir, version, error):
	log_path = str(tmpdir.join("test_log.gz"))

	with gzip.open(log_path, "wb") as f:
		f.write(pack("<4s", version.encode("utf-8")))

	if error is None:
		assert parser._get_logfile_version(log_path) == version
	elif error == "open":
		with pytest.raises(IOError):
			parser._get_logfile_version(str(tmpdir.join("nofile.gz")))
	elif error == "read":
		with pytest.raises(TypeError):
			parser._get_logfile_version(log_path)


@pytest.mark.parametrize("error", [None, "open", "check"], ids=["no-error", "open-error", "bad-check"])
@given(raw_entry_list())
@example(raw_entries=[])
def test_get_day_data(tmpdir, error, raw_entries):
	log_path = str(tmpdir.join("test_log.gz"))

	with gzip.open(log_path, "wb") as f:
		f.seek(32)

		for entry in raw_entries:
			f.write(packed_raw_entry(entry.date, entry.download, entry.upload))

		for _ in range(61 - len(raw_entries)):
			f.write(packed_raw_entry(date(1900, 1, 1), 0, 0))

		if error == "check":
			f.write(pack("B", (len(raw_entries) - 1) % 256))
		else:
			f.write(pack("B", len(raw_entries)))

	if error == "open":
		with pytest.raises(IOError):
			parser._get_day_data(str(tmpdir.join("nofile.gz")))
	elif error == "check":
		with pytest.raises(RuntimeError):
			parser._get_day_data(log_path)
	else:
		res = parser._get_day_data(log_path)
		assert sorted(raw_entries, key=lambda e: e.date) == sorted(res, key=lambda e: e.date)


@pytest.mark.parametrize("error", [None, "open", "check"], ids=["no-error", "open-error", "bad-check"])
@pytest.mark.parametrize("version", ["RS00", "RS01"], ids=["version-0", "version-1"])
@given(raw_entry_list())
@example(raw_entries=[])
def test_get_month_data(tmpdir, version, error, raw_entries):
	max_entries = 12 if version == "RS00" else 24
	raw_entries = raw_entries[:max_entries]

	log_path = str(tmpdir.join("test_log.gz"))

	with gzip.open(log_path, "wb") as f:
		f.seek(1528)

		for entry in raw_entries:
			f.write(packed_raw_entry(entry.date, entry.download, entry.upload))

		for _ in range(max_entries - len(raw_entries)):
			f.write(packed_raw_entry(date(1900, 1, 1), 0, 0))

		if error == "check":
			f.write(pack("B", (len(raw_entries) - 1) % 256))
		else:
			f.write(pack("B", len(raw_entries)))

	if error == "open":
		with pytest.raises(IOError):
			parser._get_month_data(str(tmpdir.join("nofile.gz")), version)
	elif error == "check":
		with pytest.raises(RuntimeError):
			parser._get_month_data(log_path, version)
	else:
		res = parser._get_month_data(log_path, version)
		assert sorted(raw_entries, key=lambda e: e.date) == sorted(res, key=lambda e: e.date)


@given(integers(min_value=0, max_value=6), integers(min_value=1, max_value=31),
	   one_of(just("B"), just("KiB"), just("MiB"), just("GiB"), just("TiB")))
def test_init(week_start, month_start, units):
	factors = {"B": 2 ** 0, "KiB": 2 ** 10, "MiB": 2 ** 20, "GiB": 2 ** 30, "TiB": 2 ** 40}

	p = parser(week_start, month_start, units)
	assert p.week_start == week_start
	assert p.month_start == month_start
	assert p.units == units
	assert p.factor == factors[units]


@patch.object(parser, "_get_logfile_version", return_value=0)
@patch.object(parser, "_get_day_data", return_value=["day_data"])
@patch.object(parser, "_get_month_data", return_value=["month_data"])
def test_parse_file(mock_month_data, mock_day_data, mock_logfile_version):
	p = parser(0, 1, "B")
	p.parse_file("/tmp/logfile.gz")
	assert p.logfile_version == 0
	assert p.day_data == ["day_data"]
	assert p.month_data == ["month_data"]


@given(one_of(just("B"), just("KiB")), booleans(), booleans(), booleans(), raw_entry_list())
def test_get_stats_for_console(units, write_daily, write_weekly, write_monthly, raw_entries):
	p = parser(0, 1, units)
	p.day_data = raw_entries
	res = p.get_stats_for_console(write_daily, write_weekly, write_monthly)

	if units == "B":
		daily_header = u"{0}:\t\t    {1:12.0f} {3} downloaded\t{2:12.0f} {3} uploaded"
		non_daily_header = u"{0} - {1}:    {2:12.0f} {4} downloaded\t{3:12.0f} {4} uploaded"
	else:
		daily_header = u"{0}:\t\t  {1:10.3f} {3} downloaded\t{2:10.3f} {3} uploaded"
		non_daily_header = u"{0} - {1}:  {2:10.3f} {4} downloaded\t{3:10.3f} {4} uploaded"

	if write_daily:
		daily_stats = p._aggregate_stats(raw_entries, p.factor)
		for stat in daily_stats:
			assert daily_header.format(stat.start, stat.download, stat.upload, units) in res

	if write_weekly:
		weekly_stats = p._aggregate_stats(p._partition(raw_entries, "weekly", week_start=p.week_start), p.factor)
		for stat in weekly_stats:
			assert non_daily_header.format(stat.start, stat.end, stat.download, stat.upload, units) in res

	if write_monthly:
		monthly_stats = p._aggregate_stats(p._partition(raw_entries, "monthly", month_start=p.month_start), p.factor)
		for stat in monthly_stats:
			assert non_daily_header.format(stat.start, stat.end, stat.download, stat.upload, units) in res


@pytest.mark.parametrize("out_format", ["csv", "json"])
@given(booleans(), booleans(), booleans(), raw_entry_list())
def test_write_stats(tmpdir, out_format, write_daily, write_weekly, write_monthly, raw_entries):
	outfile = str(tmpdir.join("out.{}".format(out_format)))
	p = parser(0, 1, "KiB")
	p.day_data = raw_entries
	p.write_stats(outfile, out_format, write_daily, write_weekly, write_monthly)

	if write_daily:
		daily_stats = p._aggregate_stats(raw_entries, p.factor)

	if write_weekly:
		weekly_stats = p._aggregate_stats(p._partition(raw_entries, "weekly", week_start=p.week_start), p.factor)

	if write_monthly:
		monthly_stats = p._aggregate_stats(p._partition(raw_entries, "monthly", month_start=p.month_start), p.factor)

	if out_format == "json":
		with open(outfile, "r") as f:
			dumped_stats = load(f)

		if write_daily:
			for stat in daily_stats:
				assert {"date_start": str(stat.start),
						"date_end": str(stat.start),
						"downloaded": stat.download,
						"uploaded": stat.upload,
						"units": p.units
						} in dumped_stats["daily"]

		if write_weekly:
			for stat in weekly_stats:
				assert {"date_start": str(stat.start),
						"date_end": str(stat.end),
						"downloaded": stat.download,
						"uploaded": stat.upload,
						"units": p.units
						} in dumped_stats["weekly"]

		if write_monthly:
			for stat in monthly_stats:
				assert {"date_start": str(stat.start),
						"date_end": str(stat.end),
						"downloaded": stat.download,
						"uploaded": stat.upload,
						"units": p.units
						} in dumped_stats["monthly"]

	elif out_format == "csv":
		with open(outfile, "r") as f:
			dumped_stats = list(DictReader(f))

		if write_daily:
			for stat in daily_stats:
				assert {"date_start": str(stat.start),
						"date_end": str(stat.start),
						"downloaded ({})".format(p.units): str(stat.download),
						"uploaded ({})".format(p.units): str(stat.upload)
						} in dumped_stats

		if write_weekly:
			for stat in weekly_stats:
				assert {"date_start": str(stat.start),
						"date_end": str(stat.end),
						"downloaded ({})".format(p.units): str(stat.download),
						"uploaded ({})".format(p.units): str(stat.upload)
						} in dumped_stats
		if write_monthly:
			for stat in monthly_stats:
				assert {"date_start": str(stat.start),
						"date_end": str(stat.end),
						"downloaded ({})".format(p.units): str(stat.download),
						"uploaded ({})".format(p.units): str(stat.upload)
						} in dumped_stats
