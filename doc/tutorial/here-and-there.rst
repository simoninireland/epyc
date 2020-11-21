.. _jupyter-here-and-there:

Sharing code between notebooks and engines
------------------------------------------

Of course if you use Jupyter as your primary coding platform, you'll
probably define experiments in the notebook too. This will unfortunately
immediately introduce you to one of the issues with distributed computation
in Python.

Here's an example. Suppose you define an experiment in a notebook, something like this:

.. code-block :: python

    from epyc import Experiment

    class MyExperiment(Experiment):

        def __init__(self):
            super(MyExperiment, self).__init__()
            # your initialisation code here

        def setUp(self, params):
            super(MyExperiment, self).setUp(params)
            # your setup code here

        def do(self, params):
            # whatever your experiment does

Pretty obvious, yes? And it works fine when you run it locally. Then, when you try to run it in on a cluster,
you create your experiment and submit it with :meth:`ClusterLab.runExperiment`, but all the instances fail with
an error complaining about there being no such class as ``MyExperiment``.

What's happening is that ``epyc`` is creating an instance of your class in your notebook (or program) where
``MyExperiment`` is known (so the call in ``__init__()`` works fine). Then it's passing objects (instances of
this class) over to the cluster, where ``MyExperiment`` *isn't* known. When the cluster calls :meth:`Experiment.setUp`
as part of the experiment's lifecycle, it goes looking for ``MyExperiment`` -- and fails, even though it does actually
have all the code it needs. This happens because of the way Python dynamically looks for code at run-time, which
is often a useful feature but in this case pulls things over.

To summarise, the problem is that code you define *here* (in the notebook) isn't immediately
available *there* (in the engines running the experiments): it has to be transferred there.
And the easiest way to do that is to make sure that all classes defined *here* are also
defined *there* as a matter of course.

To do this we make use of an under-used feature of Jupyter, the *cell magic*. These are
annotations placed on cells that let you control the code that executes the cell itself.
So rather than a Python code cell being executed by the notebook's default mechanism, you
can insert code that provides a new mechanism. In this case we want to have a cell execute
both *here* and *there*, so that the class is defined on notebook and engine.

.. important ::

    If you haven't taken the heart the advice about :ref:`epyc-venv`, now would be
    a really good time to do so. Create a venv for both the notebook and the engines:
    the venv at the engine side doesn't need Jupyter, but it mostly does no harm to
    use the same ``requirements.txt`` file on both sides.

The cell magic we need uses the follwing code, so put it into a cell and execute it:

.. code-block :: python

    # from https://nbviewer.jupyter.org/gist/minrk/4470122
    def pxlocal(line, cell):
        ip = get_ipython()
        ip.run_cell_magic("px", line, cell)
        ip.run_cell(cell)
    get_ipython().register_magic_function(pxlocal, "cell")    

This defines a new cell magic, ``%%pxlocal``. The built-in cell magic ``%%px`` runs
a cell on a set of engines. ``%%pxlocal`` runs a cell *both* on the engines
and locally (in the notebook). If you decorate your experiment classes this way, then they're
defined *here* and *there* as required:

.. code-block :: python

    %%pxlocal

    class MyExperiment(Experiment):

        def __init__(self):
            super(MyExperiment, self).__init__()
            # your initialisation code here

        def setUp(self, params):
            super(MyExperiment, self).setUp(params)
            # your setup code here

        def do(self, params):
            # whatever your experiment does

Now when you submit your experiments they will function as required.

.. important ::

    You only need to use ``%%pxlocal`` for cells in which you're defining classes.
    When you're running the experiments all the code runs notebook-side only, and ``epyc`` handles
    passing the necessary objects around the network.









