.. _parallellab-class:

:class:`ParallelLab`: Running experiments locally in parallel
=============================================================

.. currentmodule:: epyc

.. autoclass:: ParallelLab

.. automethod:: ParallelLab.numberOfCores


Running experiments
-------------------

As with the sequential :class:`Lab` class, experiments run on a
:class:`ParallelLab` will be run synchronously: the calling thread
will block until all the experiments have completed.

.. note::

   If you need asynchronous behaviour than you need to use a :class:`ClusterLab`.

.. automethod:: ParallelLab.runExperiment


.. warning::

   :class:`ParallelLab` uses Python's ``joblib`` internally to create
   parallelism, and ``joblib`` in turn creates sub-processes in which to
   run experiments. This means that the experiment is running in a
   different process than the lab, and hence in a different address
   space. The upshot of this is that any changes made to variables in
   an experiment will only be visible to that experiment, and won't be
   seen by either other experiments or the lab. You can't, for
   example, have a class variable that's accessed and updated by all
   instances of the same experiment: this would work in a "normal"
   :class:`Lab`, but won't work on a :class:`ParallelLab` (or indeed
   on a :class:`ClusterLab`).

   The way to avoid any issues with this is to only communicate *via*
   the :class:`Experiment` API, accepting parameters to set the
   experiment up and returning them through a :term:`results dict`.
   Any updates to experimental parameters or metadata are also
   communicated correctly (see :ref:`epyc-parameters`).
