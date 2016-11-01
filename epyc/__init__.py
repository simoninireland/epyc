# Initialisation for epyc package
#
# Copyright (C) 2016 Simon Dobson
#
# Licensed under the GNU General Public Licence v.2.0
#

'''`epyc` is a Python module for controlling a long-running series of
computational experiments, as is often found when writing simulations
of complex networks and other such domains. There is often a need to
perform a computation across a multi-dimensional parameter space,
varying the parameters, performing and aggregating multiple
repetitions, and wrangling results for analysis and
presentation. Often the experiments being performed are on such a
scale as to require the use of a computing cluster to perform multiple
experiments simultaneously.

Managing all these tasks is complicated, so `epyc` tries to automate
the process. It provides a way to define a :term:`lab` that performs
an :term:`experiment` (or, more likely, a sequence of experiments)
whose parameters and results are recorded in a lab :term:`notebook`
for later retrieval. Laboratories can be sequential (for a single
machine) or parallel (to use a multicore or cluster of machines); lab
notebooks can be persistent to allow experiments to be fired-off and
their results retrieved later - handy if you use a laptop. Notebooks
store all the data and metadata immutably in a portable format to
improve the reproducibility of computational experiments.

`epyc` also includes a small number of :term:`experiment combinators` that
separate the logic of a single experiment from the logic of performing
multiple repetitions and other structuring tasks. This means that any
experiment can be repeated and statistically summarised, for example.

'''

from .experiment import Experiment
from .experimentcombinator import ExperimentCombinator
from .repeatedexperiment import RepeatedExperiment
from .summaryexperiment import SummaryExperiment

from .lab import Lab
from .clusterlab import ClusterLab

from .labnotebook import LabNotebook
from .jsonlabnotebook import JSONLabNotebook
#from .sqlitelabnotebook import SqliteLabNotebook


