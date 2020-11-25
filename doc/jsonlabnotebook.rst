:class:`JSONLabNotebook`: A persistent store in JSON format
===========================================================

.. currentmodule :: epyc

.. note ::

    This style of notebook is fine for storing small datasets, and those
    that need to be accessed in a very portable manner, but is very
    wasteful for large datasets, for which an :class:`HDF5LabNotebook`
    is almost certainly a better choice.

.. autoclass :: JSONLabNotebook


Persistence
-----------

JSON notebooks are persistent, with the data being saved into a file
identified by the notebook's name. Committing the notebook forces a save.
   
.. automethod :: JSONLabNotebook.isPersistent
   
.. automethod :: JSONLabNotebook.commit


.. _json-file-access:

JSON file access
----------------

If you want to make sure that the file is closed
and commited after use you can use code such as:

.. code-block :: python

    with JSONLabNotebook(name='test.json', create=True).open() as nb:
        nb.addResult(rc1)
        nb.addResult(rc2)

After this the notebook's underlying file will be closed, with the new results
having been saved.


.. _json-file-structure:

Structure of the JSON file
--------------------------

The **version 1** file format is flat and stores all results in a single block.
This has been replaced by the **version 2** format that has a structure the follows
the structure of the result sets in the notebook.

.. important ::

    ``epyc`` can still read version 1 JSON notebooks, but will only save
    in the version 2 format.

The top level JSON object consists of elements holding the notebook title and
some housekeeping attributes. There is also a nested dict holding result sets,
keyed by their tag.

Each result set object contains elements for its description and any attributes.
There are also two further nested JSON objects, one holding results and
one holding pending results. Each result is simply a :term:`results dict` rendered
in JSON; each pending result is a job identifier mapped to the parameters
controlling the pending result.

