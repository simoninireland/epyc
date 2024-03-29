Glossary
========

.. currentmodule:: epyc

.. glossary::

   experiment
      A computational experiment, inheriting from :class:`Experiment`.
      Experiments are run at a point in a multi-dimensional parameter
      space, and should be designed to be repeatable.

   experiment combinators
      Experiments that wrap-up other, underlying experiments and
      perform them in some way, perhaps repeating them or summarising
      or re-writing their results. They allow common experimental
      patterns to be coded.

   experimental configuration
      A list of pairs of an experiment and the parameters at which it
      will be run, created according to an :term:`experimental design`.

   experimental design
      The way in which a set of parameters is converted into points
      at which experiments are run.

   experimental parameters
      The values used to position an individual experimental run in
      the "space" of all experiments. Each experiment has its own
      parameters, which it can use to configure itself and perform
      set-up (see :ref:`lifecycle`).

   experimental results
      The collection of values returned by an experimental run.

   lab
      A computational laboratory co-ordinating the execution of
      multiple experiments, inheriting from :class:`Lab`.

   metadata
      Additional information about an experiment, returned as part of
      a :term:`results dict`.

   notebook
      An immutable and often persistent store experimental results and
      metadata, inheriting from :class:`LabNotebook`.

   parameter space
      The set of :term:`experimental parameters` at which experiments
      will be run. The parameter space is defined by a :class:`Design`,

   result set
      A collection of results within a :term:`notebook`, inheriting
      from :class:`ResultSet`. Result sets can be created, deleted,
      and added to by running new experiments -- but can't have their
      contents changed.

   results dict
      A dict structured according to a particular convention. The dict
      uses three top-level keys, defined by the Experiment class, for
      the parameter values of the experiment, the experimental
      results, and some metadata values. Each of these top-level keys
      themselves map to a hash of further values: for some
      experiments, the experimental results key may refer to a list of
      hashes.
