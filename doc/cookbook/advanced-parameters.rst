.. _epyc-parameters:

.. currentmodule:: epyc

Advanced experimental parameter handling
----------------------------------------

**Problem**: The parameters affecting your experiment come from a
range of sources, some only found at set-up time (or later).

**Solution**: Ideally everything you need to know to run an
experiment is know when the experiment is first configured, either
directly or from a :class:`Lab`. Sometimes this isn't the case,
though: it may be that, in setting up an experiment, you want to
record additional material about the experiment. You can do this in
three ways:

1. by adding to the :term:`metadata` of the experiment;
2. by adding to the :term:`experimental parameters`; or
3. by returning it as part of the :term:`experimental results`.

Which to choose? You can simply choose which makes most sense. These
three different set of values are intended to represent different
sorts of things: monitoring information, configuration information,
and computed information respectively. Generally speaking we expect
experiments to yield results (only). Sometimes it's also worth adding
(for example) timing information to the metadata.

Occasionally one might also want to extend the set of experimental
parameters -- because, for example, in the process of setting-up the
experiment according to the parameters given, additional information
comes about that's also pertinent to how the experiment was run. In
that case it's entirely legitimate to add to the experimental
parameters. You can do this simply by writing to the parameters passed
to :meth:`Experiment.setUp`:

.. code-block:: python

   def setUp(self, params):
      super().setUp(params)

      # do our setup
      ...

      # update the parameters
      params['variance'] = var

This change to the dict of experimental parameters will be stored with
the rest of the parameters of the experiment.
