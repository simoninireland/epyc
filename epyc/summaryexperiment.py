#
# Copyright (C) 2016 Simon Dobson
# 
# Licensed under the GNU General Public Licence v.2.0
#

import epyc

import numpy


class SummaryExperiment(epyc.ExperimentCombinator):
    '''An experiment combinator that takes an underlying experiment and 
    returns summary statistics for some of its results. This only really makes
    sense for experiments that return lists of results, such as those conducted
    using RepeatedExperiment.

    When run, a summary experiment summarises the experimental
    results, creating a new set of results that include the mean and
    variance for each result that the underyling experiments
    generated. (You can also select which results to summarise.) The
    raw results are discarded. The new results have the names of the
    raw results with suffices for mean, median, and variance".

    The summarisation obviously only works on result keys coming from the
    underlying experiments that are numeric. The default behaviour is to try to
    summarise all keys: you can restrict this by providing a list of keys to the
    constructor in the summarised_results keyword argument.

    The summary calculations only include those experimental runs that succeeded,
    that is that have their status set to True. Failed runs are ignored.'''

    # Additional metadata
    UNDERLYING_RESULTS = 'repetitions'                         #: Metadata relement for the number of repetitions performed
    UNDERLYING_SUCCESSFUL_RESULTS = 'successful_repetitions'   #: Mettadata elements for the number of repetitions summarised

    # Prefix and suffix tags attached to summarised result and metadata values
    MEAN_SUFFIX = '_mean'              #: Suffix the mean of the underlking values
    MEDIAN_SUFFIX = '_median'          #: Suffix the median of the underlking values
    VARIANCE_SUFFIX = '_variance'      #: Suffix the variance of the underlking values
    
    
    def __init__( self, ex, summarised_results = None ):
        '''Create a summarised version of the given experiment. The given
        fields in the experimental results will be summarised, defaulting to all.
        If there are fields that can't be sujmmarised (because they're not
        numbers), remove them here. 

        :param ex: the underlying experiment
        :param summarised_results: list of result values to summarise (defaults to all)'''
        super(epyc.SummaryExperiment, self).__init__(ex)
        self._summarised_results = summarised_results

    def _mean( self, k ):
        '''Return the tag associated with the mean of k.'''
        return k + self.MEAN_SUFFIX

    def _median( self, k ):
        '''Return the tag associated with the median of k.'''
        return k + self.MEDIAN_SUFFIX

    def _variance( self, k ):
        '''Return the tag associated with the variance of k.'''
        return k + self.VARIANCE_SUFFIX
    
    def _summarise( self, results ):
        '''Private method to generate a summary result dict from a list of result dicts
        returned by do() on the repetitions of the underlying experiment.
        By default we generate order, mean and variance for each value recorded.

        We drop from the calculations any experiments whose completion status
        was False, indicating an error.

        Override this method to create different summary statistics.

        results: an array of result dicts
        returns: a dict of summary statistics'''
        if len(results) == 0:
            return dict()
        else:
            summary = dict()

            # work out the fields to summarise
            allKeys = results[0][epyc.Experiment.RESULTS].keys()
            ks = self._summarised_results
            if ks is None:
                # if we don't restrict, summarise all keys
                ks = allKeys
            else:
                # protect against a key that's not present
                ks = [ k for k in ks if k in allKeys ]
                
            # add the summary statistics
            for k in ks:
                vs = [ res[epyc.Experiment.RESULTS][k] for res in results ]
                summary[self._mean(k)]     = numpy.mean(vs)
                summary[self._median(k)]   = numpy.median(vs)
                summary[self._variance(k)] = numpy.var(vs)

            return summary   

    def do( self, params ):
        '''Perform the underlying experiment and summarise its results.
        Our results are the summary statistics extracted from the results of
        the instances of the underlying experiment that we performed.

        We drop from the calculations any experiments whose completion status
        was False, indicating an error.

        :param params: the parameters to the underlying experiment
        :returns: the summary statistics of the underlying results'''

        # perform the underlying experiment
        results = self.experiment().run()
        if not isinstance(results, list):
            results = [ results ]

        # extract only the successful runs
        sresults = [ res for res in results if res[epyc.Experiment.METADATA][epyc.Experiment.STATUS] ]

        # add extra values to out metadata record
        self._metadata[self.UNDERLYING_RESULTS]            = len(results)
        self._metadata[self.UNDERLYING_SUCCESSFUL_RESULTS] = len(sresults)
        
        # construct summary results
        return self._summarise(sresults)

