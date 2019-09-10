# encoding: utf-8

################################################################################
#                               rstats-logreader                               #
#   Parse RStats logfiles, display bandwidth usage, convert to other formats   #
#                            (C) 2016, 2019 Mischif                            #
#       Released under version 3.0 of the Non-Profit Open Source License       #
################################################################################

from setuptools import setup
from os import path
from io import open

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, "README.md"), encoding="utf-8") as desc:
	long_description = desc.read()

# Get the package version
with open(path.join(here, 'VERSION'), encoding="utf-8") as version_file:
	package_version = version_file.read().strip()


setup(
	name="rstats-logreader",

	version=package_version,

	packages=["rstats_logreader"],

	license="NPOSL-3.0",

	url="https://github.com/mischif/rstats-logreader",

	description="RStats logfile reader that can convert bandwith data to other formats",

	long_description=long_description,
	long_description_content_type="text/markdown",

	author="Jeremy Brown",
	author_email="mischif@users.noreply.github.com",

	python_requires=">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, <4",

	data_files=[("", ["VERSION"])],

	setup_requires=["pytest-runner"],

	tests_require=["hypothesis", "hypothesis-pytest", "pytest", "pytest-cov"],

	extras_require={
		"test": ["codecov"],
		},

	classifiers=[
		"Development Status :: 5 - Production/Stable",

		"Operating System :: OS Independent",

		"License :: OSI Approved :: Open Software License 3.0 (OSL-3.0)",

		"Programming Language :: Python :: 2",
		"Programming Language :: Python :: 2.7",
		"Programming Language :: Python :: 3",
		"Programming Language :: Python :: 3.4",
		"Programming Language :: Python :: 3.5",
		"Programming Language :: Python :: 3.6",
		"Programming Language :: Python :: 3.7",
		],

	keywords="RStats",
	)
