#
# Copyright (C) 2016 Simon Dobson
# 
# Licensed under the GNU General Public Licence v.2.0
#

import epyc

import numpy


class ExperimentCombinator(epyc.Experiment):
    '''An experiment that wraps-up another, underlying experiment. This is an abstract
    class that just provides the common wrapping logic.

    Experiment combinators aren't expected to have parameters of their own: they
    simply use the parameters of their underlying experiment.'''

    def __init__( self, ex ):
        '''Create a combinator based on the given experiment.

        ex: the underlying experiment'''
        super(epyc.ExperimentCombinator, self).__init__()
        self._experiment = ex

    def experiment( self ):
        '''Return the underlying experiment.

        returns: the underlying experiment'''
        return self._experiment

    def configure( self, params ):
        '''Configuring the summary configures the underlying experiment.

        params: the experiment's parameters'''
        self.experiment().configure(params)

    def deconfigure( self ):
        '''De-configuring the summary de-configures the underlying experiment.'''
        self.experiment().deconfigure()

    def parameters( self ):
        '''Return the current experimental parameters, taken from the
        underlying experiment.

        returns: the parameters,'''
        return self.experiment().parameters()
