:class:`LabNotebook`: A persistent store for results
====================================================

.. currentmodule:: epyc
   
.. autoclass:: LabNotebook


Metadata access
---------------

.. automethod:: LabNotebook.name
   
.. automethod:: LabNotebook.description

.. automethod:: LabNotebook.setDescription


Persistence
-----------

Notebooks may be persistent, storing results and metadata to disc. The
default implementation is simply in-memory and volatile. Committing a
notebook ensures its data is written-through to persistent storage
(where applicable).
   
.. automethod:: LabNotebook.isPersistent
   
.. automethod:: LabNotebook.commit


With blocks
-----------

Notebooks support ``with`` blocks, like files. For persistent notebooks
this will ensure that the notebook is committed. (For the default in-memory
notebook this does nothing.)

.. automethod:: LabNotebook.open

(See :ref:`json-file-access` and :ref:`hdf5-file-access` for examples
of this method in use.)

The ``with`` block approach is slightly more robust than the explicit
use of :meth:`LabNotebook.commit` as the notebook will be committed
even if exceptions are thrown while it is open, ensuring no changes
are lost accidentally. However notebooks are often held open for a
long time while experiments are run and/or analysed, so the explicit
commit can be more natural.


Result sets
-----------

Results are stored as :class:`ResultSet` objects, each with a unique tag.
The notebook allows them to be created, and to be selected to receive
results.
They can also be deleted altogether.

.. automethod:: LabNotebook.addResultSet

.. automethod:: LabNotebook.deleteResultSet

.. automethod:: LabNotebook.resultSet

.. automethod:: LabNotebook.resultSets

.. automethod:: LabNotebook.keys

.. automethod:: LabNotebook.numberOfResultSets

.. automethod:: LabNotebook.__len__

.. automethod:: LabNotebook.__contains__
		
.. automethod:: LabNotebook.resultSetTag

.. automethod:: LabNotebook.current

.. automethod:: LabNotebook.currentTag

.. automethod:: LabNotebook.select

.. automethod:: LabNotebook.already
		


Result storage and access
-------------------------

Results are stored using the :term:`results dict` structure of
parameters, experimental results, and metadata. There may be many
results dicts associated with each parameter point.

.. automethod:: LabNotebook.addResult

Results can be accessed in a number of ways: all together; as a
``pandas.DataFrame`` object for easier analysis; or as a list
corresponding to a particular parameter point.

.. automethod:: LabNotebook.numberOfResults

.. automethod:: LabNotebook.__len__

.. automethod:: LabNotebook.results

.. automethod:: LabNotebook.resultsFor

.. automethod:: LabNotebook.dataframe

.. automethod:: LabNotebook.dataframeFor


Pending results
---------------

Pending results allow a notebook to keep track of on-going
experiments, and are used by some :class:`Lab` sub-classes (for
example :class:`ClusterLab`) to manage submissions to a compute
cluster. A pending result is identified by some unique identifier,
typically a job id. Pending results can be resolved (have their
results filled in) using :meth:`LabNotebook.addResult`, or can be
cancelled, which removes the record from the notebook but *not* from
the lab managing the underlying job.

Since a notebook can have multiple result sets, the pending results
interface is split into three parts. Firstly there are the operations
on the currently-selected result set.

.. automethod:: LabNotebook.addPendingResult

.. automethod:: LabNotebook.numberOfPendingResults

.. automethod:: LabNotebook.pendingResults

Secondly, there are operations that work on any result set. You
can resolve or cancel a pending result simply by knowing its job id and
regardless of which is the currently selected result set. 

.. automethod:: LabNotebook.resolvePendingResult

.. automethod:: LabNotebook.cancelPendingResult

You can also check whether there are pending results remaining in any result set,
which defaults to the surrently selected result set.

.. automethod:: LabNotebook.ready

.. automethod:: LabNotebook.readyFraction

Thirdly, there are operations that work on all result sets.

.. automethod:: LabNotebook.allPendingResults

.. automethod:: LabNotebook.numberOfAllPendingResults


Locking the notebook
--------------------

Locking a notebook prevents further updates: result sets cannot be added,
all pending results are cancelled, and all individual result sets locked.
Locking is preserved for persistent notebooks, so once locked a notebook is
locked forever.

.. automethod:: LabNotebook.finish

.. automethod:: LabNotebook.isLocked

