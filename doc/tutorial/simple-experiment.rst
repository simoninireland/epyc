.. _simple-experiment:

.. currentmodule:: epyc

A simple experiment
-------------------

Computational experiments that justify using infrastructure like ``epyc`` are by definition
usually large and complicated -- and not suitable for a tutorial. So we'll start with a
very simple example: admittedly you could do this more easily witn straight Python code,
but that's an advantage when describing how to use a more complicated set-up.

So suppose we want to compute a set of values for some function so that we can plot
them as a graph. A complex function, or one that involved simulation, might justify
using ``epyc``. For the time being let's use a simple function:

.. math::

    z = sin \sqrt{x^2 + y^2}

We'll plot this function about :math:`(0, 0)` extending :math:`2 \pi` radians in each
axial direction.

