epyc: Python computational experiment management
================================================

.. image:: https://badge.fury.io/py/epyc.svg
    :target: https://pypi.org/project/epyc/

.. image:: https://readthedocs.org/projects/epyc/badge/?version=latest
    :target: https://epyc.readthedocs.io/en/latest/index.html

.. image:: https://github.com/simoninireland/epyc/actions/workflows/ci.yaml/badge.svg
    :target: https://github.com/simoninireland/epyc/actions

.. image:: https://www.gnu.org/graphics/gplv3-88x31.png
    :target: https://www.gnu.org/licenses/gpl-3.0.en.html

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
of "experiments" whose parameters and results are collected togethr into "result
sets" and recorded in a "lab
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

``epyc`` works with Python 3.6 and above, and with PyPy3. You can install
it directly from PyPi using ``pip``:

::

   pip install epyc

The master distribution of ``epyc`` is hosted on GitHub. To obtain a
copy, just clone the repo:

::

    git clone git@github.com:simoninireland/epyc.git
    cd epyc
    pip install .


Examples
--------

See `the examples directory <https://github.com/simoninireland/epyc/tree/main/doc/examples>`_ for code examples.


Documentation
-------------

API documentation for ``epyc`` can be found on `ReadTheDocs <https://epyc.readthedocs.io/en/latest/>`_.
You can also read a Jupyter notebook describing several ``epyc`` use
cases online `here <https://github.com/simoninireland/epyc/blob/master/doc/epyc.ipynb>`_.


Author and license
------------------

Copyright (c) 2016-2021, Simon Dobson <simoninireland@gmail.com>

Licensed under the `GNU General Public Licence v3 <https://www.gnu.org/licenses/gpl-3.0.en.html>`_.
