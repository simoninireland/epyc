.. _jupyter-disconnected:

Jupyter notebooks and compute servers
-------------------------------------

The interactive nature of Jupyer notebooks means that they lend themselves to
"disconnected" operation with a :class:`ClusterLab`. To recap, this is where
we submit experiments to a remote compute cluster and then re-connect later
to retrieve the results. See :ref:`second-tutorial` for a description of
how to set up and use a remote cluster.

This mode of working is perfect for a notebook. You simply create a connection
to the cluster and run it as you wish:

.. code-block :: python

    from epyc import ClusterLab, HDF5LabNotebook
    import numpy

    nb = HDF5LabNotebook('notebook-dataset.h5', description='My data', create=True) 
    lab = ClusterLab(url_file='ipcontroller-client.json', notebook=nb)

    lab['first'] = numpy.linspace(0.0, 1.0, num=100)
    lab.runExperiment(MyExperiment())

Running these experiments happens in the background rather than freezing your
notebook (as would happen with a ordinary :class:`Lab`. It also doesn't attempt
to melt your laptop by running too many experiments locally. Instead the
experiments are scattered onto the cluster and can be collected later -- even after
turning your computer off, if necessary.

.. note ::

    We used an :class:`HDF5LabNotebook` to hold the results so that everything is
    saved between sessions. If you used a non-persistent notebook then you'd lose
    the details of the pending results. And anyway, do you *really* not want to
    save all your experimental results for later? 

All that then needs to happen is that you re-connect to the cluster and check for results:

.. code-block :: python

    from epyc import ClusterLab, HDF5LabNotebook
    import numpy

    nb = HDF5LabNotebook('notebook-dataset.h5', description='My data') 
    lab = ClusterLab(url_file='ipcontroller-client.json', notebook=nb)

    print(lab.readyFraction())

This will print the fraction of results that are now ready, a number between
0 and 1.

.. warning ::

    Notice that we omitted the ``create=True`` flag from the :class:`HDF5LabNotebook`
    the second time: we want to re-use the notebook (which holds all the details
    of the pending results we're expecting to collect), not create it afresh.
    Many core-hours of computation have been lost this way....

Checking the results pulls any that are completed, andyou can immediately start using
them if you wish: you don't have to wait for everything to finish. Just be careful
that whatever anaysis you start to perform understands that this is partial set of
results.




                    


