.. _clusterlab-class:

:class:`ClusterLab`: Flexible, parallel, asynchronous experiments
=================================================================

.. currentmodule :: epyc

.. autoclass :: ClusterLab


Interacting with the cluster
----------------------------

The :class:`ClusterLab` can be queried to determine the number of
engines available in the cluster to which it is connected, which
essentially defines the degree of available parallelism. The lab also
provides a :meth:`ClusterLab.sync_imports` method that allows modules
to be imported into the namespace of the cluster's engines. This needs
to be done before running experiments, to make all the code used by an
experiment available in the cluster.

.. automethod :: ClusterLab.numberOfEngines

.. automethod :: ClusterLab.engines

.. automethod :: ClusterLab.sync_imports


Running experiments
-------------------

Cluster experiments are run as with a normal :class:`Lab`, by setting
a parameter space and submitting an experiment to :meth:`ClusterLab.runExperiment`.
The experiment is replicated and passed to each engine, and
experiments are run on points in the parameter space in
parallel. Experiments are run asynchronously: :meth:`runExperiment`
returns as soon as the experiments have been sent to the cluster.

.. automethod :: ClusterLab.runExperiment

The :meth:`ClusterLab.readyFraction` method returns the fraction of
results that are ready for retrieval, *i.e.*, the fraction of the
parameter space that has been explored. :meth:`ClusterLab.ready` tests
whether *all* results are ready. For cases where it is needed (which
will hopefully be few and far between), :meth:`ClusterLab.wait` blocks
until all results are ready.

.. automethod :: ClusterLab.readyFraction

.. automethod :: ClusterLab.ready

.. automethod :: ClusterLab.wait


Results management
------------------

A cluster lab is performing computation remotely to itself, typically on another machine
or machines. This means that pending results may become ready spontaneously (from the
lab's perspective.) Most of the operations that access results first synchronise the
lab's notebook with the cluster, retrieving any results that have been resolved since
the previous check. (Checks can also be carried out directly.)

.. automethod :: ClusterLab.updateResults


Connection management
---------------------

A :class:`ClusterLab` can be opened and closed to
connect and disconnect from the cluster: the class' methods do this
automatically, and try to close the connection where possible to avoid
occupying network resources. Closing the connection explicitly will
cause no problems, as it re-opens automatically when needed.

.. important ::

    Connection management is intended to be transparent, so
    there will seldom be a need to use any these methods directly.

.. automethod :: ClusterLab.open

.. automethod :: ClusterLab.close

In a very small number of circumstances it may be necessary to take control
of (or override) the basic connection functionality, which is provided by two
other helped methods.

.. automethod :: ClusterLab.connect

.. automethod :: ClusterLab.activate


Tuning parameters
-----------------

There are a small set of tuning parameters that can be adjusted to cope with
particular circumstances.

.. autoattribute :: ClusterLab.WaitingTime

.. autoattribute :: ClusterLab.Reconnections

.. autoattribute :: ClusterLab.Retries
