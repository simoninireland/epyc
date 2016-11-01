Glossary
========

.. currentmodule:: epyc
		   
.. glossary::

   experiment
      A computational experiment, inheriting from :class:`Experiment`.
      Experiments are run at a point in a multi-dimensional parameter
      space, and should be designed to be repeatable. 

   lab
      A computational laboratory co-ordinating the execution of
      multiple experiments, inheriting from :class:`Lab`.

   notebook
      An immutable and often persistent store experimental results and
      metadata, inheriting from :class:`LabNotebook`.
      
   results dict
      A dict structured according to a particular convention. The dict
      uses three top-level keys, defined by the Experiment class, for
      the parameter values of the experiment, the experimental
      results, and some metadata values. Each of these top-level keys
      themselves map to a hash of further values: for some
      experiments, the experimental results key may refer to a list of
      hashes.

   experiment combinators
      Experiments that wrap-up other, underlying experiments and
      perform them in some way, perhaps repeating them or summarising
      or re-writing their results. They allow common experimental
      patterns to be coded.
      
