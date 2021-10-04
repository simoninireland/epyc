.. _command-line:

.. currentmodule:: epyc

Command-line interface
======================

``epyc`` includes a simple command-line tool for interacting with HDF5
notebooks. This allows you to edit notebooks without needing to write
Python code, which can be good for curating datasets ready for
publication.

.. note::

   This interface is still at a very early stage of development, and
   is likely to change considerably in future releases.

The command is unimaginatively called ``epyc``, and is a "container"
command that provides access to sub-commands for different
operations:

- Copying results sets between notebooks (``epyc copy``)
- Selecting a result set as current (``epyc select``)
- Delete a result set (``epyc remove``)
- Show the structure of a notebook (``epyc show``)

The details of each sub-command can be found using the ``--help``
option, for example:

.. code-block:: sh

    epyc remove --help

A possible curation workflow would be to list all the results sets in
a notebook using ``epyc show`` and then delete any that shouldn't be
published using ``epyc remove``. Note that in keeping with ``epyc``'s
philosophy of immutability you can only remove whole result sets:
there's no way to remove individual experiments from a result set.
