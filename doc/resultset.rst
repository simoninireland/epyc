:class:`ResultSet`: A homogeneous collection of results from experiments
========================================================================

.. currentmodule :: epyc
   
.. autoclass :: ResultSet

.. important ::

    In general client code will never interact with result sets directly: all
    interactions should go through a :class:`LabNotebook` to allow for management of
    persistence and so on.


Metadata access
---------------

The result set gives access to its title and the names of the various elements it
stores. These names may change over time, if for example you add a results dict
that has extra results than those you added earlier.

.. automethod :: ResultSet.title

.. automethod :: ResultSet.names

.. automethod :: ResultSet.metadataNames

.. automethod :: ResultSet.parameterNames

.. automethod :: ResultSet.namesNames

The result set can also have attributes set, which can be accessed either
using methods or by treating the result set as a dict.

.. automethod :: ResultSet.setAttribute

.. automethod :: ResultSet.getAttribute

.. automethod :: ResultSet.keys

.. automethod :: ResultSet.__contains__

.. automethod :: ResultSet.__setitem__

.. automethod :: ResultSet.__getitem__

.. automethod :: ResultSet.__delitem__

.. important ::

    The length of a result set (:meth:`ResultSet.__len__`) refers to the
    number of results, *not* to the number of attributes (as would be the
    case for a dict). 


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
of experimental parameters. Unlike "proper" results, pending results can be
cancelled and deleted from the result set -- often by "resolving" them into
"real" results.

.. automethod :: ResultSet.addSinglePendingResult

.. automethod :: ResultSet.cancelSinglePendingResult

.. automethod :: ResultSet.pendingResults

.. automethod :: ResultSet.numberOfPendingResults

.. automethod :: ResultSet.pendingResultsFor

.. automethod :: ResultSet.ready


Dirtiness
---------

Adding results or pending results to a result set makes it dirty, in need of
storing if being used with a persistent notebook. This is used to avoid
unnecessary writing of unchanged data.

.. automethod :: ResultSet.dirty

.. automethod :: ResultSet.isDirty


Type mapping and inference
--------------------------

A result set types all the elements within a results dict using ``numpy``'s ``dtype``
system.

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

The type mapping is used to generate a dtype for each Python type, but preserving
any ``numpy`` types used.

.. automethod :: ResultSet.typeToDType

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


