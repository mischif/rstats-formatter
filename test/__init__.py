# encoding: utf-8

################################################################################
#                               rstats-logreader                               #
#   Parse RStats logfiles, display bandwidth usage, convert to other formats   #
#                            (C) 2016, 2019 Mischif                            #
#       Released under version 3.0 of the Non-Profit Open Source License       #
################################################################################

from os import getenv

from hypothesis import HealthCheck, settings

settings.register_profile(u"ci",
						  database=None,
						  deadline=300,
						  max_examples=1000,
						  suppress_health_check=[HealthCheck.too_slow])

settings.load_profile(getenv(u"HYPOTHESIS_PROFILE", u"default"))
