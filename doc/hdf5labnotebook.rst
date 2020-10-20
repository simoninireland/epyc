:class:`HDF5LabNotebook`: Results stored in a standard format
=============================================================

.. currentmodule :: epyc
   
.. autoclass :: HDF5LabNotebook


Persistence
-----------

HDF5 notebooks are persistent, with the data being saved into a file
identified by the notebook's name. Committing the notebook forces any
changes to be saved.
   
.. automethod :: HDF5LabNotebook.isPersistent
   
.. automethod :: HDF5LabNotebook.commit 


.. _hdf5-type-management:


Structure of the HDF5 file
--------------------------

HDF5 is a "container" file format, meaning that it behaves like an archive containing
directory-like structure. ``epyc`` structures its storage by using a group for each
result set, held within the "root" group of the container. The root group has
attributes that hold "housekeeping" information about the notebook.

.. autoattribute :: HDF5LabNotebook.DESCRIPTION

.. autoattribute :: HDF5LabNotebook.CURRENT

A result set's group is named after the tag used to label the result set in the notebook.
Within each group are two datasets: one holding the results of experiments, and one holding
pending results yet to be resolved.

.. autoattribute :: HDF5LabNotebook.RESULTS_DATASET

.. autoattribute :: HDF5LabNotebook.PENDINGRESULTS_DATASET

The structure is only really of interest if you're planning on using an ``epyc``-generated
dataset with some other tools.


HDF5 type management
--------------------

``epyc`` takes a very Pythonic view of experimental results, storing them
in a :term:`results dict` with an unconstrained set of keys and types: and
experiment can store anything it likes as a result. HDF5 is rather less
forgiving, in the sense that it requires a fixed set of keys in the dict,
each of which is always mapped to a value of a given type, with those
types being more constrained than those of Python. This is as one would expect,
or course, since HDF5 is essentially an archive format whose files need to be
readable by a range of tools over a long period. Nevertheless we somehow
have to map between these two views, and ``epyc`` supports two choices.

The first choice is to infer the types of each element in a reuslts dict,
converting them to HDF5 types. This is usually a straightforward choice
that works well, *modulo* the restrictions imposed by the HDF5 type system
that forces some Python types to strings.

.. automethod :: HDF5LabNotebook.inferType

The second choice is to let the user set the HDF5 types for each element
in the results dict -- typically results and parameters, but also any extra
metadata elements. This allows a programmer to take control of the ways in which
data is stored, for example by choosing a smaller int or float type when the
results are known to conform. This can result in a significant storage saving
for large result sets.

.. automethod :: HDF5LabNotebook.setResultSetType

In either case, some values will be read back with different types to those
that they had when they were generated. Specifically this affects Exceptions
and ``datetime`` values, both of which are mapped to HDF5 strings (in ISO standard
date format for the latter). A little bit of patching happens for "known"
metadata values (specifically :attr:`Experiment.START_TIME` and :attr:`Experiment.END_TIME`)
which are automatically patched to ``datetime`` instances when loaded.


Managing result sets
--------------------

Since HDF5 is designed to handle very large datasets, we need to ensure that
we manage the ways in which data comes into and out of memory. The HDF5
notebook manages this by only keeping the current result set in memory
by default: other result sets are unloaded. This process is completely
transparent to client code.

.. automethod :: HDF5LabNotebook.select


Tuning parameters
-----------------

Some parameters are available for tuning the notebook's behaviour.

The default size of a new dataset can be increased if desired, to pre-allocate
space for more results. The dataset will expand and contract automatically to
accommodate the size of a result set: its hard to see why this value would need
to be changed.

.. autoattribute :: HDF5LabNotebook.DefaultDatasetSize

By default the notebook swaps-out all result sets apart from the current one,
to save memory. This behaviour can be changed so that, once loaded (by a call to
:meth:`HDF5LabNotebook.select`) a result set is retained in memory. This would
reduce disc accesses but might use a lot of storage.

.. autoattribute :: HDF5LabNotebook.RetainResultSets

The default mapping from Python to HDF5 types is also available. It's probably
better to change the mappings of individual fields using :meth:`setResultSetType`
rather than changing the global behaviour.

.. autoattribute :: HDF5LabNotebook.TypeMapping
    :annotation:


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






