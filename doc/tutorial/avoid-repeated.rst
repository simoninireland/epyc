.. _jupyter-avoid-repeated:

.. currentmodule:: epyc

Avoiding repeated computation
-----------------------------

Consider the following use case. You create a Jupyter notebook for
calculating your exciting new results. You create a notebook, add some
result sets, do some stunning long computations, and save the notebook
for later sharing.

After some time, you decide want to add some more computations to the
notebook. You open it, and realise that all the results you computed
previously are still available in the notebook. But if you were to
re-execute the notebook, you'd re-compute all those results when
instead you could simply load them and get straight on with your new

Or perhaps you share your notebook "live" using
`Binder <https://mybinder.org>`_. The notebook is included in the
binder, and people can see the code you used to get them (as with all
good notebooks). But again they may want to use and re-analyse your
results but not re-compute them.

One way round this is to have two cells, something like this to do (or
re-do) the calculations:

.. code-block:: python

   # execute this cell if you want to compute the results
   nb = epyc.HDF5LabNotebook('lots-of-results.h5')
   nb.addResultSet('first-results',
		   description='My long-running first computation')
   e = LongComputation()
   lab = Lab(nb)
   lab[LongComputation.INITIAL] = int(1e6)
   lab.runExperiment(e)

and then another one to re-use the ones you prepared earlier:

.. code-block:: python

   # execute this cell if you want to re-load the results
   nb = epyc.HDF5LabNotebook('lots-of-results.h5')
   nb.select('first-results')

Of course this is quite awkward, relies on the notebook user to decide
which cells to execute -- and means that you can't simply run all the
cells to get back to where you started.

``epyc`` has two solutions to this problem.


Using ``createWith``
--------------------

The first (and preferred)_solution uses the :meth:`Lab.createWith`
method, which takes a function used to create a result set. When
called, the method checks if the result set already exists in the
lab's notebook and, if it does, selects it for use; if it doesn't,
then it is created, selected, and the creation function is called to
populate it.

To use this method we first define a function to create the data we
want:

.. code-block:: python

   def createResults(lab):
       e = LongComputation()
       lab[LongComputation.INITIAL] = int(1e6)
       lab.runExperiment(e)

We then use this function to create a result set, if it hasn't been
created already:

.. code-block:: python

   lab.createWith('first-results',
		  createResults,
		  description='My long-running first computation')

Note that the creation function is called with the lab it should use
as argument. :meth:`Lab.createWith` will return when the result set
has been created, which will be when all experiments have been run.

By default the lab's parameter space is reset before the creation
function is called, and any exception raised in the creation function
causes the result set to be deleted (to avoid partial results) and
propagates the exception to the caller. There are several ways to
customise this behaviour, described in the :meth:`Lab.createWith`
reference.


Using ``already``
-----------------

The second solution uses the :meth:`LabNotebook.already` method. This
is appropriate if you want to avoid creating additional functions just
for data creation, and instead have the code inline.

.. code-block:: python

   nb = epyc.HDF5LabNotebook('lots-of-results.h5')
   if not nb.already('first-results',
		     description='My long-running first computation'):
       e = LongComputation()
       lab = Lab(nb)
       lab[LongComputation.INITIAL] = int(1e6)
       lab.runExperiment(e)

If this cell is run on a lab notebook that doesn't contain the result
set, that set is created and the body of the conditional executes to
compute the results. If the cell is executed when the result set
already exists, it selects it ready for use (and any description
passed the :meth:`LabNotebook.already` is ignored). In either event,
subsequent code can assume that the result set exists, is selected,
and is populated with results.

.. note::

   Note that :meth:`Lab.createWith` is called against a lab while
   :meth:`LabNotebook.already` is called against a notebook. (The
   former uses the latter internally.)

In general :meth:`Lab.createWith` is easier to use than
:meth:`LabNotebook.already`, as the former handles exceptions,
parameter space initialisation, result set locking and the like.


Limitations
-----------

There are some limitations to be aware of, of course:

- Neither approach works with :ref:`disconnected operation <jupyter-disconnected>`
  when the results come back over a long period.
- You need to be careful about your choice of result set tags, so that
  they're meaningful to you later. This also makes the description
  and metadata more important.
- We assume that all the results in the set are computed in one go,
  since future cells protected by the same code pattern wouldn't be
  run.

The latter can be addressed by locking the result set after the
computation has happened (by calling :meth:`ResultSet.finish`) to fix
the results. :meth:`Lab.createWith` can do this automatically.
