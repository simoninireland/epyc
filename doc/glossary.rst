Glossary
========

.. currentmodule:: epyc
		   
.. glossary::

   results dict
      A dict structured according to a particular convention. The dict
      uses three top-level keys, defined by the Experiment class, for
      the parameter values of the experiment, the experimental
      results, and some metadata values. Each of these top-level keys
      themselves map to a hash of further values: for some
      experiments, the experimental results key may refer to a list of
      hashes.
      
      
