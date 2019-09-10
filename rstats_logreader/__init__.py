# encoding: utf-8

################################################################################
#                               rstats-logreader                               #
#   Parse RStats logfiles, display bandwidth usage, convert to other formats   #
#                            (C) 2016, 2019 Mischif                            #
#       Released under version 3.0 of the Non-Profit Open Source License       #
################################################################################

from io import open
from os.path import abspath, dirname, join

module_root = dirname(abspath(__file__))
package_root = dirname(module_root)

with open(join(package_root, 'VERSION'), encoding="utf-8") as version_file:
	__version__ = version_file.read().strip()
