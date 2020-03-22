.. _setup-parallel:

.. currentmodule:: epyc

Setting up a compute cluster
----------------------------

``epyc`` doesn't actually implement parallel computing itself: instead it builds on top of
existing Python infrastructure for this purpose. The underlying library ``epyc`` uses is
called `ipyparallel <https://ipyparallel.readthedocs.io/en/latest/>`_, which provides
portable parallel processing on both multicore machines and collections of machines.

.. warning::

    Confusingly, there's also a system called `PyParallel <http://pyparallel.org>`_ which is a completely
    different beast to ``ipyparallel``.

``epyc`` wraps-up ``ipyparallel`` within the framework of experiments, labs, and notebooks,
so that, when using ``epyc``, there's no need to interact directly with``ipyparallel``.
However, before we get to that stage we do need to set up the parallel compute cluster that
``epyc`` will use, and (at present) this *does* require interacting to some degree with
``ipyparallel``'s commands.

Setting up a cluster depends on what kind of cluster you have, and we'll describe each one
individually. It's probably easiest to start with the simplest system to which you have access,
and then -- if and when you need more performance -- move onto the more advanced systems.

.. toctree::
    :maxdepth: 1

    unicore-parallel.rst
    multicore-parallel.rst
    sharedfs-parallel.rst




