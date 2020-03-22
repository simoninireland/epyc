.. _jupyter:

.. currentmodule:: epyc

Integration with Jupyter
========================

`Jupyter <https://jupyter.org>`_ is an interactive notebook system that provides a flexible
front-end onto a number of different language "kernels" -- including Python. Notebooks
can include text, graphics, and executable code, and so are an excellent framework for
the interactive running of computation experiments.

``epyc`` can be used from Jupyter notebooks in a naive way simply by creating a local
lab and working with it as normal:

.. code-block:: python

    lab = epyc.Lab()

However this provides access only to the simplest kind of lab, running on a single local core.
It is clearly desirable to be able to use more flexible resources.

The :class:`ClusterLab` class has a number of features which work well with Jupyter.

