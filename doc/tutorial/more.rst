.. _more-experiments:

.. currentmodule:: epyc

Running more experiments
------------------------

We can run more experiments from the same lab if we choose: simply
change the parameter bindings, as one would with a dict. It's also
possible to remove parameters as one would expect:

.. code-block::  python

   del lab['x']
   del lab['y]

For convenience there's also a method :meth:`Lab.deleteAllParameters`
that returns the lab to an empty parameter state, This can be useful
for using the same lab for multiple sets of experiments. If you're
going to do this, it's often advisable to use multiple result sets and
a more structured approach to notebooks, as described in the
:ref:`third-tutorial`.
