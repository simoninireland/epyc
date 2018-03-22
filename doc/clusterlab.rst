:class:`ClusterLab`: Managing experiments in parallel
=====================================================

.. currentmodule:: epyc
   
.. autoclass:: ClusterLab


Lab creation and management
---------------------------

Creating a :class:`ClusterLab` connects the lab object to a
pre-existing ``ipyparallel`` cluster. This can be done in a number of
ways, matching all the ways available for ``ipyparallel.Client``
objects: the easiest is to provide a link to the
``ipcluster-client.json`` file that is created by the cluster to
contain the necessary connection parameters.

Once created, the :class:`ClusterLab` can be opened and closed to
connect and disconnect from the cluster: the class' methods do this
automatically, and try to close the connection where possible to avoid
occupying network resources. Closing the connection explicitly will
cause no problems, as it re-opens automatically when needed.

.. automethod:: ClusterLab.__init__

.. automethod:: ClusterLab.open
		
.. automethod:: ClusterLab.close

		
Interacting with the cluster
----------------------------

The :class:`ClusterLab` can be queried to determine the number of
engines available in the cluster to which it is connected, which
essentially defines the degree of available parallelism. The lab also
provides a :meth:`ClusterLab.sync_imports` method that allows modules
to be imported into the namespace of the cluster's engines. This needs
to be done before running experiments, to make all the code used by an
experiment available in the cluster.

.. automethod:: ClusterLab.numberOfEngines
		
.. automethod:: ClusterLab.engines

.. automethod:: ClusterLab.sync_imports

.. automethod:: ClusterLab.use_dill

		
Running experiments
-------------------

Cluster experiments are run as with a normal :class:`Lab`, by setting
a parameter space and submitting an experiment to :meth:`ClusterLab.runExperiment`.
The experiment is replicated and passed to each engine, and
experiments are run on points in the parameter space in
parallel. Experiments are run asynchronously: :meth:`runExperiment`
returns as soon as the experiments have been sent to the cluster.

The :meth:`ClusterLab.readyFraction` method returns the fraction of
results that are ready for retrieval, *i.e.*, the fraction of the
parameter space that has been explored. :meth:`ClusterLab.ready` tests
whether *all* results are ready. For cases where it is needed (which
will hopefully be few and far between), :meth:`ClusterLab.wait` blocks
until all results are ready.  

.. automethod:: ClusterLab.runExperiment

.. automethod:: ClusterLab.readyFraction

.. automethod:: ClusterLab.ready

.. automethod:: ClusterLab.wait



Results management
------------------


.. automethod:: ClusterLab.updateResults
		
.. automethod:: ClusterLab.numberOfResults

.. automethod:: ClusterLab.numberOfPendingResults

.. automethod:: ClusterLab.pendingResults
		
.. automethod:: ClusterLab.pendingResultsFor

.. automethod:: ClusterLab.cancelPendingResultsFor
		
.. automethod:: ClusterLab.cancelAllPendingResults
		


