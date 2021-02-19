#!/usr/bin/env python

# Setup for epyc
#
# Copyright (C) 2016--2020 Simon Dobson
#
# This file is part of epyc, experiment management in Python.
#
# epyc is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# epyc is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with epyc. If not, see <http://www.gnu.org/licenses/gpl.html>.

from setuptools import setup

with open('README.rst') as f:
    longDescription = f.read()

setup(name = 'epyc',
      version = '1.3.2',
      description = 'Python computational experiment management',
      long_description = longDescription,
      url = 'http://github.com/simoninireland/epyc',
      author = 'Simon Dobson',
      author_email = 'simon.dobson@computer.org',
      license = 'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
      classifiers = [ 'Development Status :: 4 - Beta',
                      'Intended Audience :: Science/Research',
                      'Intended Audience :: Developers',
                      'Programming Language :: Python :: 3.6',
                      'Programming Language :: Python :: 3.7',
                      'Programming Language :: Python :: 3.8',
                      'Programming Language :: Python :: 3.9',
                      'Topic :: Scientific/Engineering' ],
      python_requires = '>=3.5',
      packages = [ 'epyc' ],
      package_data = { 'epyc': [ 'py.typed' ] },
      zip_safe = False,
      install_requires = [ "numpy >= 1.17.5", "pyzmq", "ipyparallel >= 6.2.4", "cloudpickle", "pandas", "h5py", "joblib", "requests",  ],
      extra_requires = { ':python_version < 3.8': [ 'typing_extensions' ] },
)


