.. _resultset-metadata:

.. currentmodule:: epyc

Making data archives
--------------------

**Problem**: Having expended a lot of time (both your own and your computers')
on producing a dataset in a notebook, you want to be able to store it and share
it over a long period.

**Solution**: This is a perennial problem with computational science: how do we make
data readable, and keep it that way? Even more than code (which we discussed
under :ref:`epyc-venv`), data suffers from "bit rot" and becomes unreadable,
both in technical and semantic terms.

The technical part -- a file that's in an outdated format -- is the easier problem
to deal with. We can use a format that's already survived the test of time,
that has widespread support, and that -- although it eventually *will* go out
of date -- will have emough commitment that it'll be possible to convert and
upgrade it. HDF5, as used by the :class:`HDF5LabNotebook`, meets these criteria
well, and can be accessed natively by ``epyc``.

Note that ``epyc`` also records the class names of experiments in their results.
This is only a guide, of course: there's nothing that automatically identifies where
the code of a class is stored, or which version was used. It's possible to address
these issues as part of dataset semantics, though.

The semantic problem requires that we maintain an understanding of what each field
in a dataset *means*. At a trivial level, sensible field names help, as do free-text
descriptions of how and why a datset was collected. This metadata is all stored
within a persistent result set or notebook, and can be accessed when the notebook
is re-loaded or used within some other tool.

One can be even more structured. Each parameter and result field in a result set (and
each metadata field, for that matter) will presumably have a particular purpose and
likely some units. We can use attributes to store this metadata too:

.. code-block:: python

    from epyc import HDF5LabNotebook

    # load the notebook and give it a new description
    with HDF5LabNotebook('my-important-dataset.h5') as nb:
	# set the description
	nb.setDescription('A notebook I want to understand later')

	# select the result set we want to annotate with metadata
	rs = nb.select('first-experiment')
	rs.setDescription('Some physics stuff')

	# create attributes for each parameter and result
	rs[MyExperiment.VELOCITY] = 'Velocity of particle (ms^-1)'
	rs[MyExperiment.MASS] = 'Mass of particle (g)'
	rs[MyExperiment.NPARTICLES] = 'Number of particls (number)'
	rs[MyExperiment.DENSITY] = 'Final particle density (m^-2)'

	# lock the result set against further updates
	rs.finish()

We've assumed we have a class ``MyExperiment`` that defines field names for its
parameter and result fields. For each of these we create an attribute of the result
set holding a text description and units. Now, when sometime later we examine the notebook,
we'll have at least some idea of what's what. Admittedly that metadata isn't machine-readable
to allow a program to (for example) work out that masses are measured in grams: that
would require a far more sophisticated system using ontologies to describe the structure
of information. But it's a start to have the information recorded in a human-readable form,
closely associated with the data.

In particular application domains it may also be worth adhering to specific standards for metadata.
The UK Digital Curation Centre maintains a `list <https://www.dcc.ac.uk/guidance/standards/metadata/list>`_
that may be useful.

Finally, we called :meth:`ResultSet.finish` to finish and lock the result set. This
will (hopefully) prevent accidental corruption, and will also tidy up the final
file by cancelling any submitted-but-not-completed pending results. (Any such results
will still be recorded in the dataset for audit purposes.)
