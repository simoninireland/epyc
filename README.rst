epyc: Python computational experiment management
================================================

Overview
--------

``epyc`` is a Python module for controlling a long-running series of
computational experiments, as is often found when writing simulations
of complex networks and other such domains. There is often a need to
perform a computation across a multi-dimensional parameter space,
varying the parameters, performing and aggregating multiple
repetitions, and wrangling results for analysis and
presentation. Often the experiments being performed are on such a
scale as to require the use of a computing cluster to perform multiple
experiments simultaneously.

Managing all these tasks is complicated, so ``epyc`` tries to automate
it. It provides a way to define a "laboratory" performing a collection
of "experiments" whose parameters and results are recorded in a "lab
notebook" for later retrieval. Laboratories can be sequential (for a
single machine) or parallel (to use a multicore or cluster of
machines); lab notebooks can be persistent to allow experiments to be
fired-off and their results retrieved later -- handy if you use a
laptop. Notebooks store all the data and metadata in a portable format
to improve the reproducibility of computational experiments. 


Source distribution
-------------------

``epyc`` is distributed on GitHub. To obtain a copy:

::
   
    git clone git@github.com:simoninireland/epyc.git
    cd epyc
    python setup.py install


Documentation
-------------

The ``doc/`` directory contains an IPython notebook that describes the
use of `epyc` in detail. You can also read it directly
`online <https://github.com/simoninireland/epyc/blob/master/doc/epyc.ipynb>`.


Author and license
------------------

Copyright (c) 2016, Simon Dobson <simon.dobson@computer.org>

Licensed under the `GNU General Public Licence v.2.0 <https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html>`.

