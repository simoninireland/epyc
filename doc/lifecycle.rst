.. _lifecycle:

.. currentmodule :: epyc

The lifecycle of an experiment
==============================

An ``epyc`` experiment goes through the following lifecycle stages:

1. **Creation and intitialisation**. The experiment is first created.
2. **Configuration**. The experiment is configured ready to perform one or more experimental runs
   with a given set of parameters.
3. **Setup**. The experiment is made ready for an experimental run.
4. **Execution**. The experiment performs a single experimental run.
5. **Teardown**. The experiment is cleaned up after the experimental run.
6. **Deconfiguration**. The experiment is tidied up ready to receive new parameters.

Step 1 happens once, when the experiment is created. Steps 2 and 6
happen whenever the :term:`experimental parameters` of the experiment
are changed, and are the place to configure any data that will be used
for all experimental runs with these parameters.  Steps 3, 4, and 5
happen in sequence for every experimental run with a given parameter
set. Steps 3 and 5 are the place to set up and tear down data needed
for a single run. Step 4 is the place to describe what happens in a
single experimental run, using the parameter-dependent (configured)
and run-dependent (set up) data from steps 2 and 3.

.. note::

   The difference between confiuration and set-up is that configuration happens
   when parameters change while set-up happens before every individual run.

Each of these stages is encapsulated in methods within the :class:`Experiment`
class:

1. **Creation and intitialisation**. The constructor of each :class:`Experiment`
   sub-class. Be careful to always call the base constructor to perform initialisation properly.
2. **Configuration**. When parameters are first set using :meth:`Experiment.set` the
   :meth:`Experiment.configure` method is called to perform whatever configuration is
   required. Override this method to add extended configuration steps, for example
   creating object that depend on the parameters.
3. **Setup**. When the experiment is run by calling :meth:`Experiment.run` it first calls
   :meth:`Experiment.setUp` to perform any setup for this one run. This lets any
   initialisation happen.
4. **Execution**. The experiment then calls :meth:`Experiment.do` to perform the main
   task of the experiment, returning the experimental results for this run.
5. **Teardown**: The experiment then calls :meth:`Experiment.tearDown` method to tear-down any
   structures created by :meth:`Experiment.setUp` that are no longer required.
6. **Deconfigration**. If new parameters are set, :meth:`Experiment.deconfigure` is first called to
   dispose of any configuration that was done for the previous parameters, and then
   :meth:`Experiment.configure` is called as in step 2.

Notice that setting new parameters using :meth:`Experiment.set` will trigger a call to
:meth:`Experiment.deconfigure` (if the experiment had already been configured) and then
a call to :meth:`Experiment.configure` to perform any configuration.

Similarly, running the experiment by calling :meth:`Experiment.run` will call :meth:`Experiment.setUp`,
:meth:`Experiment.do`, and :meth:`Experiment.tearDown`, in that order.

There are a few things to notice about this process. Firstly, there are two sets of "bracketing" methods
that are called for each parameter change (:meth:`Experiment.configure` and :meth:`Experiment.deconfigure`)
and for each individual run (:meth:`Experiment.setUp` and :meth:`Experiment.tearDown`).
These methods can be used to create a predictable environment for the :meth:`Experiment.do` to operate in.

.. note::

   If you write unit tests with your code -- and you should, of course -- then :meth:`Experiment.setUp` and
   :meth:`Experiment.tearDown` have essentially the same purpose as ``unittest.TestCase.setUp`` and
   ``unittest.TestCase.tearDown``.)

Secondly, it is often the case that changing parameters requires creating complex data structures
which can then be reused for every experimental run with these parameters.
Separating parameter changes from individual runs is an opportunity to separate these
phases and minimise re-doing expensive construction operations.
For example, you might create a complex random dataset in :meth:`Experiment.configure` using some parameter
values, and then create a fresh copy for each run in :meth:`Experiment.setUp` so as not to expensively
re-create the dataset at every run.

Thirdly, experiments should be written so that their main body in :meth:`Experiment.do` can be run multiple times
for a given set of parameter values. This gives maximum flexibility in letting experiments be composed together,
repeated, and so forth. By separating out the different phases between the five methods described above, hopefully
you'll avoid any unexpected interactions.

Finally, whenever you override any of these methods (apart from :meth:`Experiment.do`), be sure to call the
base method first. There are some global steps that need to happen for all experiments.
