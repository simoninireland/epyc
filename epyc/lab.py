# Simulation "lab" experiment management, sequential version
#
# Copyright (C) 2016--2020 Simon Dobson
#
# This file is part of epyc, experiment management in Python.
#
# epyc is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# epyc is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with epyc. If not, see <http://www.gnu.org/licenses/gpl.html>.

from epyc import LabNotebook, Experiment, Design, FactorialDesign, ResultsDict, ExperimentalConfiguration
from pandas import DataFrame                                   # type: ignore
from typing import Dict, List, Tuple, Any


class Lab(object):
    """A laboratory for computational experiments.

    A :class:`Lab` conducts an experiment at different points in a
    multi-dimensional parameter space.  The default performs all the
    experiments locally; sub-classes exist to perform remote parallel
    experiments.

    A :class:`Lab` stores its result in a notebook, an instance of
    :class:`LabNotebook`.  By default the base :class:`Lab` class uses
    an in-memory notebook, essentially just a dict; sub-classes use
    persistent notebooks to manage larger sets of experiments.

    Each lab has an associated :class:`Design` that turns a set of
    parameter ranges into a set of individual "points" of the parameter
    space at which to perform actual experiments. The default is to
    use a :class:`FactorialDesign` that performs an experiment for every
    combination of parameter values. This might be a *lot* of experiments,
    and other designs can be used to reduce or modify the space.

    :param notebook: the notebook used to store results (defaults to an empty :class:`LabNotebook`)
    :param design: the experimental design to use (defaults to a :class:`FactorialDesign`)
    """

    def __init__(self, notebook: LabNotebook = None, design: Design = None):
        self._notebook = notebook if notebook is not None else LabNotebook()
        self._design = design if design is not None else FactorialDesign()
        self._parameters : Dict[str, Any] = dict()

    def notebook(self) -> LabNotebook:
        """Return the notebook being used by this lab.

        :returns: the notebook"""
        return self._notebook

    def design(self) -> Design:
        '''Return the experimental design this lab uses.

        :returns: the design'''
        return self._design


    # ---------- Protocol ----------

    def open( self ):
        """Open a lab for business. Sub-classes might insist the they are
        opened and closed explicitly when experiments are being performed.
        The default does nothing."""
        pass

    def close( self ):
        """Shut down a lab. Sub-classes might insist the they are
        opened and closed explicitly when experiments are being performed.
        The default does nothing."""
        pass

    def updateResults( self ):
        """Update the lab's results. This method is called by all other methods
        that return results in some sense, and may be overridden to let the results
        "catch up" with external processing. The default does nothing."""
        pass

    def recreate(self):
        '''Return a structure describing this lab in enough detail to reconstruct it,
        consisting of the name of the class and a dict of any arguments that it needs.
        Sub-classes should call the base method to fill in any defaults and then add
        any arguments they need to the dict.

        :returns: a (classname, args) pair
        '''
        n = '{modulename}.{classname}'.format(modulename = self.__class__.__module__,
                                              classname = self.__class__.__name__)
        args = dict()
        return (n, args)


    # ---------- Managing experimental parameters ----------

    def addParameter(self, k : str, r : Any):
        """Add a parameter to the experiment's parameter space. k is the
        parameter name, and r is its range. The range can be a single value
        or a list, or any other iterable. (Strings are counted as single values.)

        :param k: parameter name
        :param r: parameter range"""
        if isinstance(r, str):
            # strings are single values
            self._parameters[k] = [ r ]
        else:
            try:
                # try to unpack using iterator
                self._parameters[k] = list(r)
            except TypeError:
                # not iterable, a single value
                self._parameters[k] = [ r ]

    def deleteParameter(self, k : str):
        '''Delete a parameter from the parameter space. If the
        parameter doesn't exist then this is a no-op.

        :param k: the parameter name'''
        if k in self._parameters:
            del self._parameters[k]

    def deleteAllParameters(self):
        '''Delete all parameters from the parameter space.'''
        for k in self.parameters():
            del self[k]

    def parameters(self) -> List[str]:
        """Return a list of parameter names.

        :returns: a list of parameter names"""
        return list(self._parameters.keys())

    def __len__(self) -> int:
        """The length of an experiment is the total number of data points
        that will be explored. This is the length of the experimental
        configuration returned by :meth:`experiments`.

        :returns: the number of experimental runs"""
        return len(self.experiments(None))

    def __getitem__(self, k : str) -> Any:
        """Access a parameter range using array notation.

        :param k: parameter name
        :returns: the parameter range"""
        return self._parameters[k]

    def __setitem__(self, k : str, r : Any):
        """Add a parameter using array notation.

        :param k: the parameter name
        :param r: the parameter range"""
        self.addParameter(k, r)

    def __delitem__(self, k : str):
        '''Delete a parameter using array notation.

        :param k: the key'''
        self.deleteParameter(k)

    def __contains__(self, k : str) -> bool:
        '''Test whether the given key is a paramater for the lab.

        :param k: the keys
        :returns: True if this is a parameter'''
        return k in self.parameters()

    def experiments(self, e: Experiment) -> ExperimentalConfiguration:
        """Return the :term:`experimental configuration`, a list consisting of
        experiments and the points at which they should be run. The
        structure of the experimental space is defined by the lab's
        experimental design, which may also change the experiment to
        be run.

        :param e: the experiment
        :returns: an experimental configuration

        """
        return self._design.experiments(e, self._parameters)


    # ---------- Running experiments ----------

    def runExperiment(self, e: Experiment):
        """Run an experiment over all the points in the parameter space.
        The results will be stored in the notebook.

        :param e: the experiment"""

        # create the experimental parameter space
        eps = self.experiments(e)

        # run the experiment at each point
        nb = self.notebook()
        for (ep, p) in eps:
            #print(f"Running {p}")
            res = ep.set(p).run()
            nb.addResult(res)

        # commit the results
        nb.commit()


    # ---------- Accessing results ----------

    def dataframe(self, only_successful : bool =True) -> DataFrame:
        """Return the current results as a pandas DataFrame after resolving
        any pending results that have completed. This makes
        use of the underlying notebook's current result set. For finer control,
        access the notebook's :meth:`LabNotebook.dataframe` or
        :meth:LabNotebook.dataframeFor` methods directly.

        :param only_successful: only return successful results
        :returns: the resulting dataset as a DataFrame"""
        self.updateResults()
        return self._notebook.dataframe(only_successful=only_successful)

    def results(self) -> List[ResultsDict]:
        '''Return the current results as a list of results dicts after resolving
        any pending results that have completed. This makes
        use of the underlying notebook's current result set. For finer control,
        access the notebook's :meth:`LabNotebook.results` or
        :meth:LabNotebook.resultsFor` methods directly.

        Note that this approach to acquiring results is a lot slower and more
        memory-hungry than using :meth:`dataframe`, but may be useful for small
        sets of results that benefit from a more Pythonic intertface.'''
        self.updateResults()
        return self._notebook.results()

    def ready(self, tag : str =None) -> bool:
        """Test whether all the results are ready in the tagged result
        set -- that is, none are pending.

        :param tag: (optional) the result set to check (default is the current result set)
        :returns: True if the results are in"""
        self.updateResults()
        return self._notebook.ready(tag)

    def readyFraction(self, tag : str =None) -> float:
        '''Return the fraction of results available (not pending) in the
        tagged result set after first updating the results.

        :param tag: (optional) the result set to check (default is the current result set)
        :returns: the ready fraction'''
        self.updateResults()
        return self._notebook.readyFraction(tag)
