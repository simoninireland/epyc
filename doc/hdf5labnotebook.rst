:class:`HDF5LabNotebook`: Results stored in a standard format
=============================================================

.. currentmodule :: epyc
   
.. autoclass :: HDF5LabNotebook


Managing result sets
--------------------

.. automethod :: HDF5LabNotebook.addResultSet


Persistence
-----------

HDF5 notebooks are persistent, with the data being saved into a file
identified by the notebook's name. Committing the notebook forces any
changes to be saved.
   
.. automethod :: HDF5LabNotebook.isPersistent
   
.. automethod :: HDF5LabNotebook.commit 


.. _hdf5-file-access:

HDF5 file access
----------------

The notebook will open the underlying HDF5 file as required, and generally will leave
it open. If you want more control, for example to make sure that the file is closed
and finalised, :class:`HDF5LabNotebook` also behaves as a context manager and so can be
used in code such as:

.. code-block :: python

    nb = HDF5LabNotebook(name='test.h5') 
    with nb.open():
        nb.addResult(rc1)
        nb.addResult(rc2)

After this the notebook's underlying file will be closed, with the new results
having been saved.
Alternatively simply use :meth:`LabNotebook.commit` to flush any changes to the
underlying file, for example:

.. code-block :: python

    nb = HDF5LabNotebook(name='test.h5') 
    nb.addResult(rc1)
    nb.addResult(rc2)
    nb.commit()


.. _hdf5-file-structure:

Structure of the HDF5 file
--------------------------

.. note ::

    The structure inside an HDF5 file is only really of interest if you're planning on
    using an ``epyc``-generated dataset with some other tools.

HDF5 is a "container" file format, meaning that it behaves like an archive containing
directory-like structure. ``epyc`` structures its storage by using a group for each
result set, held within the "root" group of the container. The root group has
attributes that hold "housekeeping" information about the notebook.

.. autoattribute :: HDF5LabNotebook.VERSION

.. autoattribute :: HDF5LabNotebook.DESCRIPTION

.. autoattribute :: HDF5LabNotebook.CURRENT

Any attributes of the notebook are also written as top-level attributes in this grup.
Then, for each :class:`ResultSet` in the notebook, there is a group whose name
corresponds to the result set's tag. This group contains any attributes of the
result set, always including three attributes storing the metadata, parameter,
and experimental result field names. 

.. note ::

    Attributes are all held as strings at the moment. There's a case for giving
    them richer types in the future.

The attributes also include the description of the result set and a flag indicating whether
it has been locked.

.. autoattribute :: HDF5LabNotebook.DESCRIPTION

.. autoattribute :: HDF5LabNotebook.LOCKED

Within the group are two datasets: one holding the results of experiments, and one holding
pending results yet to be resolved.

.. autoattribute :: HDF5LabNotebook.RESULTS_DATASET

.. autoattribute :: HDF5LabNotebook.PENDINGRESULTS_DATASET

If there are no pending results then there will be no pending results dataset.
This makes for cleaner interaction when archiving datasets, as there are no
extraneous datasets hanging around.

So an ``epyc`` notebook containing a result set called "my_data" will give
rise to an HDF5 file containing a group called "my_data", within which
will be a dataset named by :attr:`HDF5LabNotebook.RESULTS_DATASET` and possibly
another dataset named by :attr:`HDF5LabNotebook.PENDINGRESULTS_DATASET`. There will
also be a group named by :attr:`LabNotebook.DEFAULT_RESULTSET` which is where
results are put "by default" (*i.e.*, if you don't define explicit result sets).


.. _hdf5-type-management:

HDF5 type management
--------------------

``epyc`` takes a very Pythonic view of experimental results, storing them
in a :term:`results dict` with an unconstrained set of keys and types: and
experiment can store anything it likes as a result. The :class:`ResultSet`
class handles mapping Python types to ``numpy`` dtypes: see :ref:`resultset-type-inference`
for details.

The HDF5 type mapping follows the ``numpy`` approach closely. Some types
are mapped more restrictively than in ``numpy``: this is as one would expect,
of course, since HDF5 is essentially an archive format whose files need to be
readable by a range of tools over a long period.
Specifically this affects exceptions, tracebacks,
and ``datetime`` values, all of which are mapped to HDF5 strings (in ISO standard
date format for the latter). A little bit of patching happens for "known"
metadata values (specifically :attr:`Experiment.START_TIME` and :attr:`Experiment.END_TIME`)
which are automatically patched to ``datetime`` instances when loaded.

.. warning ::

    ``epyc`` allows result dicts to contain arrays as results. These can only be
    written to HDF5 if all the array results have the same shape: having different
    shapes will (probably) result in an exception with a hard-to-understand
    message.

    To work around this, it's safest to not have array-valued results. If you need
    them, pick a shape beforehand and stick to it.

    This limitation may be removed in future versions.


Tuning parameters
-----------------

Some parameters are available for tuning the notebook's behaviour.

The default size of a new dataset can be increased if desired, to pre-allocate
space for more results.

.. autoattribute :: HDF5LabNotebook.DefaultDatasetSize

The dataset will expand and contract automatically to
accommodate the size of a result set: its hard to see why this value would need
to be changed.


Low-level protocol
------------------

The low-level handling of the HDF5 file is performed by a small number of
private methods -- never needed directly in client code, but possibly in
need of sub-classing for some specialist applications.

Three methods handle file creation and access.

.. automethod :: HDF5LabNotebook._create

.. automethod :: HDF5LabNotebook._open

.. automethod :: HDF5LabNotebook._close

Four other methods control notebook-level and result-set-level I/O. These
all assume that the file is opened and closed around them, and will fail if not.

.. automethod :: HDF5LabNotebook._load

.. automethod :: HDF5LabNotebook._save

.. automethod :: HDF5LabNotebook._read

.. automethod :: HDF5LabNotebook._write

There are also two private methods that handle the conversion of ``numpy`` dtypes
to the (ever so slightly different) ``h5py`` dtypes.

.. automethod :: HDF5LabNotebook._HDF5simpledtype

.. automethod :: HDF5LabNotebook._HDF5dtype




