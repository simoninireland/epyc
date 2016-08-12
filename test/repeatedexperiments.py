# Tests of repeated experiments combinator
#
# Copyright (C) 2016 Simon Dobson
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
        
        results = self._lab.results()
        self.assertEqual(len(results), N * len(self._lab['x']))
        for res in self._lab.notebook().resultsFor(dict(x = self._lab['x'][0])):
            self.assertEqual(res[Experiment.RESULTS]['result'], self._lab['x'][0])
            
    def testRepetitionsMultiplePoint( self ):
        '''Test we can repeat an experiment across a parameter space'''
        N = 10
        
        self._lab['x'] = [ 5, 10, 15 ]
        
        e = SampleExperiment1()
        er = RepeatedExperiment(e, N)

        self._lab.runExperiment(er)
        results = self._lab.results()
        self.assertEqual(len(results), N * len(self._lab['x']))

        for x in range(len(self._lab['x'])):
            for res in self._lab.notebook().resultsFor(dict(x = x)):
                self.assertIn(res[Experiment.PARAMETERS]['x'], x)
                self.assertEqual(res[Experiment.RESULTS]['result'], x)


