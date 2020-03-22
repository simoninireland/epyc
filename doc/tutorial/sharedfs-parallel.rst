.. _sharedfs-parallel:

.. currentmodule:: epyc

Setting up a cluster of machines with a shared file system
==========================================================

With this setup we move away from running a cluster on a single machine and tackle multiple machines.
This is the simplest example of a **distributed compute cluster**, where "distributed" just means that we'll
be making use of several independent machines.

.. warning::

    We'll assume that all the machines in your cluster is running Linux or some other Unix variant.

The type of cluster we'll set up is common in university environments, and consists of several
machines that share a common file system. By this we mean that, whichever machine you log-on to, you're
presented with the same set of files -- and most especially, with your home directory.

What we want to do is to set up what is essentially a :ref:`multicore machine <muilticore-parallel>`, but
one that uses cores on several machines. For this to work we need to tell ``ipcluster`` what machines
are in the cluster so that it can start engines on them.


Controllers, engines, and profiles
----------------------------------

The first thing to understand is what ``ipcluster`` is actually doing. We didn;t need to know
when using only one machine, but it becomes quite important when we're using a distributed cluster.

``ipcluster`` is essentially a control script that runs two other programs: ``ipcontroller`` that
controls the cluster, and ``ipengine`` that does the actual computing. For any cluster there is exactly
one instance of ``ipcontroller`` running, and then one instance of ``ipengine`` *for each core*.
So the ``-n=8`` option we saw in the :ref:`multicore case <muilticore-parallel>` is setting how many
engine processes are started and connected to the (one) controller.

When ``epyc`` connects to a cluster, it actually connects to the controller, which is then in turn
connected to the engines. So ``epyc`` can interact with a cluster of any complexity or size
in the same way.

As you might have guessed by now, in setting up a distributed cluster we need to start a controller
and then some engines, where the engines will reside on *different* machines. If each machine
is milticore, we'll want to start several engines on each -- but they'll all be connecting
back to the singfle controller.

When we created a profile for a :ref:`unicore machine <unicore-parallel>` we didn't go into details
about what happened: what *is* a profile anyway? A profile is best thought of as a little
environment within which we can do computing, and specifically *parallel* computing (hence the ``--parallel``
option) using ``ipcluster``. The profile contains all the information the ``ipcluster`` needs
to start-up a cluster, and this includes all the information we need for a distributed cluster.

The profile actually lives in a directory which we can find using:

.. code-block:: sh

    ipython locate profile cluster

(once again assuming we called our profile "cluster") which prints out the directory
on the file system that holds the profile's files. Let's assume for the rest of this tutorial that this results
in a path "/home/yourself/.ipython/profile_cluster", which would be fairly typical on Linux.

There are several files in this directory structure. Two are particularly important to us:

- ``ipcontroller_config.py``, the configuration for the cluster controller
- ``security/ipcontroller-client.json``, the controller connection credentials file

We'll refer to each of these files later.


Scenario
--------

Let's suppose we have 5 machines called ``cl-0`` up to ``cl- 4``.
Let's further suppose we're logged-on to ``cl-0``. And let's also suppose that each machine in the
cluster has 8 cores. And finally, let's suppose that we're logging-in to each machine
using ``ssh``.

.. warning::

    Distributed computing is a topic that can get very complicated very quickly. What follows
    is the explanation for a common, but rather basic, setup: there are many, many others.
    Your mileage may vary.

What we'll do is start a cluster with the cluster controller on ``cl-0``
and engines on the other 9 machines. Since the machines are all the same, and since they al
have 8 cores, we're expecting to start :math:`8 * 4 = 32` engines.

.. note::

    Why not 40 engines? Well we could, by starting 8 engines on ``cl-0`` as well. It's often
    a reasonable idea to leave the machine with the controller less loaded, though, because
    it has other things to do. However, if you need peak performance, starting engines
    on the controller machine is fine too.

We're going to need to tell ``ipcluster`` the machines we want to run on and how many engines
to run on each. This information is defined in the profile that we created earlier.


Editing the profile
-------------------

We need to edit the profile to record the names of all the machines. We need to add some information
to the ``ipcontroller_config.py`` file in the profile:

- Configure it for proper parallel use
- Set up the launcher for engines
- List the engines

If you open the file in an editor you'll see a long, long, list of Python assignments. The file is simply Python
code that sets upo the profile as required. We're going to edit it so that, when we execute ``ipcluster``
in this profile, it creates the processes we need.

Move to the end of the file in the editor and append the following:

