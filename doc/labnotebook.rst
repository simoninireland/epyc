:class:`LabNotebook`: A persistent store for results
====================================================

.. currentmodule:: epyc
   
.. autoclass:: LabNotebook


Notebook creation and management
--------------------------------

.. automethod:: LabNotebook.__init__
   
.. automethod:: LabNotebook.name
   
.. automethod:: LabNotebook.description


Persistence
-----------

Notebooks may be persistent, storing results and metadata to disc. The
default implementation is simply in-memory and volatile. Committing a
notebook ensures its data is written-through to persistent storage
(where applicable).
   
.. automethod:: LabNotebook.isPersistent
   
.. automethod:: LabNotebook.commit


Result storage and access
-------------------------

Results are stored using the :term:`results dict` structure of
parameters, experimental results, and metadata. There may be many
results dicts associated with each parameter point.

Results can be accessed in a number of ways: all together; as a
``DataFrame`` from ``pandas`` for easier analysis; as a list
corresponding to a particular parameter point; or as the latest result
for a given point.

.. automethod:: LabNotebook.addResult

.. automethod:: LabNotebook.numberOfResults

.. automethod:: LabNotebook.results

.. automethod:: LabNotebook.dataframe

.. automethod:: LabNotebook.__len__

.. automethod:: LabNotebook.__iter__

.. automethod:: LabNotebook.resultsFor

.. automethod:: LabNotebook.latestResultsFor


Pending results
---------------

Pending results allow a notebook to keep track of on-going
experiments, and are used by some :class:`Lab` sub-classes (for
example :class:`CLusterLab`) to manage submissions to a compute
cluster. A pending result is identified by some unique identifier,
typically a job id. Pending results can be resolved (have their
results filled in) using :meth:`addResult`, or can be cancelled, which
removes the record from the notebook from *not* from the lab managing
the underlying job.

.. automethod:: LabNotebook.addPendingResult

.. automethod:: LabNotebook.pendingResults

.. automethod:: LabNotebook.pendingResultsFor
 
.. automethod:: LabNotebook.cancelPendingResult
 
.. automethod:: LabNotebook.cancelPendingResultsFor
 
.. automethod:: LabNotebook.cancelAllPendingResults
