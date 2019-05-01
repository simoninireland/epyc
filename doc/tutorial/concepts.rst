.. currentmodule:: epyc

Concepts
--------

``epyc`` is built around three core concepts: experiments, labs, and notebooks.

An **experiment** is just an object inheriting from the :class:`Experiment` class. An experiment can contain
pretty much any code you like, which is then called according to a strict protocol (described in detail
in :ref:`lifecycle`). The most important thing about experiments is that they can be parameterisedwith a set
oif parameters passed to your code as a dict.

Parameters can come directly from calling code if the experiment is called directly, but it is more common for
experiments to be invoked from a **lab**. A lab defines a parameter space, a collection of parameters whose values
are each taken from a range. The set of all possible combinations of parameter values forms a multi-dimensional space,
and the lab runs an experiment for each point in that space (each combination of values). This allows the same
experiment to be done across a whole range of parameters with a single command. Different lab implementations provide
simple local sequential execution of experiments, parallel execution on a multicore machine, or parallel and
distributed execution on a compute cluster or in the cloud. The same experiment can usually be performed in any
lab, with ``epyc`` taking care of all the house-keeping needed. This makes it easy to scale-out experiments
over larger parameter spaces or numbers of repetitions.

Running the experiment produces results, which are stored in a **notebook**. Notebooks are immutable: once results have
been entered, they can't be modified or discarded. Notebooks can also be persistent, for example storing their results
in JSON for easy access from other tools. They can also return their results as a ``pandas`` dataframe for later
analysis.
