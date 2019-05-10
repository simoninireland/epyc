:class:`Experiment`: A single computational experiment
======================================================

.. currentmodule:: epyc
   
.. autoclass:: Experiment

.. important::

    Experiments have quite a detailed lifcycle that it is important to understand
    when writing any but the simplest experiments. See :ref:`lifecycle` for
    a detailed description.


Creating an experiment
----------------------

.. automethod:: Experiment.__init__
	       
	       
Structuring the results dict
----------------------------

The :term:`results dict` is the structure returned from running an
:class:`Experiment`. The dict has three top-level keys:

.. autoattribute:: Experiment.PARAMETERS
   :annotation:      

.. autoattribute:: Experiment.RESULTS
   :annotation:      

.. autoattribute:: Experiment.METADATA
   :annotation:      

The contents of the parameters and results dicts are defined by the :class:`Experiment`
designer. The metadata dict includes a number of standard elements. If the
:class:`Experiment` has run successfully, the
:attr:`Experiment.STATUS` key will be ``True``; if not, it will be
``False`` and the :attr:`Experiment.EXCEPTION` key will contain the
exception that was raised to cause it to fail. The metadata elements
include:

.. autoattribute:: Experiment.STATUS
   :annotation:

.. autoattribute:: Experiment.EXCEPTION
   :annotation:
      
.. autoattribute:: Experiment.TRACEBACK
   :annotation:
      
.. autoattribute:: Experiment.START_TIME
   :annotation:

.. autoattribute:: Experiment.END_TIME
   :annotation:

.. autoattribute:: Experiment.SETUP_TIME
   :annotation:

.. autoattribute:: Experiment.EXPERIMENT_TIME
   :annotation:

.. autoattribute:: Experiment.TEARDOWN_TIME
   :annotation:

:class:`Experiment` sub-classes may add other elements.

.. Warning::

   The exception traceback, if present, is a string, not a ``traceback`` object, since these
   do not work well in a distributed environment.

		   
Configuring the experiment
--------------------------

An :class:`Experiment` is given its parameters, a "point" in the
parameter space being explored, by called :meth:`Experiment.set`. This
takes a dict of named parameters and returns the :class:`Experiment`
itself.

.. automethod:: Experiment.set

.. automethod:: Experiment.configure

.. automethod:: Experiment.deconfigure

.. important::

   Be sure to call the base methods when overriding :meth:`Experiment.configure` and
   :meth:`Experiment.deconfigure`. (There should be no need to override :meth:`Experiment.set`.)

Running the experiment
----------------------

To run the experiment, a call to :meth:`Experiment.run` will run the experiment
at the given parameter point.

The dict of experimental results returned by :meth:`Experiment.do` is
formed into a :term:`results dict` by the private :meth:`Experiment.report`
method. Note the division of responsibilities here: :meth:`Experiment.do` returns the results
of the experiment (as a dict), which are then wrapped in a further dict by
:meth:`Experiment.report`.

.. automethod:: Experiment.run

.. automethod:: Experiment.do

.. automethod:: Experiment.setUp

.. automethod:: Experiment.tearDown

.. automethod:: Experiment.report


Accessing results
-----------------

The easiest way to access an :class:`Experiment`'s results is to store
the :term:`results dict` returned by :meth:`Experiment.run`. It is also
possible to access the results *post facto* from the
:class:`Experiment` object itself. It is also possible to access
experimental results using a dict-like interface keyed by name. These
operations only make sense on a newly-run :class:`Experiment`.

.. automethod:: Experiment.success

.. automethod:: Experiment.failed

.. automethod:: Experiment.results

.. automethod:: Experiment.experimentalResults

.. automethod:: Experiment.__getitem__

.. automethod:: Experiment.parameters

.. automethod:: Experiment.metadata

    
