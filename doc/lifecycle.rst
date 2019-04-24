.. _lifecycle:

.. currentmodule:: epyc

The lifecycle of an experiment
==============================

An ``epyc`` experiment goes through the following lifecycle stages:

1. **Creation and intitialisation**. Experiment should call the base class constructor from
   :class:`Experiment` to make sure global initialisation happens.

2. **Configuration**. When parameters are first set using :meth:`Experiment.set` the
   :meth:`Experiment.configure` method is called to perform whatever configuration is
   required. Override this method to add extended configuration steps, for example
   creating object that depend on the parameters.

3. **Setup**. When the experiment is run (:meth:`Experiment.run`) it first calls
   :meth:`Experiment.setUp` to perform any setup for this one run. This lets any
   initialisation happen.

4. **Execution**. The experiment then calls :meth:`Experiment.do` to perform the main
   task of the experiment, returning the experimental results.

5. **Teardown**: The :meth:`Experiment.tearDown` method is then called to tear-down any
   structures no longwr required.

6. If the experiment is run again, steps 3--5 happen again.

7. If new parameters are set, :meth:`Experiment.deconfigure` is first called to tear-down
   any configuration that was done for the previous parameters, and then :meth:`Experiment.configure`
   is called as in step 2.

There are a few things to notice about this process. Firstly, each time an experiment is run it calls the method
sequence :meth:`Experiment.setUp` -- :meth:`Experiment.do` -- :meth:`Experiment.tearDown`. The bracketing methods
can therefore be used to create a predictable environment for the :meth:`Experiment.do` to operate in. (If you
write unit tests with your code -- and you should, of course -- then :meth:`Experiment.setUp` and
:meth:`Experiment.tearDown` perform the same functions as ``unittest.TestCase.setUp`` and
``unittest.TestCase.tearDown``.

Secondly, when a new set of parameters is provided, an experiment calls :meth:`Experiment.deconfigure` (of there
were parameters previously set) and then :meth:`Experiment.configure` to perform any parameter-specific
configuration. This lets you write potentially expensive code that needs to be done for new parameters here,
and keep per-run setup code to a minimum.

(As an example, you might create a complex random dataset in :meth:`Experiment.configure` using some parameter
values, and then create a fresh copy for each run in :meth:`Experiment.setUp` so as not to re-create the dataset at every
run.)

Thirdly, experiments should be written so that their main body in :meth:`Experiment.do` can be run multiple times
for a given set of parameter values. This gives maximum flexibility in letting experiments be composed together,
repeated, and so forth. By separating out the different phases between the five methods described above, hopefully
you'll avoid any unexpected interactions.

Finally, whenever you override any of these methods (apart from :meth:`Experiment.do`), be sure to call the
base method first. There are some global steps that need to happen for all experiments.



