.. _second-tutorial:

Second tutorial: parallel execution
===================================

``epyc``'s main utility comes from being able to run experiments, like those we defined in
the first tutorial and ran on a single machine, on multicore machines and clusters of machines.
In this tutorial we'll explain how ``epyc`` manages parallel machines.

(If you know about parallel computing, then it'll be enough for you to know that ``epyc`` creates
a task farm of experiments across multiple cores. If this didn't make sense, then you
should first read the :ref:`parallel processing concepts <concepts-parallel>`.)

.. include:: setup.rst

.. include:: clusterlab.rst

