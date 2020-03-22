.. _disconnected-usage:

.. currentmodule:: epyc

Using a cluster without staying connected to it
-----------------------------------------------

**Problem**: You're using a remote machine to run your simulations on, and don't want your local machine to have
to stay connected while they're running because you're doing a lot of computation.

**Solution**: ``epyc``'s cluster labs can work asynchronously, so you submit the experiments you want to do
and then come back to collect them later. This is good for long-running sets of experiments, and especially
good when your front-end machine is a laptop that you want to be able to take off the network when you go home.

Asynchronous operation is actually the default for :class:`ClusterLab`. When you start an experiment,
for example:

.. code-block:: python

    nb = epyc.JSONLabNotrebook('myexperiment.json')
    lab = epyc.ClusterLab(nb)
    lab['x'] = range(1000)
    lab.runExperiment(myExperiment())

The call to :meth:`ClusterLab.runExperiment` returns immediately. You can then wait to get all the results:

.. code-block:: python

    lab.wait()

which will block until all the results become available, implying that your machine has to stay connected
to the cluster until the experiments finish: possibly a long wait.

However, you can also just close the progam and walk away. The cluster keeps working. Later, when enough time
has passed, you can come back and call :meth:`ClusterLab.wait` to get all the results.

But what if you don't give the cluster enough time? -- you'll be stuck again. A better solution is to get
the results *that have actually finished*, and leave the rest running. To do this, you simply re-connect to the
cluster and request that it update its notebook with the completed results:

.. code-block:: python

    nb = epyc.JSONLabNotrebook('myexperiment.json')
    lab = epyc.ClusterLab(nb)
    lab.updateResults()
    print('We have {r} results available ({f} of the total'.format(r=lab.numberOfResults(), f=lab.readyFraction()))

The call to :meth:`ClusterLab.updateResults` connects to the cluster and pulls down any results that have completed,
entering them into the notebook. You can then ask thee lab (or indeed the notebook) for the number of results
available and.or for the fraction of results so you can check progress.

This approach works particularly well from Jupyter notebooks, where you can define an experiment, kick-off a simulation,
carry on writing, and have a cell that checks for the results that you re-execute until they're finished.
(Updating results when all the results are already in costs nothing.) If you want to be particularly funky, write
code that generates graphs or other results from whatever results are available, rather than having the code assume
that all the results are there: that way you can see the simulation progressing, which can be quite iluminating
in itself.
