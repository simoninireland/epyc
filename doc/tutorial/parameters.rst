.. _parameters-experiment:

.. currentmodule:: epyc

Specifying the experimental parameters
--------------------------------------

We next need to specify the parameter space over which we want the lab to run the experiment. This
is done by mapping variables to values in a dict. The keys of the dict match the parameter values
references in the experiment; the values can be single values (constants) or ranges of values. The
lab will then run the the experiment for all combinations of the values provided.

For our purposes we want to run the experiment over a range :math:`[-2 \pi, 2 \pi]` in two axial directions.
We can deifne this using ``numpy``:

.. code-block :: python

    lab['x'] = numpy.linspace(-2 * numpy.pi, 2 * numpy.pi)
    lab['y'] = numpy.linspace(-2 * numpy.pi, 2 * numpy.pi)

How many points are created in these ranges? We've simply let ``numpy`` use its default, which is 50 points:
we could have specified a number if we wanted to , to get finer or coarser resolution for the point cloud.
Notice that the *lab itself* behaves as a dict for the parameters.

What experiments will the lab now run? We can check by retrieving the entire parameter space for the lab:

.. code-block :: python

    print(lab.parameterSpace())

This returns a list of the combinations of parameters that the lab will use for running experiments. If you're only
interested in how many experiments will run, you can get this with:

.. code-block : python

    print(len(lab))

