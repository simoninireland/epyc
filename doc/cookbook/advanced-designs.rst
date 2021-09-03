.. _epyc-designs:

.. currentmodule:: epyc

Different experimental designs
------------------------------

**Problem**: The default behaviour of a :class:`Lab` is to run an
experiment at every combination of parameter points. You want to do
something different -- for example use specific combinations of
parameters only.

**Solution**: This is a problem of :term:`experimental design`: how
many experiments to run, and with what parameters?

`epyc` encapsulates experimental designs in the :class:`Design`
class. The default design is a :class:`FactorialDesign` that runs
experiments at every combination of points: essentially this design
forms the cross-product of all the possible values of all the
parameters, and runs an experiment at each. This is a sensible
default, but possibly too generous in some applications. You can
therefore sub-class :class:`Design` to implement other strategies.

In the specific case above, the :class:`SingletonDesign` performs the
necessary function. This design takes each parameter range and
combines the corresponding values, with any parameters with only a
single value in their range being extended to all experiments. (This
implies that all parameters are *either* singletons *or* have
ranges of the same size.)

We can create a lab that uses this design:

.. code-block:: python

   lab = Lab(design=epyc.SingletonDesign())
   lab['a'] = range(100)
   lab['b'] = range(100, 200)
   lab['c'] = 4

When an experiment is run under this design, it will generate 100
experimental runs (one per corresponding pair of elements of the
ranges of parameters 'a' and 'b', with 'c' being constantly 4) rather
than the 40,000 runs that a factorial design would generate under the
same conditions. Of course that's not a sensible comparison: the
singleton design doesn't explore the parameter space the way the
factorial design does.
