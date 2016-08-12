# Tests of summarising experiments combinator
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
        return dict(result = params['x'],
                    dummy = 1)

class SampleExperiment2(Experiment):

    def __init__( self ):
        super(SampleExperiment2, self).__init__()
        self._allvalues = []
    
    def do( self, params ):
        v = numpy.random.random()
        self._allvalues.append(v)
        return dict(result = v)

    def values( self ):
        return self._allvalues

class SampleExperiment3(SampleExperiment2):

    def __init__( self ):
        super(SampleExperiment3, self).__init__()
        self._ran = 0
    
    def do( self, params ):
        v = numpy.random.random()
        if v < 0.5:
            # experiment succeeds
            self._allvalues.append(v)
            self._ran = self._ran + 1
            return dict(result = v)
        else:
            # experiment fails
            raise Exception("Failing")

    def ran( self ):
        return self._ran

    
class SummaryExperimentTests(unittest.TestCase):

    def setUp( self ):
        self._lab = Lab()
        
    def testRepetitionsOnePoint( self ):
        '''Test we can repeat an experiment at a single point'''
        N = 10
        
        self._lab['x'] = [ 5 ]
        
        e = SampleExperiment1()
        es = SummaryExperiment(RepeatedExperiment(e, N))

        self._lab.runExperiment(es)
        res = (self._lab.results())[0]

        self.assertTrue(res[Experiment.METADATA][Experiment.STATUS])
        self.assertEqual(res[Experiment.METADATA][SummaryExperiment.UNDERLYING_RESULTS], N)
        
    def testRepetitionsMultiplePoint( self ):
        '''Test we can repeat an experiment across a parameter space'''
        N = 10
        
        self._lab['x'] = [ 5, 10, 15 ]
        
        e = SampleExperiment1()
        es = SummaryExperiment(RepeatedExperiment(e, N))

        self._lab.runExperiment(es)
        res = self._lab.results()
        self.assertEqual(len(res), len(self._lab['x']))

        for i in range(len(self._lab['x'])):
            self.assertTrue(res[i][Experiment.METADATA][Experiment.STATUS])
            self.assertIn(res[i][Experiment.PARAMETERS]['x'], self._lab['x'])
            self.assertEqual(res[i][Experiment.METADATA][SummaryExperiment.UNDERLYING_RESULTS], N)
            self.assertEqual(res[i][Experiment.RESULTS]['result_mean'],
                             res[i][Experiment.PARAMETERS]['x'])
            self.assertEqual(res[i][Experiment.RESULTS]['result_variance'], 0)

    def testSummary( self ):
        '''Test that summary statistics are created properly'''
        N = 10
        
        self._lab['x'] = [ 5 ]
        
        e = SampleExperiment2()
        es = SummaryExperiment(RepeatedExperiment(e, N))

        self._lab.runExperiment(es)
        res = (self._lab.results())[0]

        self.assertTrue(res[Experiment.METADATA][Experiment.STATUS])
        self.assertEqual(res[Experiment.RESULTS]['result_mean'],
                         numpy.mean(e.values()))
        self.assertEqual(res[Experiment.RESULTS]['result_variance'],
                         numpy.var(e.values()))
       
    def testSelect( self ):
        '''Test we can select summary results'''
        N = 10
        
        self._lab['x'] = [ 5 ]
        
        e = SampleExperiment1()
        es = SummaryExperiment(RepeatedExperiment(e, N),
                               summarised_results = [ 'dummy' ])

        self._lab.runExperiment(es)
        res = (self._lab.results())[0]
        
        self.assertTrue(res[Experiment.METADATA][Experiment.STATUS])
        self.assertEqual(len(res[Experiment.RESULTS].keys()), 3)
        self.assertIn('dummy_mean', res[Experiment.RESULTS].keys())
        self.assertEqual(res[Experiment.RESULTS]['dummy_mean'], 1)
        self.assertIn('dummy_median', res[Experiment.RESULTS].keys())
        self.assertEqual(res[Experiment.RESULTS]['dummy_median'], 1)
        self.assertIn('dummy_variance', res[Experiment.RESULTS].keys())
        self.assertEqual(res[Experiment.RESULTS]['dummy_variance'], 0)

    def testIgnoring( self ):
        '''Test that we ignore failed experiments'''
        N = 10
        
        self._lab['x'] = [ 5 ]
        
        e = SampleExperiment3()
        es = SummaryExperiment(RepeatedExperiment(e, N))

        self._lab.runExperiment(es)
        res = (self._lab.results())[0]
        
        self.assertTrue(res[Experiment.METADATA][Experiment.STATUS])
        self.assertEqual(res[Experiment.METADATA][SummaryExperiment.UNDERLYING_RESULTS], N)
        self.assertEqual(res[Experiment.METADATA][SummaryExperiment.UNDERLYING_SUCCESSFUL_RESULTS], e.ran())
        self.assertEqual(res[Experiment.RESULTS]['result_mean'],
                         numpy.mean(e.values()))
        self.assertEqual(res[Experiment.RESULTS]['result_variance'],
                         numpy.var(e.values()))
         
