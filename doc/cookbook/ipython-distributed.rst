.. _ipython-distributed:

.. currentmodule:: epyc

Improving performance using a distributed compute cluster
---------------------------------------------------------

*Problem*: You've tried :ref:`ipython-multicore` and its not enough: you need still more computing power.

*Solution*: You need a compute cluster, a set of machiens whose sole purpose in life is to run your computing
jobs. Clusters are nothing new, they're a well-established way to get a "supercomputer on the cheap" by using
a collection of machines that you happen to have lying around (or can get access to). A university undergraduate
computing lab at the weekend might be a good example: all that lovely compute power sitting unused! A cluster
lets you put it to use.

.. note::

    This subject gets very involved very quickly. For the sake of everybodies'  mental health we'll assume you understand how
    to use ``ssh`` to log in to machines, and ``scp`` to copy files around. We'll also assume you've already
    read (and hopefully tried) :ref:`ipython-multicore`.

The basic approach to using ``epyc`` on a cluster is exactly the same as we used for a single multicore machine:
we create engines that can have jobs sent to them. Indeed, the Python code is *identical*, and there's no reason
for an experiment to be able to tell whether it's running sequentially, in parallel on a multicore,
or distributed on a cluster.

That's the good news. The bad news is that the steps we need to set up the compute infrastructure are a lot more
involved. But conceptually all we're doing here is creating *several* (probably) multicore computing systems and
wiring them together to act as a single cluster. Bear this in mind and we should be OK.

Getting the cluster running involves four steps, some of which are a bit complicated:

1. Getting the names of all the machines in the cluster

2. Setting up the compute environment *on each machine in the cluster*, which includes...

    2a. Editing the IPython profile

3. Running the ``ipyparallel`` infrastructure, which includes...

    3a. Copying security tokens to every machine in the cluster

4. Setting up a lab that will submit to this infrastructure

*Getting the names of the machines*. This is up to you, and depends entirely on your local set-up. Talk to a
sysadmin if you need help: actually, talk to one anyway to make sure it's OK to use the machines you're planning to use.

When you've got the machines names, make a note of them: we'll need them later.

.. note::

    We'll assume for the purposes of this tutorial that you can log-in directly to *all* these machines from
    your laptop or workstation. If you can't, it's still possible to set up a cluster using these machines, but it's
    considerably more in-depth and requires an understanding of ``ssh`` tunneling and other arcana that are out of scope
    here.

*Setting up the parallel infrastructure*. Let's begin by creating a venv.

.. warning::

    Previously we've mentioned that Python virtual environments or "venvs" are a good idea for
    reproducible scientific computing. They're *essential* for compute clusters, and without them things rapidly
    descend into chaos. So now might be a good time to review :ref:`epyc-venv`.

Log-on to one of the machines in your cluster, which should be one of the machines whose names you collected in step 1.
We'll designate this machine the *controller*. Create a venv and activate it

.. code-block:: shell

    virtualenv venv
    . venv/bin/activate

Populate it using ``pip`` with all the packages your experiments need plus everything ``epyc`` needs itself, which is:

.. code-block:: python

    six
    future
    ipython
    pyzmq
    ipyparallel
    dill
    pandas

Having set everything up to your satisfaction, freeze the venv:

.. code-block:: shell

    pip freeze >cluster-requirements.txt

(The name of the requirements file doesn't matter, but we'll need it later.) Now set up an IPython parallel profile too:

.. code-block:: shell

    ipython profile create --parallel epyc-cluster

(Again, the profile name doesn't matter.)

Now we need to do some editing. The profile we've created is actually a small set of files living in the
``~/.ipython/profile_epyc-cluster`` directory of your home directory. Open the file
``~/.ipython/profile_epyc-cluster/ipcontroller.py`` using your favourite editor, and add the following line to the
bottom of the file:

.. code-block:: python

    c.IPControllerApp.reuse_files = True

Now we need to create the *same* environment (venv and profile) on *all* the other machines in the cluster, which we
designate the *workers*. Firstly, for simplicity, let's store the list of machine names in a shell variable:

.. code-block:: shell

    WORKERS="lab1 lab2 lab3 lab4"

Here I have four machines imaginatively called ``lab1``, ``lab2``, ``lab3``, and ``lab4``. Firstly we copy the
requirements file for the venv to all these machines:

.. code-block:: shell

    for worker in $WORKERS; do
        scp cluster-requirements.txt $(WORKER):
    done

Now we need to log-in to all the machines and install the same venv and IPython profile, You can do this by hand,
by using ``ssh`` to log-in to each machine and then running:

.. code-block:: shell

    virtualenv venv
    . venv/bin/activate
    pip install -r cluster-requirements.txt
    ipython create profile --parallel epyc-cluster

Finally, make sure all the machines have the same profile:

.. code-block:: shell

    for worker in $WORKERS; do
        scp ~/.ipython/profile_epyc-cluster/ipcontroller.py $(WORKER):'~/.ipython/profile_epyc-cluster'
    done

The result of all this is that we have the same computational set-up on all our cluster's machines.

*Spinning-up the parallel infrastructure*. Now we want to start things up. For a multicore system we used the
``ipcluster`` tools to handle creating the controller and workers. That doesn't quite work for a cluster, because
we want slightly different software running on thje different machines: one controller, plus workers on all the
worker machines. So we have to set things up manually.

On the controller machine, run:

.. code-block:: shell

    ipcontroller --profile=epyc-cluster &

This starts a controller and puts it into background mode. A few lines of logging information will be generated,
which should all be innocuous.

In order to



Now we need to start computing engines on each worker machine. Let's assume for the sake of argument that each
of our worker machines has eight cores, so we want to start eight engines at each. Log-in to each of the worker
machines and run the following:

.. code-block:: shell

    for e in `seq 8`; do
        nohup ipengine --profile=epyc-cluster &
    done

If you like you


