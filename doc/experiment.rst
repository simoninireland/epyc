:class:`Experiment`: A single computational experiment
======================================================

.. currentmodule:: epyc
   
.. autoclass:: Experiment


Creating an experiment
----------------------

.. automethod:: Experiment.__init__
	       
	       
Structuring the results dict
----------------------------

The :term:`results dict` is the structure returned from running an
:class:`Experiment` using :meth:`Experiment.do`. The structure has
three top-level keys:

.. autoattribute:: Experiment.PARAMETERS
   :annotation:      

.. autoattribute:: Experiment.RESULTS
   :annotation:      

.. autoattribute:: Experiment.METADATA
   :annotation:      

The parameters and results are defined by the :class:`Experiment`
designer. The metadata includes a number of standard elements. If the
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

		   
Configuring the experiment
--------------------------

An :class:`Experiment` is given its parameters, a "point" in the
parameter space being explored, by called :meth:`Experiment.set`. This
takes a dict of named parameters and returns the :class:`Experiment`
itself, so it can be chained with further functions (typically :meth:`Experiment.do`).

A call to :meth:`Experiment.set` calls :meth:`Experiment.deconfigure`
if parameters have previously been set, and then calls :meth:`Experiment.configure`
to set the new parameters. Sub-classes can override :meth:`Experiment.configure`
and :meth:`Experiment.deconfigure` to, for example, set up
the :class:`Experiment` for repeated runs at the same parameter
point. Overriding methods should call the base implementation to
perform the standard functions as well as their own.

.. automethod:: Experiment.set

.. automethod:: Experiment.configure

.. automethod:: Experiment.deconfigure


Running the experiment
----------------------

To run the experiment, a call to :meth:`Experiment.run` will run the experiment
at the given parameter point. :meth:`Experiment.run` first calls :meth:`Experiment.setUp`
to perform any setting-up needed for the run; then calls :meth:`Experiment.do`
to perform the experiment itself; and fiinally calles :meth:`Experiment.tearDown`
to tidy up. :meth:`Experiment.do` must be overridden in sub-classes,
while :meth:`Experiment.setUp` and :meth:`Experiment.tearDown` may be
as required (and should call the base implementations first).

The dict of experimental results returned by :meth:`Experiment.do` is
formed into a :term:`results dict` by the private :meth:`Experiment.report`
method. This method can be overridden to customise the results dict,
typically to add additional metadata: again, overriding methods should
call the base implementation to make sure the dict is well-formed.

.. automethod:: Experiment.run

.. automethod:: Experiment.do

.. automethod:: Experiment.setUp

.. automethod:: Experiment.tearDown

.. automethod:: Experiment.report


Accessing results
-----------------

The easiest way to access an :class:`Experiment`'s results is to store
the results dict returned by :meth:`Experiment.do`. It is also
possible to access the results *post facto* from the
:class:`Experiment` object itself. It is also possible to access
experimental results using a dict-like interface keyed by name. These
operations only make sense on a newly-run :class:`Experiment`.

.. automethod:: Experiment.results

.. automethod:: Experiment.experimentalResults

.. automethod:: Experiment.__getitem__

.. automethod:: Experiment.parameters

.. automethod:: Experiment.metadata

    
