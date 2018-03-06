#!/usr/bin/env python

# Setup for epyc
#
# Copyright (C) 2016 Simon Dobson
# 
# Licensed under GPL 2.0
#

from setuptools import setup

with open('README.rst') as f:
    longDescription = f.read()

setup(name = 'epyc',
      version = '0.11.1',
      description = 'Python computational experiment management',
      long_description = longDescription,
      url = 'http://github.com/simoninireland/epyc',
      author = 'Simon Dobson',
      author_email = 'simon.dobson@computer.org',
      license = 'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
      classifiers = [ 'Development Status :: 4 - Beta',
                      'Intended Audience :: Science/Research',
                      'Intended Audience :: Developers',
                      'Programming Language :: Python :: 2.7',
                      'Topic :: Scientific/Engineering' ],
      packages = [ 'epyc' ],
      zip_safe = True,
      install_requires = [  ])


