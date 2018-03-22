#
# Copyright (C) 2016 Simon Dobson
# 
# Licensed under the GNU General Public Licence v.2.0
#

from epyc import *


class ExperimentCombinator(Experiment):
    '''An experiment that wraps-up another, underlying experiment. This is an abstract
    class that just provides the common wrapping logic.

    Experiment combinators aren't expected to have parameters of their own: they
    simply use the parameters of their underlying experiment. They may however
    give rise to metadata of their own, and modify the results returned by running
    their underlying experiment.'''

    def __init__( self, ex ):
        '''Create a combinator based on the given experiment.

        ex: the underlying experiment'''
        super(ExperimentCombinator, self).__init__()
        self._experiment = ex

    def experiment( self ):
        '''Return the underlying experiment.

        :returns: the underlying experiment'''
        return self._experiment

    def set( self, params ):
        '''Set the parameters for the experiment, returning the
        now-configured experiment.

        :param params: the parameters
        :returns: the experiment combinator itself'''
        self.experiment().set(params)
        return self

    def parameters( self ):
        '''Return the current experimental parameters, taken from the
        underlying experiment.

        :returns: the parameters,'''
        return self.experiment().parameters()

    
