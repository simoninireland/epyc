#!/usr/bin/env python

# Setup for epyc
#
# Copyright (C) 2016 Simon Dobson
# 
# Licensed under GPL 2.0
#

from distutils.core import setup

setup(name = 'epyc',
      version = '0.1.0',
      description = 'Python computational experiment management',
      url = 'http://github.com/simoninireland/epyc',
      author = 'Simon Dobson',
      author_email = 'simon.dobson@computer.org',
      license = 'CC-BY-NC-SA',
      packages = [ 'epyc' ],
      requires = [ 'ipyparallel' ])

      
