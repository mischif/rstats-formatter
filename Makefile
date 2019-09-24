################################################################################
#                               rstats-logreader                               #
#   Parse RStats logfiles, display bandwidth usage, convert to other formats   #
#                            (C) 2016, 2019 Mischif                            #
#       Released under version 3.0 of the Non-Profit Open Source License       #
################################################################################

COV_OPTIONS="--cov=rstats_logreader --cov-report xml --cov-report term-missing --cov-config setup.cfg"

.PHONY: test ci-test build

clean:
	rm -rf rstats_logreader/VERSION .coverage coverage.xml .eggs/ .hypothesis/ .pytest_cache/ *egg-info/ dist/ build/
	find . -name __pycache__ -exec rm -rf {} +
	find . -name *.pyc -exec rm -rf {} +

test:
	python -B setup.py test

ci-test:
	HYPOTHESIS_PROFILE=ci python setup.py test --addopts ${COV_OPTIONS}

build:
	cp VERSION rstats_logreader/
	python setup.py build sdist bdist_wheel
