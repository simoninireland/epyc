# Tests of repeated experiments combinator
#
# Copyright (C) 2016--2018 Simon Dobson
# 
# Licensed under the GNU General Public Licence v.2.0
#

from epyc import *

import unittest
import numpy
import numpy.random


class SampleExperiment1(Experiment):
        
    def do( self, params ):
        return dict(result = params['x'])

    
class RepeatedExperimentTests(unittest.TestCase):

    def setUp( self ):
        self._lab = Lab()
        
    def testRepetitionsOnePoint( self ):
        '''Test we can repeat an experiment at a single point'''
        N = 10
        
        self._lab['x'] = [ 5 ]
        
        e = SampleExperiment1()
        er = RepeatedExperiment(e, N)

        self._lab.runExperiment(er)
        self.assertTrue(er.success())

        rresults = self._lab.results()
        self.assertEqual(len(rresults), 1)

        self.assertEqual(rresults[0][Experiment.METADATA][RepeatedExperiment.REPETITIONS], N)
        
        results = rresults[0][Experiment.RESULTS]
        self.assertEqual(len(results), N * len(self._lab['x']))
        for res in results:
            self.assertEqual(res[Experiment.RESULTS]['result'], self._lab['x'][0])
            
    def testRepetitionsMultiplePoint( self ):
        '''Test we can repeat an experiment across a parameter space'''
        N = 10
        
        self._lab['x'] = [ 5, 10, 15 ]
        
        e = SampleExperiment1()
        er = RepeatedExperiment(e, N)

        self._lab.runExperiment(er)
        self.assertTrue(er.success())
        
        rresults = self._lab.results()
        self.assertEqual(len(rresults), 3)

        for i in xrange(3):
            results = rresults[i][Experiment.RESULTS]
            self.assertEqual(len(results), N)

            for j in range(N):
                res = results[j]
                self.assertIn(res[Experiment.PARAMETERS]['x'], self._lab['x'])
                self.assertEqual(res[Experiment.RESULTS]['result'], res[Experiment.PARAMETERS]['x'])


