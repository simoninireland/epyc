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

from epyc import ExperimentCombinator, Experiment, ResultsDict
import numpy                     # type: ignore
import sys
if sys.version_info >= (3, 8):
    from typing import List, Dict, Any, Final
else:
    # backwards compatibility with Python 35, Python36, and Python37 
    from typing import List, Dict, Any
    from typing_extensions import Final


class SummaryExperiment(ExperimentCombinator):
    """An experiment combinator that takes an underlying experiment and
    returns summary statistics for some of its results. This only really makes
    sense for experiments that return lists of results, such as those conducted
    using :class:`RepeatedExperiment`, but it works with any experiment.

    When run, a summary experiment summarises the experimental
    results, creating a new set of results that include the mean and
    variance for each result that the underyling experiments
    generated. (You can also select which results to summarise.) The
    raw results are discarded. The new results have the names of the
    raw results with suffices for mean, median, variance, and extrema.

    The summarisation obviously only works on result keys coming from the
    underlying experiments that are numeric. The default behaviour is to try to
    summarise all keys: you can restrict this by providing a list of keys to the
    constructor in the summarised_results keyword argument. Trying to summarise
    non-numeric results will be ignored (with a warining).

    The summary calculations only include those experimental runs that succeeded,
    that is that have their status set to True. Failed runs are ignored."""

    # Additional metadata
    UNDERLYING_RESULTS : Final[str] = 'epyc.summaryexperiment.repetitions'                          #: Metadata element for the number of results that were obtained.
    UNDERLYING_SUCCESSFUL_RESULTS : Final[str] = 'epyc.summaryexperiment.successful_repetitions'    #: Metadata elements for the number of results that were summarised.

    # Prefix and suffix tags attached to summarised result and metadata values
    MEAN_SUFFIX : Final[str] = '_mean'              #: Suffix for the mean of the underlying values.
    MEDIAN_SUFFIX : Final[str] = '_median'          #: Suffix for the median of the underlying values.
    VARIANCE_SUFFIX : Final[str] = '_variance'      #: Suffix for the variance of the underlying values.
    MIN_SUFFIX : Final[str] = '_min'                #: Suffix for the minimum of the underlying values.
    MAX_SUFFIX : Final[str] = '_max'                #: Suffix for the maximum of the underlying values.
    
    
    def __init__(self, ex : Experiment, summarised_results : List[str] =None):
        """Create a summarised version of the given experiment. The given
        fields in the experimental results will be summarised, defaulting to all.
        If there are fields that can't be summarised (because they're not
        numbers), remove them here.

        :param ex: the underlying experiment
        :param summarised_results: list of result values to summarise (defaults to all)"""
        super(SummaryExperiment, self).__init__(ex)
        self._summarised_results = summarised_results

    def _mean(self, k : str) -> str:
        """Return the tag associated with the mean of k."""
        return k + self.MEAN_SUFFIX

    def _median(self, k : str) -> str:
        """Return the tag associated with the median of k."""
        return k + self.MEDIAN_SUFFIX

    def _variance(self, k : str) -> str:
        """Return the tag associated with the variance of k."""
        return k + self.VARIANCE_SUFFIX
    
    def _min(self, k : str) -> str:
        """Return the tag associated with the minimum of k."""
        return k + self.MIN_SUFFIX
    
    def _max(self, k : str) -> str:
        """Return the tag associated with the maximum of k."""
        return k + self.MAX_SUFFIX
    
    def summarise(self, results : List[ResultsDict]) -> ResultsDict:
        """Generate a summary of results from a list of experimental results dicts
        returned by running the underlying experiment. By default we generate
        mean, median, variance, and extrema for each value recorded.

        Override this method to create different or extra summary statistics.

        :param results: an array of experimental results dicts
        :returns: a dict of summary statistics"""
        if len(results) == 0:
            return dict()
        else:
            summary = dict()

            # work out the fields to summarise
            allKeys = results[0][Experiment.RESULTS].keys()
            ks = self._summarised_results
            if ks is None:
                # if we don't restrict, summarise all keys
                ks = allKeys
            else:
                # protect against a key that's not present
                ks = [ k for k in ks if k in allKeys ]
                
            # add the summary statistics
            for k in ks:
                # compute summaries for all fields we're interested in
                vs = [ res[Experiment.RESULTS][k] for res in results ]
                try:
                    summary[self._mean(k)]     = numpy.mean(vs)
                    summary[self._median(k)]   = numpy.median(vs)
                    summary[self._variance(k)] = numpy.var(vs)
                    summary[self._min(k)]      = numpy.min(vs)
                    summary[self._max(k)]      = numpy.max(vs)
                except Exception as e:
                    # couldn't do the statistics
                    print('Failed to summarise {k}: {e}'.format(k=k, e=e), file=sys.stderr)
                    
            return summary   

    def _flatten(self, rc : ResultsDict) -> List[ResultsDict]:
        '''Flatten-out any nested results.

        :param rc: a results dict, poissibly containing others nested as its results
        :returns: a flat list of results dicts'''
        rcs = []

        def _doflat(prc):
            if isinstance(prc[Experiment.RESULTS], list):
                for nrc in prc[Experiment.RESULTS]:
                    _doflat(nrc)
            else:
                rcs.append(prc)

        _doflat(rc)
        return rcs

    def do(self, params : Dict[str, Any]) -> Dict[str, Any]:
        """Perform the underlying experiment and summarise its results.
        Our results are the summary statistics extracted from the results of
        the instances of the underlying experiment that we performed.

        We drop from the calculations any experiments whose completion status
        was False, indicating an error. Our own completion status will be
        True unless we had an error summarising a field (usually caused by trying
        to summarise non-numeric data).

        We record the exceptions generated by any experiment we summarise under
        the metadata key :attr:`SummaryExperiment.UNDERLYING_EXCEPTIONS`

        :param params: the parameters to the underlying experiment
        :returns: the summary statistics of the underlying results"""

        # perform the underlying experiment
        rc = self.experiment().run()
        
        # extract all the results as a single list
        rcs = self._flatten(rc)

        # extract only the successful runs
        sres = [ rc for rc in rcs if rc[Experiment.METADATA][Experiment.STATUS] ]
      
        # add extra values to our metadata record
        self._metadata[self.UNDERLYING_RESULTS]            = len(rcs)
        self._metadata[self.UNDERLYING_SUCCESSFUL_RESULTS] = len(sres)
        
        # construct summary results
        return self.summarise(sres)

