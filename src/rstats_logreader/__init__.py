# encoding: utf-8

################################################################################
#                               rstats-logreader                               #
#   Parse RStats logfiles, display bandwidth usage, convert to other formats   #
#                       (C) 2016, 2019-2020 Jeremy Brown                       #
#       Released under version 3.0 of the Non-Profit Open Source License       #
################################################################################

from io import open
from os.path import abspath, dirname, join

module_root = dirname(abspath(__file__))

with open(join(module_root, "VERSION"), encoding="utf-8") as version_file:
	__version__ = version_file.read().strip()
