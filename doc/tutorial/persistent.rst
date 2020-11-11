.. _persistent-datasets:

.. currentmodule :: epyc

Persistent datasets
-------------------

We :ref:`already met <lab-experiment>` ``epyc``'s :class:`JSONLabNotebook`
class, which stores notebooks using a portable JSON format. This is neither
compact nor standard: it takes a lot of disc space for large notebooks, and
doesn't immediately interoperate with other tools.

The :class:`HDF5LabNotebook` by contrast uses the HDF5 file format which is
supported by a range of other tools. It can be used in the same way as
any other notebook:

.. code-block :: python

    from epyc import Lab, HDF5LabNotebook
    
    lab = Lab(notebook=HDF5LabNotebook('mydata.h5'))

Change to result sets are persisted into the underlying file. It's possible
to apply compression and other filters to optimise storage, and the file format
is as far as possible self-describing with metadata to allow it to be read
and interpreted at a later date.

 
