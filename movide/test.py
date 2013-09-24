from settings import *
import logging

BAD_LOGGER_NAMES = ['south', 'factory.containers', 'factory.generate']
bad_loggers = []
for bln in BAD_LOGGER_NAMES:
    logger = logging.getLogger(bln)
    logger.setLevel(logging.INFO)
    bad_loggers.append(bln)

# Nose Test Runner
INSTALLED_APPS += ('django_nose',)

NOSE_ARGS = ['--with-xunit', '--with-coverage',
              '--cover-package', 'api',
              '--cover-package', 'frontend',
              ]

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'