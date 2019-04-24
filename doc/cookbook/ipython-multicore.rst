.. _ipython-multicore:

.. currentmodule:: epyc

Improving performance using a multicore machine
-----------------------------------------------

*Problem*: You want to make use of your multicore machine to run experiments in parallel.

*Solution*: A multicore machine has several independent processors (or "cores") that can run programs
simultaneously. IPython comes with a library for parallel computying, ``ipyparallel``. ``epyc`` can use this library
to get portable parallelism on multicore architectures.

``ipyparallel`` offers a multi-engine or multi-worker view of concurrency. A number of engine processes are set up
which request work from a single controller. Clients -- processes having work to do -- submit jobs to this controller,
which then farms them out to the engines as they become free.

It's important to understand how parallelism is manifested in ``epyc``. Each single experiment is coded as sequential
program: it's just a piece of Python code that, when run, takes a certain amount of time to get its results.
Parallelism in ``epyc`` comes from a lab running several experiments concurrently, possibly at different points in
the parameter space being explored. Each individual experiment still runs sequentially, and therefore doesn't get
any faster -- but instead of running the experiments one after the other, on a machine with eight cores we'll try to
run eight experiments simultaneously.

Getting improved performance involves three steps:

1. Setting up the compute environment

2. Running the ``ipyparallel`` infrastructure

3. Setting up a lab that will submit to this infrastructure

.. tip::

    All the following steps are best done in a predictable, reproducible environment: see :ref:`epyc-venv` for
    details of how to set up such an environment.

*Setting up the compute environment*. What packages do we need? Whatever our code requires, of course, plus
``epyc``'s requiremnets, which include the following packages:

.. code-block:: python

    six
    future
    ipython
    pyzmq
    ipyparallel
    dill
    pandas

You can simply install these packages using ``pip`` as normal. If you want to be exceptionally conservative and use
exactly the packages that the current version of ``epyc`` uses, you can do the following commands in a shell:

.. code-block:: shell

    wget https://raw.githubusercontent.com/simoninireland/epyc/master/requirements.txt
    pip install -r requirements.txt

(If you're running in a venv, make sure the shell you run these commands from has the venv activated.)

*Spinning-up the parallel infrastructure*. We now use IPython to create the necessary infrastructure of engines  and
a controller for us to submit jobs to. This comes in two stages: creating an IPython parallel profile, and then
spinning-up the processes.

IPython uses profiles a little like venvs, to describe a computational set-up. Let's create one that includes the
capabilities for parallel code. We'll call it "epyc-compute" for no particularly good rerason: you can choose any
appropriate name:

.. code-block:: shell

    ipython profile create --parallel epyc-compute

We can now spin-up a controller and some workers. But how many engines? If you have a machine with eight cores it
might make sense to have eight engines, so we can reasonably expect them to spread across all the available cores.
If you were using the machine for something else as well as computing, you might want fewer engines to leave some
cores free. It doesn't make any sense to have *more* engines than cores, though.

.. tip::

    If you don't know how many cores your machine has, but you're running Linux, you can
    ask the machine itself:

    .. code-block:: shell

        grep -c processor /proc/cpuinfo

    which queries the kernel as to how many processor cores are available.

Let's say we decide we have eight cores. You can instruct IPython to spin-up a controller and eight engines:

.. code-block:: shell

    ipcluster start --profile=epyc-worker --n=8

This will run the controller in the foreground: killing this process will kill all the engines as well, letting us
exit the infrastructure cleanly.

*Running the experiments*. The final step is to load all the code we need to run the experiments, and set them
running with the right parameters. Start up a new shell and activate the venv if you're using one. Rather than creating a normal
:class:`Lab`, we'll instead create a :class:`ClusterLab` and pass it the information it needs to access to
compute cluster we've just set up.

.. code-block:: python

    include epyc

    nb = epyc.LabNotebook()
    lab = epyc.ClusterLab(nb, cluster = `epyc-compute`)

Remember that this ``lab`` object is a front-end to a computing infrastructure that has eight engines. The engines are
just Python processes that we're going to pass code to for them to run. We therefore need to make sure that
the engines' Python interpreters have imported the packages the code will need. Suppose your experiment needs ``numpy``
and ``mpmath``. We instruct the cores to load these packages. (They'll do this from their own Python environment, of
course, which is why we said to run them *and* lab code in the *same* venv. Horrendous confusion will otherwise ensue.)

.. code-block:: python

    with lab.sync_imports():
        import numpy
        import mpmath

This code will import the packages we need on all the engines simultaneously. Finally we can run our experiment:

.. code-block:: python

    # set up the parameter space
    lab['x'] = numpy.linspace(0.0, 1.0, num = 100, endpoint = True)

    # run an experiment
    lab.runExperiment(MySimpleExpriment()

In this case we've chosen to use a simple :class:`LabNotebook` for the results: you could use a persistent one instead,
which probably makes more sense. The parameter space and experiment are up to you too. The code will block until the
experiments have all completed: under the set-up we created above, we'll run experiments at eight points in the
parameter space simultaneously, starting new ones as old ones finish. All being well it should take considerably less
time than the same experiments would take on a single core using a simple lab.

.. tip::

    How much less time? Well that's a tricky question. In principle a machine with ** cores and *n* engines will take
    1/*n* times as long as a machine with one core would take for the same workload, referred to as a "speed-up of *n*".

    In practice several factors conspire to slow things down. Different experimental runs may take different amounts of time;
    we might run out of work early, so not all the engines are kept busy; the machine will be running other things as well
    as our computations; and there are always overheads involved
    in setting up and housekeeping the parallel activities. Having said all this, ``ipyparallel`` is a pretty
    efficient parallel computing harness, so you should see speed-ups in the range (*n* - 1) or so.

*Troubleshooting*. By far the most common problem with using compute clusters like this is not to import the correct
modules everywhere. This will manifest itself with a code-not-found exception of some kind. The easiest solution
is to run everything in the *same* venv, and to make sure that you import all the packages that your experimental
code needs using :meth:ClusterLab.sync_imports`.
