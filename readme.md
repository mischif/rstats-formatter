rstats-formatter
================

Displays rstats bandwidth logfiles created by routers running Tomato firmware in human-readable formats and supports conversion of data to CSV/JSON to use with other programs.

Released under version 3.0 of the Non-Profit Open Software License.

Usage
-----

# Simple Usage

Printing to screen:

    $ python rstats-formatter.py --show-daily --show-weekly --show-monthly

Printing to file:

    $ python rstats-formatter.py --convert-daily --convert-weekly --convert-monthly -o out.csv

# Advanced Usage

    $ python rstats-formatter.py -h

    usage: rstats-formatter [-h] [--show-daily] [--show-weekly] [--show-monthly]
                            [-w {Mon - Sun}] [-m {1 - 31}] [-u {B - TiB}]
                            [-o outfile.dat] [-f {csv,json}] [--convert-daily]
                            [--convert-weekly] [--convert-monthly] [--version]
                            logfile

    positional arguments:
      logfile               gzipped rstats logfile

    optional arguments:
      --show-daily                                  Show daily statistics
      --show-weekly                                 Show weekly statistics
      --show-monthly                                Show monthly statistics

      -w {Mon - Sun}, --week-start {Mon - Sun}      Day statistics should reset (default Mon)
      -m {1 - 31}, --month-start {1 - 31}           Date statistics should reset (default 1st)
      -u {B - TiB}, --units {B - TiB}               Units statistics will be displayed in (default MiB)

      -o outfile.dat, --out outfile.dat             File to write converted statistics to
      -f {csv,json}, --format {csv,json}            Format to convert statistics to (default csv)
      --convert-daily                               Include daily statistics in output file
      --convert-weekly                              Include weekly statistics in output file
      --convert-monthly                             Include monthly statistics in output file
      --version                                     show program's version number and exit
      -h, --help                                    show this help message and exit

Why?
----

Mostly I was bored. Also the rstats file was the easiest way to get some off-router record of bandwidth usage and the scripts that were already available didn't meet my needs.