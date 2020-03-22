.. _unicore-parallel:

.. currentmodule:: epyc

Setting up a machine with a single core
=======================================

You might ask why you'd do this: isn't a single-core machine useless for parallel processing? Well, yes ... and
no, it's the same basic architecture as for a :ref:`multicore machine <multicore-parallel>`, so it's useful
to understand how things go together.

The first thing we need to do is create a "profile", which is just a small description of how
we want the cluster to behave. Creating a profile requires one command:

.. code-block:: sh

    ipython profile create --parallel cluster

This creates a profile called ``cluster`` -- you can choose any name you like for yours. Profiles let
us run multiple clusters (should we want to), each with a different name.

We can now start our compute cluster using this profile:

.. code-block:: sh

    ipcluster start --profile=cluster

That's it! (If you used a different name for your profile, of course, use that instead of ``cluster`` above.)
You'll see some debugging information streaming past, which indicates that the cluster has
started and is ready for use.

Unsurprisingly, if you want to halt the cluster, you execute:

.. code-block:: sh

    ipcluster stop --profile=cluster

You need to provide the profile name to make sure ``epyc`` stops the right cluster.




