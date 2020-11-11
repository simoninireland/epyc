.. _pending-datasets:

.. currentmodule :: epyc

Pending results
---------------

Both multiple result sets and persistent notebooks really come into their own when combined
with the use of :class:`ClusterLab` instances to perform remote computations.

Once you have a connection to a cluster, you can start computations in multiple result
sets.

.. code-block :: python

    from epyc import ClusterLab

    lab = ClusterLab(profile="mycluster",
                     notebook=HDF5LabNotebook('mydata.h5', create=True))
    nb = lab.notebook()

    # perform some of the first experiments
    nb.addResultSet('first-experiments')
    lab['a'] = 12
    lab['b'] = range(1000)
    e = MyFirstExperiment()
    lab.runExperiment(e)

    # and then some others
    nb.addResultSet('second-experiments')
    lab['a] = 15
    lab['b'] = ['cat', 'dog', 'snake']
    lab['c'] = range(200)
    e = MySecondExperiment()
    lab.runExperiment(e)

These experiments will give rise to "pending" results as they are computed on the cluster:
1000 experimental runs in the first case, 300 in the second (the sizes of the respective
parameter spaces). If we check the fraction of results that are ready in each dataset they
will be retieved from the cluster and stored in the notebook:

.. code-block :: python

    nb.select('first-experiments')
    print(lab.readyFraction())

Note that results that are ready are collected for *all* datasets, not just the one we
query, but the fraction refers only to the *selected* current result set. This means that
over over time all the results in the notebook will be collected from
the cluster and stored.

Clusters support disconnected operation, which work well with persistent notebooks.
See :ref:`disconnected-usage` for details.

