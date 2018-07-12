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

``epyc`` also includes a small number of "experiment combinators" that
separate the logic of a single experiment from the logic of performing
multiple repetitions and other structuring tasks. This means that
any experiment can be repeated and statistically summarised, for
example.


Installation
------------

``epyc`` works with both Python 2.7 and Python 3. You can install it directly from PyPi using ``pip``:

::

   pip install epyc

The master distribution of ``epyc`` is hosted on GitHub. To obtain a
copy, just clone the repo:

::
   
    git clone git@github.com:simoninireland/epyc.git
    cd epyc
    python setup.py install


   
Documentation
-------------

API documentation for `epyc` can be found on `ReadTheDocs <https://epyc.readthedocs.io/en/latest/>`.
You can also read a Jupyter notebook describing several `epyc` use
cases online at <https://github.com/simoninireland/epyc/blob/master/doc/epyc.ipynb>.


Author and license
------------------

Copyright (c) 2016-2018, Simon Dobson <simon.dobson@computer.org>

Licensed under the `GNU General Public Licence v.2.0 <https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html>`.

