.. _disconnected-usage:

.. currentmodule :: epyc

Using a cluster without staying connected to it
-----------------------------------------------

**Problem**: You're using a remote machine to run your simulations on, and don't want your local machine to have
to stay connected while they're running because you're doing a lot of computation.

**Solution**: ``epyc``'s cluster labs can work asynchronously, so you submit the experiments you want to do
and then come back to collect them later. This is good for long-running sets of experiments, and especially
good when your front-end machine is a laptop that you want to be able to take off the network when you go home.

Asynchronous operation is actually the default for :class:`ClusterLab`. Starting experiments by
default creates a pending result that will be resoplved when it's been computed on the cluster. 

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

You can then wait to get all the results:

.. code-block :: python

    lab.wait()

which will block until all the results become available, implying that your machine has to stay connected
to the cluster until the experiments finish: possibly a long wait. Alternatively you can check
what fraction of each result set has been successfully computed:

.. code-block :: python

    lab = ClusterLab(profile="mycluster",
                     notebook=HDF5LabNotebook('mydata.h5'))
    nb = lab.notebook()

    nb.select('first-experiments')
    print(lab.readyFraction())
    nb.select('second-experiments')
    print(lab.readyFraction())


(This is an important use case especially when using a remote cluster with a Jupyter
notebook, detailed more in the :ref:`fourth-tutorial`.)
The notebook will gradually be emptied of pending results and filled with completed results,
until none remain.

.. code-block :: python

    import time

    allReady = False
    tags = nb.resultSets()
    while not allReady:
        time.sleep(5)    # wait 5s
        allReady = all(map(lambda tag: lab.ready(tag), tags))
    print('All ready!')

The system for retrieving completed results is quite robust in that it commits the notebook
as results come in, minimising the posibility for loss through a crash.

.. important ::

    If you look at the API for :class:`LabNotebook` you'll see methods for
    :meth:`LabNotebook.ready` and :meth:`LabNotebook.readyFraction`. These
    check the result set *without updating*; the corresponding methods
    :meth:`Lab.ready` and :meth:`Lab.readyFraction` check the result set
    *after updating* with newly-completed results.

You can also, if you prefer, force an update of pending results directly:

.. code-block :: python

    lab.updateResults()

The call to :meth:`ClusterLab.updateResults` connects to the cluster and pulls down any results that have completed,
entering them into the notebook. You can then query the notebook (rather than the lab) about
what fraction of results are ready, taking control of when the cluster is interrogated.

