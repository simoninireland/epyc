:class:`SummaryExperiment`: Statistical summaries of experiments
================================================================

.. currentmodule:: epyc
   
.. autoclass:: SummaryExperiment


Creating a summary
------------------

.. automethod:: SummaryExperiment.__init__

		
Extra metadata elements in the results dict
-------------------------------------------

Summarisation removes the raw results of the various experiments from
the results dict and replaces them with summary values. Each
summarised value is replaces by three derived values for the mean,
median, and variance, with standard suffices.

.. autoattribute:: SummaryExperiment.MEAN_SUFFIX
   :annotation:      

.. autoattribute:: SummaryExperiment.MEDIAN_SUFFIX
   :annotation:      

.. autoattribute:: SummaryExperiment.VARIANCE_SUFFIX
   :annotation:      

The metadata also enumerates the number of experiments performed and
the number summarised, since unsuccessful experiments are omitted.

.. autoattribute:: SummaryExperiment.UNDERLYING_RESULTS
   :annotation:      

.. autoattribute:: SummaryExperiment.UNDERLYING_SUCCESSFUL_RESULTS
   :annotation:      

		   
Running the experiment
----------------------

.. automethod:: SummaryExperiment.do
