:class:`JSONLabNotebook`: A persistent store for results
========================================================

.. currentmodule:: epyc
   
.. autoclass:: JSONLabNotebook


Notebook creation
-----------------

.. automethod:: JSONLabNotebook.__init__


Persistence
-----------

JSON notebooks are persistent, with the data being saved into a file
identified by the notebook's name. Committing the notebook forces a save.
   
.. automethod:: JSONLabNotebook.isPersistent
   
.. automethod:: JSONLabNotebook.commit

.. automethod:: JSONLabNotebook.patch

