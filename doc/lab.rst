:class:`Lab`: An environment for running experiments
====================================================

.. currentmodule:: epyc

.. autoclass:: Lab


Lab creation and management
---------------------------

.. automethod:: Lab.__init__

.. automethod:: Lab.open

.. automethod:: Lab.close

.. automethod:: Lab.updateResults


Parameter management
--------------------

A :class:`Lab` is equipped with a multi-dimensional parameter space
over which to run experiments, one experiment per point. The
dimensions of the space can be defined by single values, lists, or
iterators that give the points along that dimension. Strings are
considered to be single values, even though they're technically
iterable in Python. Experiments are then conducted on the cross
product of the dimensions.

.. automethod:: Lab.addParameter

.. automethod:: Lab.parameters

.. automethod:: Lab.__len__

.. automethod:: Lab.__getitem__

.. automethod:: Lab.__setitem__

Parameters can be dropped, either individually or *en masse*, to
prepare the lab for another experiment. This will often accompany
creating or selecting a new result set in the :class:`LabNotebook`.

.. automethod:: Lab.__delitem__

.. automethod:: Lab.deleteParameter

.. automethod:: Lab.deleteAllParameters


Building the parameter space
----------------------------

The parameter ranges defined above need to be translated into "points"
in the parameter space at which to conduct experiments. This function
is delegated to the :term:`experimental design`, an instance of
:class:`Design`, which turns ranges into points. The design is
provided at construction time: by default a :class:`FactorialDesign`
is used, and this will be adequate for most use cases..

.. automethod:: Lab.design

.. automethod:: Lab.experiments


Running experiments
-------------------

Running experiments involves providing a :class:`Experiment` object
which can then be executed by setting its parameter point (using :meth:`Experiment.set`)
and then run (by calling :meth:`Experiment.run`) The :class:`Lab`
co-ordinates the running of the experiment at all the points chosen by
the design.

.. automethod:: Lab.runExperiment

.. automethod:: Lab.ready

.. automethod:: Lab.readyFraction


Conditional experiments
-----------------------

Sometimes it is useful to run experiments conditionally, for example
to create a :term:`result set` only if it doesn't already
exist. :class:`Lab` can do this by providing a function to execute in
order to populate a result set.

.. note::

   This technique work especially well with Jupyter notebooks, to
   avoid re-computing some cells. See :ref:`jupyter-avoid-repeated`.

.. automethod:: Lab.createWith


Accessing results
-----------------

Results of experiments can be accessed directly. via the lab's
underlying :class:`LabNotebook`, or directly as a ``DataFrame`` from
the ``pandas`` analysis package.

.. automethod:: Lab.notebook

.. automethod:: Lab.results

.. automethod:: Lab.dataframe
