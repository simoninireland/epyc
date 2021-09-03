.. currentmodule:: epyc


:class:`CancelledException`: A result was cancelled
===================================================

.. autoclass:: CancelledException


:class:`ResultSetLockedException`: Trying to change a locked result set
=======================================================================

.. autoclass:: ResultSetLockedException


:class:`LabNotebookLockedException`: Trying to change a locked lab notebook
===========================================================================

.. autoclass:: LabNotebookLockedException


:class:`PendingResultException`: Unrecognised pending result job identifier
===========================================================================

.. autoclass:: PendingResultException

.. automethod:: PendingResultException.jobid


:class:`ResultsStructureException`: Badly-structured results dict (or dicts)
============================================================================

.. autoclass:: ResultsStructureException

.. automethod:: ResultsStructureException.resultsdict


:class:`NotebookVersionException`: Unexpected version of a notebook file
=========================================================================

.. autoclass:: NotebookVersionException

.. automethod:: NotebookVersionException.expectedVersion

.. automethod:: NotebookVersionException.actualVersion


:class:`DesignException`: Impossible design
===========================================

.. autoclass:: DesignException
