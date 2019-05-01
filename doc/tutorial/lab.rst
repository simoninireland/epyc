.. _lab-experiment:

.. currentmodule:: epyc

A lab for the experiment
------------------------

To perform our experiment properly, we need to run the experiment at a *lot* of points,
to give use a "point cloud" dataset that we can then plot to see the shape of the function.
``epyc`` lets us define the space of parameters over which we want to run the experiment,
and then will automatically run and collect results.

The object that controls this process is a :class:`Lab`, which we'll create first:

.. code-block:: python

    lab = epyc.Lab()

This is the most basic use of labs, which will store the results in an in-memory :class:`LabNotebook`.
For more serious use, if we wanted to save the results for later, then we can create an persistent
notebook using JSON and store it in a file:

.. code-block:: python

    lab = epyc.Lab(notebook = epyc.JSONLabNotebook("sin.json",
                                                   create = True,
                                                   description = "A point cloud of $sin \sqrt{x^2 + y^2}$"))

