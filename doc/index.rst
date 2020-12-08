.. epyc documentation master file, created by
   sphinx-quickstart on Sat Jul 28 14:37:14 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

epyc: Computational experiment management in Python
===================================================

Vision: Automated, repeatable management of computational experiments
---------------------------------------------------------------------

``epyc`` aims to simplify the process of conducting large-scale computational experiments.


What is ``epyc``?
------------------

``epyc`` is a Python module that conducts computational experiments. An experiment is simply a Python object that is
passed a tuple of parameters which is uses to perform some computation (typically a simulation) and return a tuple of
results. ``epyc`` allows a single experiment to be conducted across a space of parameters in a single command,
configuring and running the experiment at each point in the parameter space. The results are collected together into
a notebook along with the parameters for each result and some metadata about the performamnce of the experiment. Notebooks
are immutable, can be persistent, and can be imported into ``pandas`` for analysis.

``epyc`` can run the same experiment sequentially on a single local machine, in parallel on a multicore machine,
or in parallel on a distributed compute cluster of many machines. This allows simulations to be scaled-out with
minimal re-writing of code. Moreover jobs running on compute servers don't require the submitting machine to remain
connected, meaning one can work from a laptop, start a simulation, and come back later to collect the results. Results
can be collected piecemeal, to fully support disconnected operation.


Current features
----------------

* Single-class definition of experiments

* Run experiments across an arbitrarily-dimensioned parameter space with a single command

* Experiment combinators to control repetition and summarisation, separate from the core
  logic of an experiment

* Immutable storage of results

* Experiments can run locally, remotely, and in parallel

* Works with Python 3.5 and later, and with PyPy3

* Remote simulation jobs run asynchronously

* Start and walk away from remote simulations, collect results as they become available

* Fully integrated with ``ipython`` and ``ipyparallel`` for parallel and distributed simulation

* Fully compatible with ``jupyter`` notebooks and labs

* Annotated with ``typing`` type annotations

.. toctree ::
   :hidden:

   install
   tutorial
   reference
   cookbook
   glossary


