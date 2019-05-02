.. _unicore-parallel:

.. currentmodule:: epyc

Setting up a machine with multiple cores
----------------------------------------

A multicoree machine is a far mopre sensible system on which to do large-scale computing, and they're
now surprisingly common: despite what we said before, a lot of laptops (and even a lot of phones) are
now multicore. Setting up an cluster on a multicore machine is just as easy as
for a `single core machine <unicore-parallel>`_ --once we know how many cores we have.
You may of course *know* how many cores you have, which is fine. If not, ``epyc`` can (usually) query
the machine to find out.

.. note::

    At the moment querying the number of available cores only works on Linux.

We use ``epyc-cluster`` to start the cluster as before, but tell it how many cores it has to work with.
If your machine has 16 cores, then the command would be:

.. code-block:: sh

    epycluster start --profile cluster --n 16

(Obviously we're assuming your cluster is called ``cluster`` as before.)

Suppose you don't know how many cores you have? ``epyc`` will try to guess:

.. code-block:: sh

    epycluster start --profile cluster

If ``epyc`` can find the number of cores, then it will create engines to use them all. If it can't,
it will simply create a single engine.

.. note::

    If you have a machine with only 8 cores, there's no point telling the cluster you have more: you won't get
    any extra speedup, and in fact things will probably run *slower* than if you let ``ipyparallel`` optimise
    itself for the actualy hardware it has available.

    Occasionally you may want to run a cluster with *fewer* cores than you actually have, to stop ``epyc``
    monopolising the machine: for example if you're sharing it with others, or if you want to also run
    other things. In this case you can tell ``ipcluster`` to use a smaller number of cores, leaving the
    remainder free for other programs to use.




