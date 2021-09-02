.. _running-experiment:

.. currentmodule:: epyc

Running the experiment
----------------------

We can now run the entire experiment with one command:

.. code-block:: python

    lab.runExperiment(CurveExperiment())

What experiments will be run depends on the lab's :term:`experimental
design`.  By default labs use a :class:`FactorialDesign` that performs
an experiment for each combination of parameter values, which in this
case will have 250 points: 50 points along each axis.

Time will now pass until all the experiments are finished.

Where are the results? They've been stored into the notebook we
associated with the lab, either in-memory or in a JSON file on disk.