.. code-block:: python
   :linenos:

    # ssh-based cluster
    c.IPClusterEngines.engine_launcher_class = 'SSHEngineSetLauncher'
    c.SSHLauncher.to_send = []
    c.SSHLauncher.to_fetch = []

    # connection management
    c.IPControllerApp.reuse_files = True

    # persistent store for jobs
    c.HubFactory.db_class = 'SQLiteDB'

Line 2 tell ``ipcluster`` to start its engines using ``ssh`` -- in other words, by logging-in
to the machines using ``ssh`` and running engine processes. Lines 3--4 say that we have a shared
file system and so no need to start copying control files around. Line 7 says to re-use connection
information between runs of the cluster, which cuts down on complexity. Line 10 tells the
controller to use a persistent database for the jobs it runs, which is important for supporting
:class:`ClusterLab`'s asynchronous operation.

We now need to provide the list of machines we're going to run engines on. These take the
form of a Python dict mapping each machine name (as used by ``ssh`` for login) to another dict
specifying the number of engines and the command used to start each one. For our cluster we have
four machines that will run 8 engines each, so we add the following:

.. code-block:: python

c.SSHEngineSetLauncher.engines = {
    'cl-1' : { 'n': 8, 'engine_cmd': [ 'python3', '-m', 'ipyparallel.engine' ] },
    'cl-2' : { 'n': 8, 'engine_cmd': [ 'python3', '-m', 'ipyparallel.engine' ] },
    'cl-3' : { 'n': 8, 'engine_cmd': [ 'python3', '-m', 'ipyparallel.engine' ] },
    'cl-4' : { 'n': 8, 'engine_cmd': [ 'python3', '-m', 'ipyparallel.engine' ] } }

.. note::

    ``ipcontroller_config.py`` is just Python, so one could get more funky and write
    a loop that populates ``c.SSHEngineSetLauncher.engines`` instead of all that
    repetition.

We now have a profile set up to run our cluster, and we can just run it as normal:

.. code-block:: sh

    ipcluster start --profile=cluster

The cluster should fire-up 8 engines on each of the four worker machines, plus a controller
on ``cl-0`` where we run the command.


Accessing the cluster locally
-----------------------------

If you're running yyour experiments directly on ``cl-0``, you'll now be able to create
a :class:`ClusterLab` that accesses the cluster immediately:

.. code-block:: python

    lab = epyc.ClusterLab(profile='cluster')
    print(lab.numberOfEngines())

    32

You now have a 32-node cluster ready for use.


Accessing the cluster from another machine
------------------------------------------

What if you're not running your experiments on ``cl-0``? -- whether because you have a
workstation elsewhere, or bacause you have a laptop? Both these are common use cases, and
both are easy to handle.

Firstly, you may be lucky: the shared file system we've assumed for all the cluster machines may
be shared by your workstation too. (This used to be a very common scenario, now sadly a lot
less so.) In this case, you can work with the cluster just as though it were local.

If this isn't the case, one more step is needed. We need to set up a profile on our workstation
that "shadows" the one on the cluster. Then a con ection to this profile connects us to
our cluster as we want.

We first create the "shadow" profile on our workstation:

.. code-block:: sh

    ipython profile create --parallel shadow

(I called the shadow profile ``shadow``: it might make more sense to use the same name as
you used for the cluster profile -- ``cluster`` in this tutorial -- but for the sake of explanation
I thought using a different name made things clearer.)

Now we need to copy the connection credentials file from the ``cluster`` profile to the ``shadow`` profile.
The following is a likely way to do this:

.. code-block:: sh

    cd ~/.ipython/profile_shadow/security
    scp cl-0:/home/yourself/.ipython/profile_cluster/security/ipcontroller-client.json .

Now if we start a :class:`ClusterLab` pointing at the ``shadow`` profile, we should connect
to the ``cluster`` profile: 

.. code-block:: python

    lab = epyc.ClusterLab(profile='shadow')
    print(lab.numberOfEngines())

    32


What can possibly go wrong?
---------------------------

An enormous amount! -- and unfortunately far too much to discuss in this tutorial, since most
of what can go wrong will go wrong in ``ipyparallel``, not in ``epyc`` (I hope...). A lot
of debugging can be done by `referring to the documentation <https://ipyparallel.readthedocs.io/en/latest/>`_,
but that does unfortunately require a lot of patience. The results are worth it, though,
as Python parallelism this way gives you access to far more computing power than can possibly
be available on a single machine. Good luck!




