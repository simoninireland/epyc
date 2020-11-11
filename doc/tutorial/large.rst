.. _large-datasets:

.. currentmodule :: epyc

Structuring larger datasets
---------------------------

A single result is a homogeneous collection of results from experimental runs.
Each "row" of the result set contains values for the *same* set of parameters,
experimental results, and metadata. Typically that means that all the results
in the result set were collected for the same experiment, or at least for
experiments with the same overall structure.

That might not be the case. You might want to collect together the results
of lots of *different* sorts of experiment that share a common theme. An example
of this might be where you have a model of a disease which you want to run
over different underlying models of human contacts described with different
combinations of parameters. Putting all these in the same result set would be
potentially quite confusing.

An ``epyc`` :class:`LabNotebook` can therefore store multiple separate result sets,
each with its own structure. You choose which result set to add results to
by selecting that result set as "current", and similarly can access the
results in the selected result set.

Each result set has a unique "tag" that identifies it within the notebook. ``epyc``
places no restrictions on tags, except that they must be strings: a meaningful
name would probably make sense.

When a notebook is first created, it has a single default result set ready to receive
results immediately.

.. code-block :: python

    from epyc import Experiment, LabNotebook, ResultSet

    nb = LabNotebook()
    print(len(nb.resultSets())

The default result set is named according to :attr:`LabNotebook.DEFAULT_RESULTSET`.

.. code-block :: python

    print(nb.resultSets())

We can add some results, assuming we have an experiment lying around:

.. code-block :: python

    e = MyExperiment()

    # first result
    params = dict(a=12, b='one')
    rc = e.set(params).run()
    nb.addResult(rc)

    # second result
    params['b']='two'
    rc = e.set(params).run()
    nb.addResult(rc)

These results will set the "shape" of the default result set.

You can create a new result set simply by providing a tag:

.. code-block :: python

    nb.addResultSet('my-first-results')

Adding the result set selects it and makes it current. We can then add some other
results from a different experiment, perhaps with a different set of parameters:

.. code-block :: python

    e = MyOtherExperiment()
    params = dict(a=12, c=55.67)
    rc = e.set(params).run()
    nb.addResult(rc)

We can check how many results we have:

.. code-block :: python

    print(nb.numberOfResults())

The result will be 1: the number of results in the current result set. If we select
the default result set instead, we'll see those 2 results instead:

.. code-block :: python

    nb.select(LabNotebook.DEFAULT_RESULTSET)
    print(nb.numberOfResults())

The two results sets are entirely separate and can be selected between as required.
They can also be given attributes that for example describe the circumstances
under which they were collected or the significance of the different parameters.
This kind of documentation metadata becomes more important datasets become 
larger, become more complicated, and are stored for longer. 





