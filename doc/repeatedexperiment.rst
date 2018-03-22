:class:`RepeatedExperiment`: Repeating an experiment experiment
===============================================================

.. currentmodule:: epyc
   
.. autoclass:: RepeatedExperiment
   :show-inheritance:


Performing repetitions
----------------------

.. automethod:: RepeatedExperiment.__init__

.. automethod:: RepeatedExperiment.repetitions


Extra metadata elements in the results dict
-------------------------------------------

.. autoattribute:: RepeatedExperiment.REPETITIONS
   :annotation:      

      
Running the experiment
----------------------

.. automethod:: RepeatedExperiment.do
