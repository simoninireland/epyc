# Experiment combinator to run the same experiment several times and
# return only the summary statistics
#
# Copyright (C) 2016 Simon Dobson
# 
# Licensed under the GNU General Public Licence v.2.0
#

import epyc


class RepeatedExperiment(epyc.ExperimentCombinator):
    '''A experiment combinator that takes a "base" experiment and runs it
    several times. This means you can define a single experiment separate
    from its repeating logic.

    When run, a repeated experiment runs a number of repetitions of the underlying
    experiment at the same point in the parameter space. The result of the
    repeated experiment is the list of results from the underlying experiment.
    If the underlying experiment itself returns a list of results, these are all
    flattened into a single list.'''

    def __init__( self, ex, N ):
        '''Create a repeated version of the given experiment.

        :param ex: the underlying experiment
        :param N: the number of repetitions to perform'''
        super(epyc.RepeatedExperiment, self).__init__(ex)
        self._N = N

    def repetitions( self ):
        '''Return the number of repetitions of the underlying experiment
        we expect to perform.

        returns: the number of repetitions'''
        return self._N

    def do( self, params ):
        '''Perform the number of repetitions we want.

        params: the parameters to the experiment
        returns: a list of result dicts'''
        N = self.repetitions()
        results = []
        for i in xrange(N):
            res = self.experiment().run()
            if isinstance(res, list):
                results.extend(res)
            else:
                results.append(res)
        return results

    def report( self, params, meta, res ):
        '''Return just the list of results, don't add any more metadata.

        :param params: the parameters we ran under
        :param meta: the metadata for this run
        :param res: the list of results
        :returns: the list of results'''
        return res
    
