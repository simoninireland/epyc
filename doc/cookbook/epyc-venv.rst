.. _epyc-venv:

.. currentmodule :: epyc

Reproducing experiments reliably
--------------------------------

**Problem**: Over time the versions numbers of different packages you
use change as the code is developed. You're worried this might affect
your code, either by breaking it or by changing its results somehow.

**Solution**: This is a real problem with computational
science. Fortunately it's fairly easy to address, at least at a simple
level.

Python includes a feature called **virtual environments** or
**venvs**. A venv is an installation of Python and its libraries
that's closed-off from any other installations you may have on your
machine. Essentially it takes the global installation of Python and
throws away anything that's not part of the core distribution. You can
"enter" the venv and install exactly those packages you want -- and
*only* those packages, and with specific version numbers if you like
-- secure in the knowledge that if the global environment, or another
venv, wants diffrent pacxkages and version numnbers they won't
interfere with you. You can also "freeze" your venv by grabbing a list
of packages and version numbers installed, and then install this
exact environment again later -- or indeed elsewhere, on another
machine.

Let's assume we want to *create* a venv that we've imaginatively named
``venv``. (You can pick any name you like.)  You create venvs from the
command line:

.. code-block:: sh

    python3 -m venv ./venv

We next need to *activate* the environment, making it the "current"
one that Python will use. This is again done from the command line:

.. code-block:: sh

    . venv/bin/activate

This alters the various include paths, command paths, and other
elements to make sure that, when you execute the Python interpreter or
any of the related tools, it runs the ones in the venv and not any
others.

We next need to *populate* the venv, that is, add the packages we
want. We do this using ``pip`` as normal:

.. code-block:: sh

    pip3 install ipython ipyparallel

.. note::

    In some installations, ``pip`` always refers to the ``pip`` tool
    of Python 2.7, while Python 3's tool is called ``pip3``. It never
    hurts when unsure to run ``pip3`` explicitly if you're working
    with Python 3. Similarly you may find there's a tool called
    ``python3`` or even ``python3.7`` in your venv.

Remember that because we've activated the venv, the Python tools we
run (including ``pip``) are those of the venv, and they affect the
venv: thus this call to ``pip`` will install the latest versions of
``ipython`` and ``ipyparallel`` just as we'd expect -- but into the
venv, not into the global environment. We can call ``pip`` repeatedly
to install all the packages we need. If we then run some Python code
(either interactively or as a script) from the shell in which we
activated the venv, it will use the packages we've installed. If we've
missed out a package that the code needs, then an exception will be
raised *even if the package is available globally*: only what's
explicitly loaded into the venv is available in the venv. Conversely
if we run the same code from a shell in which we haven't activated
this (or any other) venv, it will run in the packages installed
globally: *what happens in the venv stays in the venv*.

Suppose we now want to be able to reproduce this venv for later
use. We can use ``pip`` to *freeze* the state of the venv for us:

.. code-block:: sh

    pip freeze >requirements.txt

This generates a ``requirements.txt`` file including all the packages
and their version numbers: remember to execute this command from the
shell in which we activated the venv. If we later want to reproduce
this environment, so we're sure of the package versions our code will
use, we can create another venv that uses this file to reproduce the
frozen venv:

.. code-block:: sh

    python3 -m venv ./venv2
    . venv2/bin/activate
    pip install -r requirements.txt

This new venv now has exactly the structure of the old one, meaning we
can move the computational environment across machines.

.. warning::

    This sometimes doesn't work as well as it might: Python's
    requirements files aren't very well structured, not all packages
    (or all package versions) are available on all operating systems,
    Python on OS X has some unique packages, `Anaconda
    <https://www.anaconda.com/>`_ includes a huge set by default, and
    so forth. But at least you get start from a place where the
    environment is well-known.

    A handy debugging strategy is to run ``pip install -r
    requirements.txt`` and, if it fails, delete the offending line
    from ``requirements.txt`` and try again. If you remove a package
    that's needed by another, then a compatible version should be
    found by ``pip`` -- but possibly not the one you were using
    originally. This doesn't often cause problems in real life.
