# encoding: utf-8

################################################################################
#                               rstats-logreader                               #
#   Parse RStats logfiles, display bandwidth usage, convert to other formats   #
#                       (C) 2016, 2019-2020 Jeremy Brown                       #
#       Released under version 3.0 of the Non-Profit Open Source License       #
################################################################################

from io import open
from os.path import abspath, dirname, join
from setuptools import setup


package_root = abspath(dirname(__file__))
module_root = join(package_root, "rstats_logreader")

# Get the long description from the README file
with open(join(package_root, "README.md"), encoding="utf-8") as desc:
	long_description = desc.read()

# Get the package version
with open(join(module_root, "VERSION"), encoding="utf-8") as version_file:
	package_version = version_file.read().strip()


setup(
	name="rstats-logreader",

	version=package_version,

	packages=["rstats_logreader"],

	license="NPOSL-3.0",

	url="https://github.com/mischif/rstats-logreader",

	description="Read bandwidth logfiles in the RStats format and perform simple analysis/aggregation.",

	long_description=long_description,
	long_description_content_type="text/markdown",

	author="Jeremy Brown",
	author_email="mischif@users.noreply.github.com",

	python_requires=">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*, !=3.5.*, <4",

	package_data={"rstats_logreader": ["VERSION"]},

	setup_requires=["pytest-runner"],

	tests_require=["hypothesis", "hypothesis-pytest", "mock", "pytest", "pytest-cov"],

	extras_require={
		"test": ["codecov"],
		},

	entry_points={
		"console_scripts": ["rstats-reader=rstats_logreader.cli:main"],
		},

	classifiers=[
		"Development Status :: 5 - Production/Stable",

		"Environment :: Console",
		
		"Intended Audience :: Information Technology",

		"License :: OSI Approved :: Open Software License 3.0 (OSL-3.0)",

		"Operating System :: OS Independent",

		"Programming Language :: Python :: 2",
		"Programming Language :: Python :: 2.7",
		"Programming Language :: Python :: 3",
		"Programming Language :: Python :: 3.6",
		"Programming Language :: Python :: 3.7",
		"Programming Language :: Python :: 3.8",

		"Topic :: System :: Networking",
		"Topic :: System :: Networking :: Monitoring",
		],

	keywords="RStats",
	)
