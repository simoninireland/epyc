# Initialisation for epyc package
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

"""`epyc` is a Python module for controlling a long-running series of
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
whose parameters and results are recorded as a :term:`result set` in a lab :term:`notebook`
for later retrieval. Laboratories can be sequential (for a single
machine) or parallel (to use a multicore or cluster of machines); lab
notebooks can be persistent to allow experiments to be fired-off and
their results retrieved later -- handy if you use a laptop. Notebooks
store all the data and metadata immutably in a portable format
(JSON or HDF5) to improve the reproducibility of computational experiments.

`epyc` also includes a small number of :term:`experiment combinators` that
separate the logic of a single experiment from the logic of performing
multiple repetitions and other structuring tasks. This means that any
experiment can be repeated and statistically summarised, for example.

"""

# String written into every persistent notebook file
PackageContactInfo = 'Created by epyc, computational experiment management for Python <https://pypi.org/project/epyc/>'

from .experiment import Experiment, ResultsDict
from .experimentcombinator import ExperimentCombinator
from .repeatedexperiment import RepeatedExperiment
from .summaryexperiment import SummaryExperiment

from .resultset import ResultSet, ResultSetLockedException, CancelledException, PendingResultException
from .labnotebook import LabNotebook, ResultsStructureException, NotebookVersionException, LabNotebookLockedException
from .jsonlabnotebook import JSONLabNotebook
from .hdf5labnotebook import HDF5LabNotebook

from .lab import Lab
from .parallellab import ParallelLab
from .clusterlab import ClusterLab

# Late and/or complex initialisation
Experiment._init_statics()
ResultSet._init_statics()


