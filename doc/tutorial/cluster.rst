.. _clusterlab-experiment:

.. currentmodule:: epyc

Running experiments on a cluster
--------------------------------

Having set uo the cluster of whatever kind, we can now let ``epyc`` run experiments on it.
This involves using a :class:`ClusterLab`, which is simply a :class:`Lab` that runs
experiments remotely on a cluster rather than locally on the machine with the lab.

We create a :class:`ClusterLab` in the same way as :ref:`"ordinary" labs <lab-experiment>`:

.. code-block:: python

    clab = epyc.ClusterLab(profile = 'cluster',
                           notebook = epyc.JSONLabNotebook('our-work.json'))

The lab thus created will connect to the cluster described in the ``cluster`` profile
(which must already have been created and started).

A :class:`ClusterLab` behaves like :class:`Lab` in most respects: we can set a
parameter space, run a set of experiments at each point in the space, and so forth.
But they differ in one important respect. Runn ing an experiment in a :class:`Lab`
is a *synchronous* process: when you call :meth:`Lab.runExperiment` you wait until the
experiments finish before regaining control. That's fine for small cases, but what if
you're wanting top run a huge computation? -- many repetitionsd of experiments across
a large parameter space? That after all is the reason we want to do parallel computing:
to support large computations. It would be inconvenient to say the least if performing
such experiments locked-up a computer forr a long period.

:class:`ClusterLab` differs from :class:`Lab` by being *asynchronous*. When you
call :meth:`ClusterLab.runExperiment`, the experiments are submitted to the cluster in one
go *and control returns to your program*: the computation happens "in the background"
on the cluster.

So suppose we go back to our :ref:`example <simple-experiment>` of computing a curve.
This wasn't a great example for a sequential lab, and it's monumentally unrealistic
for parallel computation except as an example. We can set up the parameter space and run
them all in parallel using the same syntax as before:

.. code-block:: python

    clab['x'] = numpy.linspace(-2 * numpy.pi, 2 * numpy.pi)
    clab['y'] = numpy.linspace(-2 * numpy.pi, 2 * numpy.pi)

    clab.runExperiment(CurveExperiment())

Control will rreturn immediately, as the computation is spun-up on the cluster.

How can we tell when we're finished? There are three ways. The first is to make
the whole comp[utation synchronous by waiting for it to finish:

.. code-block:: python

    clab.wait()

This will lock-up your computer waiting for all the experiments to finish. That's
not very flexible. We can instead test whether the computations have finished:

.. code-block:: python

    clab.ready()

which wil return ``True`` when everything has finished. But that might take a long time,
and we might want to get results as they become available -- for example to plot them
partially. We can see what fraction of experiments are finished using:

.. code-block:: python

    clab.readyFraction()

which returns a number between 0 and 1 indicating how far along we are. 

As results come in, they're stored in the lab's notebook and can be retrieved
:ref:`as normal <results-experiment>`: as a list of dicts, as a ``DataFrame``, and
so forth. As long as :meth:`ClusterLab.ready` is returning ``False`` (and
:meth:`ClusterLab.readyFraction` is therefore returning less than 1), there are
still "pending" results that will be filled in later. Each call to one of these
"query" methods synchronises the notebook with the results computed on the
cluster.

In fact :class:`ClusterLab` has an additional trick up its sleeve, allowing
completely :ref:`disconnected operation <disconnected-usage>`. But that's another topic.
