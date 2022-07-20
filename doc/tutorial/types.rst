.. types-experiment:

.. currentmodule:: epyc

Types of results from the experiment
------------------------------------

``epyc`` tries to be very Pythonic as regards the types one can return
from experiments. However, a lot of scientific computing must
interoperate with other tools, which makes some Python types less than
attractive.

The following Python types are safe to use in ``epyc`` result sets:

  - ``int``
  - ``float``
  - ``complex``
  - ``string``
  - ``bool``
  - one-dimensional arrays of the above
  - empty arrays

There are some elements of experimental metadata that use exceptions
or datestamps: these get special handling.

Also note that ``epyc`` can handle lists and one-dimensional arrays in
notebooks, but it *can't* handle higher-dimensional arrays. If you
have a matrix, for example, it needs to be unpacked into one or more
one-dimensional vectors. This is unfortunate in general but not often
an issue in practice.

There are some conversions that happen when results are saved to
persistent notebooks, using either JSON (:class:`JSONLabNotebook`) or
HDF5 (:class:`HDF5LabNotebook`): see the class documentation for the
details (or if unexpected things happen), but generally it's fairly
transparent when you stick top the types listed above.
