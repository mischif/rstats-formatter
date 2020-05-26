# encoding: utf-8

################################################################################
#                               rstats-logreader                               #
#   Parse RStats logfiles, display bandwidth usage, convert to other formats   #
#                       (C) 2016, 2019-2020 Jeremy Brown                       #
#       Released under version 3.0 of the Non-Profit Open Source License       #
################################################################################

from io import open
from os.path import abspath, dirname, join
from setuptools import find_packages, setup


package_root = abspath(dirname(__file__))

# Get the long description from the README file
with open(join(package_root, "README.md"), encoding="utf-8") as desc:
	long_description = desc.read()


setup(
	name="rstats-logreader",

	packages=find_packages(where="src"),

	package_dir={"": "src"},

	license="NPOSL-3.0",

	url="https://github.com/mischif/rstats-logreader",

	description="Read bandwidth logfiles in the RStats format and perform simple analysis/aggregation.",

	long_description=long_description,
	long_description_content_type="text/markdown",

	author="Jeremy Brown",
	author_email="mischif@users.noreply.github.com",

	python_requires="~=3.6",

	package_data={"rstats_logreader": ["VERSION"]},

	setup_requires=["pytest-runner", "setuptools_scm"],

	tests_require=["hypothesis", "hypothesis-pytest", "mock", "pytest", "pytest-cov"],

	zip_safe=False,
	
	keywords=["RStats", "logfile"],

	extras_require={
		"test": ["codecov"],
		},

	entry_points={
		"console_scripts": ["rstats-reader=rstats_logreader.cli:main"],
		},

	options={
		"aliases": {
			"test": "pytest",
			},

		"metadata": {
			"license_files": "LICENSE",
			},
		},

	classifiers=[
		"Development Status :: 5 - Production/Stable",

		"Environment :: Console",
		
		"Intended Audience :: Information Technology",

		"License :: OSI Approved :: Open Software License 3.0 (OSL-3.0)",

		"Operating System :: OS Independent",

		"Programming Language :: Python :: 3",
		"Programming Language :: Python :: 3.6",
		"Programming Language :: Python :: 3.7",
		"Programming Language :: Python :: 3.8",

		"Topic :: System :: Networking",
		"Topic :: System :: Networking :: Monitoring",
		],
	)
