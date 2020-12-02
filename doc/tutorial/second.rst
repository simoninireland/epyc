.. _second-tutorial:

Second tutorial: Parallel execution
===================================

``epyc``'s main utility comes from being able to run experiments, like those we defined in
the first tutorial and ran on a single machine, on multicore machines and clusters of machines.
In this tutorial we'll explain how ``epyc`` manages parallel machines.

(If you know about parallel computing, then it'll be enough for you to know that ``epyc`` creates
a task farm of experiments across multiple cores. If this didn't make sense, then you
should first read :ref:`concepts-parallel`.)


Two ways to get parallelism
---------------------------

``epyc`` arranges the execution of experiments around the :class:`Lab` class, which handles
the execution of experiments across a parameter space. The default :class:`Lab` executes
experiments sequentially.

But what if you have more than one core? -- very common on modern workstations. Or if
you have access to a cluster of machines? Then ``epyc`` can make use of these resources
with *no change to your experiment code*.

If you have a multicore machine, the easiest way to use it with ``epyc`` is to replace
the :class:`Lab` managing the experiments with a :class:`ParallelLab` to get
*local parallelism*. This will execute
experiments in parallel using the available cores. (You can limit the number of cores
used if you want to.) For example:

.. code-block :: python

    from epyc import ParallelLab, HDF5LabNotebook

    nb = HF5LabNotebook('mydata.h5', create=True)
    lab = ParallelLab(nb, cores=-1)                 # leave one core free

    e = MyExperiment()
    lab['first'] = range(1, 1000)
    lab.runExperiment(e)

On a machine with, say, 16 cores, this will use 15 of the cores to run experiments
and return when they're all finished.

If you have a cluster, things are a little more complicated as you need to set up
some extra software to manage the cluster for you. Once that's done, though, accessing
the cluster from, ``epyc`` is largely identical to accessing local parallelism.

.. include :: setup.rst

.. include :: cluster.rst

.. include :: cluster-problems.rst


Clusters *versus* local parallelism
-----------------------------------

You probably noticed that, if you have a single multicore workstation, there are two ways
to let ``epyc`` use it:

- a :class:`ParallelLab`; or
- a :class:`ClusterLab` that happens to only run engines locally.

There are pros and cons to each approach. For the :class:`ParallelLab` we have:

- it's very simple to start, requiring no extra software to manage;
- you only get (at most) as many cores as you have on your local machine; and
- experiments run *synchronously*, meaning the program that runs them is locked
  out until they complete (this is especially inconvenient when using
  :ref:`Jupyter <fourth-tutorial>`).

For the :class:`ClusterLab`:

- you need to set up the cluster outside ``epyc``; but
- experiments run *asynchronously*, meaning you can :ref:`get on with other things <disconnected-usage>`; and
- you can use all the cores of all the machines you can get access to.

As a rule of thumb, a suite of experiments likely to take hours or days will be
better run on a cluster; shorter campaigns can use local parallelism to get a useful
speed-up.


