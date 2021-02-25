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
[Binder](https://mybinder.org). The notebook is included in the
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

``epyc`` solves this problem with the @meth:`LabNotebook.already`
method. This checks whether a given result set exists. If it does, it
is selected and the method returns True; if it doesn't then it's added
(and therefore implicitly selected) and the method returns False. We
can then use a much more attractive coding pattern:

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

There are a couple of limitations to be aware of, of course:

- You need to be careful about your choice of result set tags, so that
  they're meaningful to you later. This also makes the description
  and metadata more important.
- We assume that all the results in the set are computed in one go,
  since future cells protected by the same code pattern wouldn't be
  run.

The latter can be addressed by locking the result set after the
computation has happened (by calling :meth:`ResultSet.finish`) to fix
the results.

	 
