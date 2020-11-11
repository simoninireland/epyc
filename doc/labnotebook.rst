:class:`LabNotebook`: A persistent store for results
====================================================

.. currentmodule:: epyc
   
.. autoclass :: LabNotebook


Metadata access
---------------

.. automethod :: LabNotebook.name
   
.. automethod : LabNotebook.description

.. automethod : LabNotebook.setDescription


Persistence
-----------

Notebooks may be persistent, storing results and metadata to disc. The
default implementation is simply in-memory and volatile. Committing a
notebook ensures its data is written-through to persistent storage
(where applicable).
   
.. automethod: : LabNotebook.isPersistent
   
.. automethod :: LabNotebook.commit


Result sets
-----------

Results are stored as :class:`ResultSet` objects. There is seldom any need
to interact with the result sets directly: the notbook allows them to be created,
and to be selected to receive results.



Result storage and access
-------------------------

Results are stored using the :term:`results dict` structure of
parameters, experimental results, and metadata. There may be many
results dicts associated with each parameter point. The most flexible
way to add results is using the :meth:`LabNotebook.addResults` method,
which handles single and sets of results. 

.. automethod :: LabNotebook.addResults

There is also a single-result version of the same method.

.. automethod :: LabNotebook.addResult

Results can be accessed in a number of ways: all together; as a
``pandas.DataFrame`` object for easier analysis; or as a list
corresponding to a particular parameter point.

.. automethod :: LabNotebook.numberOfResults

.. automethod :: LabNotebook.__len__

.. automethod :: LabNotebook.results

.. automethod :: LabNotebook.resultsFor

.. automethod :: LabNotebook.dataframe

.. automethod :: LabNotebook.dataframeFor


Pending results
---------------

Pending results allow a notebook to keep track of on-going
experiments, and are used by some :class:`Lab` sub-classes (for
example :class:`ClusterLab`) to manage submissions to a compute
cluster. A pending result is identified by some unique identifier,
typically a job id. Pending results can be resolved (have their
results filled in) using :meth:`LabNotebook.addResult`, or can be cancelled, which
removes the record from the notebook but *not* from the lab managing
the underlying job.

Since a notebook can have multiple result sets, the pending results
interface is split into three parts. Firstly there are the operations
on the currently-selected result set.

.. automethod :: LabNotebook.addPendingResult

.. automethod :: LabNotebook.numberOfPendingResults

.. automethod :: LabNotebook.pendingResults

Secondly, there are operations that work on any result set. You
can resolve or cancel a pending result simply by knowing its job id and
regardless of which is the currently selected result set. 

.. automethod :: LabNotebook.resolvePendingResult

.. automethod :: LabNotebook.cancelPendingResult

You can also check whether there are pending results remaining in any result set,
which defaults to the surrently selected result set.

.. automethod :: LabNotebook.ready

.. automethod :: LabNotebook.readyFraction

Thirdly, there are operations that work on all result sets.

.. automethod :: LabNotebook.allPendingResults

.. automethod :: LabNotebook.numberOfAllPendingResults

