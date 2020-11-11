.. _defining-experiment:

.. currentmodule:: epyc

Defining the experiment
-----------------------

We first create a class describing our experiment. We do this by extending
:class:`Experiment` and overriding :meth:`Experiment.do` to provide the code actually executed:

.. code-block :: python

    from epyc import Experiment, Lab, JSONLabNotebook
    import numpy

    class CurveExperiment(Experiment):

        def do(self, params):
            '''Compute the sin value from two parameters x and y, returning a dict
            containing a result key with the computed value.

            :param params: the parameters
            :returns: the result dict'''
            x = params['x']
            y = params['y']
            r = numpy.sin(numpy.sqrt(x**2 + y**2))
            return dict(result = r)

That's it: the code for the computational experiment, that will be executed at a point
diven by the provided parameters dict.