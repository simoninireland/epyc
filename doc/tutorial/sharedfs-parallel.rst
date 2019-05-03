.. _sharedfs-parallel:

.. currentmodule:: epyc

Setting up a cluster of machines with a shared file system
----------------------------------------------------------

With this setup we move away from running a cluster on a single machine and tackle multiple machines.
This is the simplest example of a **distributed compute cluster**, where "distributed" just means that we'll
be making use of several independent machines.

.. warning::

    We'll assume that all the machines in your cluster is running Linux or some other Unix variant.

The type of cluster we'll set up is common in university environments, and consists of several
machines that share a common file system. By this we mean that, whichever machine you log-on to, you're
presented with the same set of files -- and most especially, with your home directory.

Let's suppose we have a 10-machine cluster, with machines called ``cl-0``, ``cl-1``, up to ``cl-9``. Suppose we're
logged-on to ``cl-0``. To start a cluster, we first create a profile and then provide ``epyc`` with the names
of the machines we want to make use of. The cluster is controlled form the machine we're logged-in on (``cl-0`` in
this case): the machine names we provide will have engines started on them, and if that list includes
``cl-0`` then it'll get engines as well:

.. code-block:: sh

    epycluster.sh start --profile default --machines "cl-0 cl-1 cl-2 cl-3 cl-4 cl-5 cl-6 cl-7 cl-8 cl-9"

That list of machines is awkward, so we could probably benefit from storing it in a shell variable in
case we want to use it several times:

.. code-block:: sh

    machines="cl-0 cl-1 cl-2 cl-3 cl-4 cl-5 cl-6 cl-7 cl-8 cl-9"
    epycluster.sh start --profile default --machines $machines

Actually in this case we can simply things a bit moree, since clusters of this kind
often have machines with very structured names: ``cl-`` plus anumber in our case. It therefore
makes sense to make use of this structure to reduce the amount of typing we have to do:

.. code-block:: sh

    epycluster.sh start --profile default --machines "$(seq -f 'cl-%g' 0 9)"

The piece of magic at the end generates a seuqnece of numbers from 0 to 9 and, for each one, fills-in the
template of the form of a C ``printf`` format string.

To stop the cluster, we use:

.. code-block:: sh

    epycluster.sh stop --profile default

Notice that we don't need the list of machine names: ``epyc`` remembers them.












