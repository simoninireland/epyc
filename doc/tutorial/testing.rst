.. testing-experiment:

.. currentmodule:: epyc

Testing the experiment
----------------------

Good development practice demands that we now test the experiment before running it in anger.
Usually this would involve writing unit tests within a framework provided by Python's ``unittest``
library, but that's beyond the scope of this tutorial: we'll simply run the experiment at a point
for which we know the answer:

.. code-block:: python

    # set up the test
    params = dict()
    params['x'] = 0
    params['y'] = 0
    res = numpy.sin(numpy.sqrt(x**2 + y**2))   # so we know the answer

    # run the experiment
    e = CurveExperiment()
    rc = e.set(params).run()
    print(rc[epyc.RESULTS]['result'] == res)

The result should be ``True``. Don't worry about how we've accessed the result: that'll become
clear in a minute.



