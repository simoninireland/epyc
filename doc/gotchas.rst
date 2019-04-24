.. _gotchas:

.. currentmodule:: epyc

Tripping hazards
================

While ``epydemic`` tried hard to hide the details of parallel and distributed computing in Python, there are some
"gotchas" that seem to be unavoidable. (At least, we haven't found robust workarounds for them yet.) In this
chapter we'll point out the ones we've most often tripped over.


Experiments defined in programs or Jupyter notebooks can't use their own classname
----------------------------------------------------------------------------------

If you define an :class:`Experiment` either in a Jupyter notebook or in a standalone program, you may
write code something like this:

.. code-block:: python

    class MyExperiment(epyc.Experiment):

        def __init__( self ):
            super(MyExperiment, self).__init__()
            # your initialisation code here

        def setUp( self, params ):
            super(MyExperiment, self).setUp(params)
            # your setup code here

        def do( self, params ):
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

There are three solutions to this problem -- well two solutions, one of which has two variants.

The easiest way is to replace code like this:

.. code-block:: python

    def setUp( self, params ):
        super(MyExperiment, self).setUp(params)
        # your setup code here

with code like this:

.. code-block:: python

    def setUp( self, params ):
        epyc.Experiment.setUp(self, params)
        # your setup code here

In other words, explicitly call the base class method, passing ``self`` to it as its first parameter. You'll notice
that this removes all mentionm of ``MyExperiment``, which is what was causing the problem. The disadvantage of this
approach is that you might find this style of code harder to read, which is always a bad idea.

The second solution is to make ``MyExperiment`` available to the cluster. The first variant (if you don't have very much
code) is to put the class definition into its own file (for example ``myexperiment.py``) and then import it both
into your program (or notebook) and into the cluster itself:

.. code-block:: python

    import epyc
    import myexperiment

    lab = epyc.ClusterLab()
    with lab.sync_imports():
        import myexperiment

    lab['x'] = range(1000)
    e = myexperiment.MyExperiment()
    lab.runExperiment(e)

You'll also need to create an empty file ``__init__.py`` to indicate to Python that it's OK to import files in this
directory.

The second variant of this solution (if you have  a lot of code, for example a set of experiments) is to put
``myExperiment`` into its own "proper" module and import it as above. This has the advantage of separating your
experiment-defining code from your experiment-running code, at the cost of a more complicated source file structure.

If you're using Jupyter notebooks, the second solution (in either variant) has the enormous *disadvantage* of taking
your experiment out of your notebook and putting it in a separate source file that your readers might not be able
to get at. For Jupyter, then, it's probably better to use the first solution, accepting the small loss of readability
as an unfortunate side effect.




