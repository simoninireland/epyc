.. _multicore-parallel:

.. currentmodule:: epyc

Setting up a machine with multiple cores
========================================

A multicore machine is a far more sensible system on which to do large-scale computing, and they're
now surprisingly common: despite what we said before, a lot of laptops (and even a lot of phones) are
now multicore. Setting up an cluster on a multicore machine is just as easy as
for a :ref:`single core machine <unicore-parallel>` --once we know how many cores we have. If you're
running on Linux, we can ask the operating system, how many cores you have:

.. code-block:: sh

    grep -c processor /proc/cpuinfo

This prints the number of cores available.

.. note::

    At the moment querying the number of available cores only works on Linux.

We use ``ipcluster`` to start the cluster as before, but tell it how many cores it has to work with.
If your machine has 16 cores, then the command would be:

.. code-block:: sh

    upcluster start --profile=cluster --n=16

(Obviously we're assuming your cluster is called ``cluster`` as before.)

.. note::

    If you have a machine with only 8 cores, there's no point telling the cluster you have more: you won't get
    any extra speedup, and in fact things will probably run *slower* than if you let ``ipyparallel`` optimise
    itself for the actualy hardware it has available.

    Occasionally you may want to run a cluster with *fewer* cores than you actually have, to stop ``epyc``
    monopolising the machine: for example if you're sharing it with others, or if you want to also run
    other things. In this case you can tell ``ipcluster`` to use a smaller number of cores, leaving the
    remainder free for other programs to use.




