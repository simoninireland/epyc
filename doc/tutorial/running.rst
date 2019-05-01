.. _running-experiment:

.. currentmodule:: epyc

Running the experiment
======================

We can now run the entire experiment with one command:

.. code-block:: python

    lab.runExperiment(CurveExperiment())

Time will now pass while the experiment is run on the 250 points in the parameter space: 50 points
along each axis, with the experiment being run with each possible pair of values for each parameter.

Where are the results? They've been stored into the notebook we associated with the lab, either
in-memory or in a JSON file on disk.


