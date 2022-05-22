#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2022 Adam.Dybbroe

# Author(s):

#   Adam.Dybbroe <a000680@c21856.ad.smhi.se>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Setup for the dr-schedule-and-coverage-tools package.
"""

from setuptools import setup, find_packages

try:
    # HACK: https://github.com/pypa/setuptools_scm/issues/190#issuecomment-351181286
    # Stop setuptools_scm from including all repository files
    import setuptools_scm.integration
    setuptools_scm.integration.find_files = lambda _: []
except ImportError:
    pass


description = ('Tools to analyse satellite direct reception schedules and conflicts,'
               'and calculate accumulated data coverage from schedules')

try:
    with open('./README.md', 'r') as fd:
        long_description = fd.read()
except IOError:
    long_description = ''

requires = ['docutils>=0.3', 'numpy>=1.5.1', 'scipy>=0.14',
            'matplotlib', 'pyorbital', 'pytroll-schedule',
            'requests',
            'pyyaml']

test_requires = ['pyyaml', 'pytest']

NAME = 'dr-schedule-and-coverage-tools'

setup(name=NAME,
      description=description,
      author='Adam Dybbroe',
      author_email='adam.dybbroe@smhi.se',
      classifiers=['Development Status :: 4 - Beta',
                   'Intended Audience :: Science/Research',
                   'License :: OSI Approved :: GNU General Public License v3 ' +
                   'or later (GPLv3+)',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'Topic :: Scientific/Engineering'],
      url='https://github.com/adybbroe/dr-schedule-and-coverage-tools',
      long_description=long_description,
      license='GPLv3',

      packages=find_packages(),
      # Project should use reStructuredText, so ensure that the docutils get
      # installed or upgraded on the target machine
      install_requires=requires,
      extras_require={'pyorbital': ['pyorbital'],
                      'trollsift': ['trollsift'],
                      'matplotlib': ['matplotlib'],
                      'pandas': ['pandas'],
                      'pytroll-schedule': ['pytroll-schedule'],
                      },
      scripts=['bin/create_list_of_possible_sat_receptions.py'],
      test_suite='pyspectral.tests.suite',
      tests_require=test_requires,
      python_requires='>=3.8',
      zip_safe=False,
      use_scm_version=True
      )
