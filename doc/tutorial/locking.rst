.. _locking-resultsets:

.. currentmodule :: epyc

Locking result sets
-------------------

If you've just burned hundred of core-hours on significant experiments,
you want to be careful of the results! The persistent notebooks try
to ensure that results obtained are committed to persistent storage,
which you can always force with a call to :meth:`LabNotebook.commit`.

Because notebooks can store the results of different experimental configurations,
you may find yourself managing several result sets under different
tags. There's a risk that you'll accidentally use one result set when you
meant to use another one, for example by not calling :meth:`LabNotebook.select`
to select the correct one.

The risk of this can be minimised by locking a result set once all its experiments
have been completed. We might re-write the experiments we did above to lock
each result set once the experiments are all done.

.. code-block :: python

    # perform some more experiments
    nb.addResultSet('third-experiments')
    lab['a'] = 12
    lab['b'] = range(1000)
    e = MyThirdExperiment()
    lab.runExperiment(e)

    # wait for the results to complete ... time passes ...
    lab.wait()

    # the results are in, lock and commit
    nb.current().finish()
    nb.commit()

The :meth:`ResultSet.finish` method does two things. It cancels any pending results
still missing there won't be any of these in this example, because of the call
to :meth:`ClusterLab.wait`), and then locks the result set against any further updates.
This locking is persistent, so re-loading the notebook later will still leave
this result set locked, in perpetuity.

