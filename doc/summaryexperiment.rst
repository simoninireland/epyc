:class:`SummaryExperiment`: Statistical summaries of experiments
================================================================

.. currentmodule :: epyc
   
.. autoclass :: SummaryExperiment
   :show-inheritance:

		
Extra metadata elements in the results dict
-------------------------------------------

Summarisation removes the raw results of the various experiments from
the results dict and replaces them with summary values. Each
summarised value is replaced by five derived values for the mean,
median, variance, and extrema, with standard suffices.

.. autoattribute :: SummaryExperiment.MEAN_SUFFIX
   :annotation:      

.. autoattribute :: SummaryExperiment.MEDIAN_SUFFIX
   :annotation:      

.. autoattribute :: SummaryExperiment.VARIANCE_SUFFIX
   :annotation:      

.. autoattribute :: SummaryExperiment.MIN_SUFFIX
   :annotation:      

.. autoattribute :: SummaryExperiment.MAX_SUFFIX
   :annotation:      

The metadata also enumerates the number of experiments performed,
the number summarised (since unsuccessful experiments are omitted),
and any exceptions raised.

.. autoattribute :: SummaryExperiment.UNDERLYING_RESULTS
   :annotation:      

.. autoattribute :: SummaryExperiment.UNDERLYING_SUCCESSFUL_RESULTS
   :annotation:      

		   
Running the experiment
----------------------

.. automethod :: SummaryExperiment.do

				   
Creating and changing the summary statistics
--------------------------------------------

.. automethod :: SummaryExperiment.summarise

