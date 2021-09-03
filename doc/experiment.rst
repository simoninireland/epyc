:class:`Experiment`: A single computational experiment
======================================================

.. currentmodule:: epyc

.. autoclass:: Experiment

.. important::

    Experiments have quite a detailed lifcycle that it is important to understand
    when writing any but the simplest experiments. See :ref:`lifecycle` for
    a detailed description.


Creating the results dict
--------------------------

The :term:`results dict` is the structure returned from running an
:class:`Experiment`. They are simply nested Python dicts which can be
created using a static method.

.. automethod:: Experiment.resultsdict

The ``ResultsDict`` type is an alias for this structure. The dict has three top-level keys:

.. autoattribute:: Experiment.PARAMETERS
   :annotation:

.. autoattribute:: Experiment.RESULTS
   :annotation:

.. autoattribute:: Experiment.METADATA
   :annotation:

The contents of the parameters and results dicts are defined by the :class:`Experiment`
designer. The metadata dict includes a number of standard elements.


Standard metadata elements
--------------------------

The metadata elements include:

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

:class:`Experiment` sub-classes may add other metata elements as required.

.. note::

   Since metadata can come from many sources, it's important to consider the
   names given to the different values. `epyc` uses structured names based on
   the class names to avoid collisions.

If the :class:`Experiment` has run successfully, the
:attr:`Experiment.STATUS` key will be ``True``; if not, it will be
``False`` and the :attr:`Experiment.EXCEPTION` key will contain the
exception that was raised to cause it to fail and the :attr:`Experiment.TRACEBACK`
key will hold the traceback for that exception.

.. warning::

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

If the experiment returns a list of results dicts instead of just a single set, then
by default they are each wrapped in the same parameters and metadata and returned
as a list of results dicts.

.. automethod:: Experiment.setUp

.. automethod:: Experiment.run

.. automethod:: Experiment.do

.. automethod:: Experiment.tearDown

.. automethod:: Experiment.report

.. important::

   Again, if you override any of these methods, be sure to call the base class
   to get the default management functionality. (There's no such basic functionality
   for :meth:`Experiment.do`, though, so it can be overridden freely.)

.. note::

   You can update the parameters controlling the experiment from
   within :meth:`Experiment.setUp` and :meth:`Experiment.do`, and
   these changes will be saved in the :term:`results dict` eventually
   returned by :meth:`Experiment.run`.


Accessing results
-----------------

The easiest way to access an :class:`Experiment`'s results is to store
the :term:`results dict` returned by :meth:`Experiment.run`. It is also
possible to access the results *post facto* from the
:class:`Experiment` object itself, or using a dict-like interface keyed
by name. These operations only make sense on a newly-run :class:`Experiment`.

.. automethod:: Experiment.success

.. automethod:: Experiment.failed

.. automethod:: Experiment.results

.. automethod:: Experiment.experimentalResults

.. automethod:: Experiment.__getitem__

.. automethod:: Experiment.parameters

.. automethod:: Experiment.metadata
