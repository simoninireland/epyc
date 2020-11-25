:class:`ResultSet`: A homogeneous collection of results from experiments
========================================================================

.. currentmodule :: epyc
   
.. autoclass :: ResultSet

.. important ::

    Most interactions with results should go through a :class:`LabNotebook` to allow
    for management of persistence and so on.


Adding results
--------------

Results can be added one at a time to the result set. Since result sets are persistent
there are no other operations.

.. automethod :: ResultSet.addSingleResult

The :meth:`LabNotebook.addResult` has a much more flexible approach to addition that
handles adding lists of results at one time.


Retrieving results
------------------

A result set offers two distinct ways to access results: as results dicts,
or as a ``pandas.DataFrame``. The former is often easier on small scales,
the latter for large scales.

.. automethod :: ResultSet.numberOfResults

.. automethod :: ResultSet.__len__

.. automethod :: ResultSet.results

.. automethod :: ResultSet.resultsFor

.. automethod :: ResultSet.dataframe

.. automethod :: ResultSet.dataframeFor

.. important ::

    The results dict access methods return all experiments, or all that have the
    specified parameters, regardless of whether they were successful or not.
    The dataframe access methods can pre-filter to extract only the successful
    experiments.
    

Parameter ranges
----------------

A result set can hold results for a range of parameter values. These are all returned
as part of the results dicts or dataframes, but it can be useful to access them
alone as well, independntly of specific results. The ranges returned by these methods
refer only to real results.

.. automethod :: ResultSet.parameterRange

.. automethod :: ResultSet.parameterSpace

.. automethod :: ResultSet.parameterCombinations


Managing pending results
------------------------

Pending results are those that are in the process of being computed based on a set
of experimental parameters.

.. automethod :: ResultSet.pendingResults

.. automethod :: ResultSet.numberOfPendingResults

.. automethod :: ResultSet.pendingResultsFor

.. automethod :: ResultSet.pendingResultParameters

.. automethod :: ResultSet.ready

Three methods within the interface are used by :class:`LabNotebook` to management
pending results. They shouldn't be needed from user code.

.. automethod :: ResultSet.addSinglePendingResult

.. automethod :: ResultSet.cancelSinglePendingResult

.. automethod :: ResultSet.resolveSinglePendingResult


Metadata access
---------------

The result set gives access to its description and the names of the various elements it
stores. These names may change over time, if for example you add a results dict
that has extra results than those you added earlier.

.. automethod :: ResultSet.description

.. automethod :: ResultSet.setDescription

.. important ::

    You can change the description of a result set after it's been created -- but you
    can't change any results that've been added to it.

.. automethod :: ResultSet.names

.. automethod :: ResultSet.metadataNames

.. automethod :: ResultSet.parameterNames

.. automethod :: ResultSet.resultNames

The result set can also have attributes set, which can be accessed either
using methods or by treating the result set as a dict.

.. automethod :: ResultSet.setAttribute

.. automethod :: ResultSet.getAttribute

.. automethod :: ResultSet.keys

.. automethod :: ResultSet.__contains__

.. automethod :: ResultSet.__setitem__

.. automethod :: ResultSet.__getitem__

.. automethod :: ResultSet.__delitem__

There are various uses for these attributes: see :ref:`resultset-metadata`
for one common use case.

.. important ::

    The length of a result set (:meth:`ResultSet.__len__`) refers to the
    number of results, *not* to the number of attributes (as would be the
    case for a dict). 


Locking
-------

Once the set of experiments to be held in a result set is finished, it's probably
sensible to prevent any further updated. This is accomplished by "finishing"
the result set, leaving it locked against any further updates.

.. automethod :: ResultSet.finish

One can check the lock in two ways, either by polling or as an assertion that
raises a :class:`ResultSetLockedException` when called on a locked result set. This
is mainly used to protect update methods.

.. automethod :: ResultSet.isLocked

.. automethod :: ResultSet.assertUnlocked


Dirtiness
---------

Adding results or pending results to a result set makes it dirty, in need of
storing if being used with a persistent notebook. This is used to avoid
unnecessary writing of unchanged data.

.. automethod :: ResultSet.dirty

.. automethod :: ResultSet.isDirty


.. _resultset-type-inference:

Type mapping and inference
--------------------------

A result set types all the elements within a results dict using ``numpy``'s 
`"dtype" data type system <https://numpy.org/doc/stable/reference/arrays.dtypes.html>`_.

.. note ::
    
    This approach is transparent to user code, and is explained here purely
    for the curious. 

There are actually two types involved: the dtype of results dicts formed from
the metadata, parameters, and experimental results added to the result set; and the 
dtype of pending results which includes just the parameters.

.. automethod :: ResultSet.dtype

.. automethod :: ResultSet.pendingdtype

The default type mapping maps each Python type we expect to see to a corresponding
``dtype``. The type mapping can be changed on a per-result set basis if required.

.. autoattribute :: ResultSet.TypeMapping
    :annotation:

There is also a mapping from ``numpy`` type kinds to appropriate default values, used
to initialise missing fields.

.. autoattribute :: ResultSet.TypeMapping
    :annotation:

.. automethod :: ResultSet.zero

The type mapping is used to generate a dtype for each Python type, but preserving
any ``numpy`` types used.

.. automethod :: ResultSet.typeToDtype

.. automethod :: ResultSet.valueToDtype

The result set infers the ``numpy``-level types automatically as results (and pending
results) are added.

.. automethod :: ResultSet.inferDtype

.. automethod :: ResultSet.inferPendingResultDtype

This behaviour can be sidestapped by explicitly setting the stypes (with care!).

.. automethod :: ResultSet.setDtype

.. automethod :: ResultSet.setPendingResultDtype

The progressive nature of typing a result set means that the type may change as new
results are added. This "type-level dirtiness" is controlled by two methods:

.. automethod :: ResultSet.typechanged

.. automethod :: ResultSet.isTypeChanged


