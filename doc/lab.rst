Lab: An environment for running experiments
===========================================

.. currentmodule:: epyc
   
.. autoclass:: Lab


Lab creation and management
---------------------------

.. automethod:: Lab.__init__

.. automethod:: Lab.open

.. automethod:: Lab.close

.. automethod:: Lab.updateResults


Parameter space management
--------------------------

A :class:`Lab` is equipped with a multi-dimensional parameter space
over which to run experiments, one experiment per point. The
dimensions of the space can be defined by single values, lists, or
iterators that give the points along that dimension. Strings are
considered to be single values, even though they're technically
iterable in Python. Experiments are then conducted on the cross
product of the dimensions.

.. automethod:: Lab.addParameter
		
.. automethod:: Lab.parameters
		
.. automethod:: Lab.parameterSpace
		
.. automethod:: Lab.__len__
		
.. automethod:: Lab.__getitem__
		
.. automethod:: Lab.__setitem__


Running experiments
-------------------

Running experiments involves providing a :class:`Experiment` object
which can then be executed by setting its parameter point (using :meth:`Experiment.set`)
and then run (by calling :meth:`Experiment.run`) The :class:`Lab`
co-ordinates the running of the experiment at all points in the lab's
parameter space. 

.. automethod:: Lab.runExperiment
		
.. automethod:: Lab.ready
		

Accessing results
-----------------

Results of experiments can be accessed directly. via the lab's
underlying :class:`LabNotebook`, or directly as a ``DataFrame`` from
the ``pandas`` analysis package.

.. automethod:: Lab.notebook
		
.. automethod:: Lab.results
		
.. automethod:: Lab.dataframe
		

