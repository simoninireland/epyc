---
title: 'epyc: Computational experiment management in Python'
tags:
  - Python
  - computational science
  - cluster computing
  - high-performance computing
  - automation
 authors:
  - name: Simon Dobson
    email: simoninireland@gmail.com
    orcid: 0000-0001-9633-2103
    affiliation: 1
 affiliations:
  - name: School of Computer Science, University of St Andrews, Scotland UK
    index: 1
 date: 25 february 2021
 ---
 
 # Summary
 
 ``epyc`` is a Python module for controlling long-running series of
computational experiments, as is often found when writing simulations
of complex networks and other such domains. In these applications,
there is often a need to perform a computation at a number of points
across a multi-dimensional parameter space, aggregating multiple
repetitions and wrangling results for analysis and presentation. Often
the experiments being performed are on such a scale as to require the
use of a computing cluster to perform multiple experiments
simultaneously.

Managing all these tasks is complicated, so ``epyc`` tries to automate
it. It provides a way to define a "laboratory" performing a collection
of "experiments" whose parameters and results are recorded in a "lab
notebook" for later retrieval. Laboratories can be sequential (for a
single machine) or parallel (to use a multicore or cluster of
machines); lab notebooks can be persistent to store the results of
experiments in a non-destructive form; and experiments on a cluster
can be performed asynchronously, fired-off and their results retrieved
later -- handy if you use a laptop. Notebooks store all the data and
metadata in a portable format to improve the reproducibility of
computational experiments. Results can be accessed through ``pandas``
DataFrames for easy wrangling and visualisation.

``epyc`` also includes a small number of "experiment combinators" that
separate the logic of a single experiment from the logic of performing
multiple repetitions and other structuring tasks. This means that any
experiment can be repeated and statistically summarised as a single
unit.

# Compatibility and availability

``epyc`` works with versions of Python from Python 3.5, and can be
installed directly from [PyPy](https://pypi.org/project/epyc/) using
``pip``. API and tutorial documentation can be found on
[ReadTheDocs](https://epyc.readthedocs.io/en/latest/).  Source code is
available on [GitHub](https://github.com/simoninireland/epyc), where
issues can also be reported.

