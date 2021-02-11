# Tests of experiments class
#
# Copyright (C) 2016--2021 Simon Dobson
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

from epyc import *

import unittest
import time


class SampleExperiment0(Experiment):
    '''A base experiment that records the phases of the experiment.'''
    
    def __init__( self ):
        super(SampleExperiment0, self).__init__()
        self._ps = []
        
    def setUp( self, params ):
        self._ps.append('setup')

    def tearDown( self ):
        self._ps.append('teardown')
        
    def do( self, params ):
        self._ps.append('do')
        return dict()

    def report( self, params, meta, res ):
        ext = Experiment.report(self, params, meta, res)
        ext[self.METADATA]['phases'] = self._ps
        return ext

class SampleExperiment1(Experiment):
    '''An experiment that does literally nothing.'''
    
    def do( self, params ):
        pass

class SampleExperiment2(SampleExperiment0):
    '''An experiment that does nothing for 1s and returns a results dict.'''
    
    def do( self, params ):
        time.sleep(1)
        return SampleExperiment0.do(self, params)

class SampleExperiment3(SampleExperiment0):
    '''An experiment that does a calculation.'''
    
    def do( self, params ):
        return dict(result = params['a'] + params['b'])

class SampleExperiment4(SampleExperiment0):
    '''An experiment that makes sure there are timings to test.'''
    
    def setUp( self, params ):
        time.sleep(1)

    def tearDown( self ):
        time.sleep(1)

    def do( self, params ):
        time.sleep(1)
        return dict()

class SampleExperiment5(SampleExperiment0):
    '''An experiment that fails in its main action.'''
    
    def do( self, params ):
        raise Exception('We failed (on purpose)')
   
class SampleExperiment6(SampleExperiment0):
    '''An experiment that fails in its setup, and so should not do a teardown.'''
    
    def setUp( self, params ):
        raise Exception('We failed (on purpose)')

class SampleExperiment7(SampleExperiment0):
    '''An experiment that fails in its teardown.'''
    
    def tearDown( self ):
        raise Exception('We failed (on purpose)')

class SampleExperiment8(Experiment):
    '''An experiment that returns a lot of results dicts.'''

    def do(self, params):
        res = []
        rc = self.resultsdict()
        rc[Experiment.RESULTS] = dict(a=1, c=params['c'])
        res.append(rc)
        rc = self.resultsdict()
        rc[Experiment.RESULTS] = dict(a=2, c=params['c'])
        res.append(rc)
        return res

class ExperimentTests(unittest.TestCase):

    def testNoResults( self ):
        '''Test do() not returning results.'''
        e = SampleExperiment1()
        e.set(dict())
        res = e.run()
        self.assertTrue(res[Experiment.METADATA][Experiment.STATUS])

    def testPhases( self ):
        '''Test that phases execute correctly.'''
        e = SampleExperiment2()
        e.set(dict())
        res = e.run()
        self.assertTrue(res[Experiment.METADATA][Experiment.STATUS])
        self.assertIn('phases', res[Experiment.METADATA].keys())
        self.assertEqual(res[Experiment.METADATA]['phases'], [ 'setup', 'do', 'teardown' ])

    def testParameters( self ):
        '''Test that parameters are recorded properly.'''
        e = SampleExperiment2()
        params = dict(a = 1, b = 1.0, c = 'hello world')
        e.set(params)
        res = e.run()
        self.assertTrue(res[Experiment.METADATA][Experiment.STATUS])
        self.assertIn(Experiment.PARAMETERS, res.keys())
        for k in params.keys():
            self.assertEqual(res[Experiment.PARAMETERS][k], params[k])

    def testReporting( self ):
        '''Test that results are reported properly.'''
        e = SampleExperiment3()
        params = dict(a = 1, b = 2, c = 'hello world')
        e.set(params)
        res = e.run()
        self.assertTrue(res[Experiment.METADATA][Experiment.STATUS])
        self.assertIn('result', res[Experiment.RESULTS].keys())
        self.assertEqual(res[Experiment.RESULTS]['result'], params['a'] + params['b'])

    def testTiming( self ):
        '''Test that timings are plausible.'''
        e = SampleExperiment4()
        e.set(dict())
        res = e.run()
        self.assertTrue(res[Experiment.METADATA][Experiment.STATUS])

        timing = res[Experiment.METADATA]
        #print(timing)
        self.assertTrue(timing[Experiment.END_TIME] > timing[Experiment.START_TIME])
        self.assertTrue(timing[Experiment.ELAPSED_TIME] > 0)
        self.assertTrue(timing[Experiment.SETUP_TIME] > 0)
        self.assertTrue(timing[Experiment.EXPERIMENT_TIME] > 0)
        self.assertTrue(timing[Experiment.TEARDOWN_TIME] > 0)
        self.assertAlmostEqual(timing[Experiment.ELAPSED_TIME], timing[Experiment.SETUP_TIME] + timing[Experiment.TEARDOWN_TIME] + timing[Experiment.EXPERIMENT_TIME], places=3)

    def testException( self ):
        '''Test that exceptions are caught and reported in-line.'''
        e = SampleExperiment5()
        e.set(dict())
        res = e.run()
        self.assertFalse(res[Experiment.METADATA][Experiment.STATUS])
        self.assertIn('phases', res[Experiment.METADATA].keys())
        self.assertEqual(res[Experiment.METADATA]['phases'], [ 'setup', 'teardown' ])

    def testExceptionInSetup( self ):
        '''Test that exceptions in setup are caught and not torn down.'''
        e = SampleExperiment6()
        e.set(dict())
        res = e.run()
        self.assertFalse(res[Experiment.METADATA][Experiment.STATUS])
        self.assertIn('phases', res[Experiment.METADATA].keys())
        self.assertEqual(res[Experiment.METADATA]['phases'], [ ])

    def testExceptionInTeardown( self ):
        '''Test that exceptions in teardown are caught.'''
        e = SampleExperiment7()
        e.set(dict())
        res = e.run()
        self.assertFalse(res[Experiment.METADATA][Experiment.STATUS])
        self.assertIn('phases', res[Experiment.METADATA].keys())
        self.assertEqual(res[Experiment.METADATA]['phases'], [ 'setup', 'do' ])

    def testRecordingOnObject( self ):
        '''Test that everything is also available through the experiment object.'''
        e = SampleExperiment3()
        params = dict(a = 1, b = 2, c = 'hello world')
        e.set(params)
        res = e.run()
        self.assertTrue(res[Experiment.METADATA][Experiment.STATUS])
        self.assertEqual(res[Experiment.METADATA][Experiment.STATUS], e.success())
        self.assertIn('result', res[Experiment.RESULTS].keys())
        self.assertEqual(res[Experiment.RESULTS]['result'], params['a'] + params['b'])

    def testKeyInterface( self ):
        '''Test access to results by key.'''
        e = SampleExperiment3()
        params = dict(a = 1, b = 2, c = 'hello world')
        e.set(params)
        res = e.run()
        self.assertEqual(e['result'], params['a'] + params['b'])

    def testListResults(self):
        '''Test we wrap a list of experimental results properly.'''
        e = SampleExperiment8()
        params = dict(c='hello world')
        e.set(params)
        rc = e.run()
        self.assertFalse(isinstance(rc, list))
        self.assertTrue(isinstance(rc[Experiment.RESULTS], list))
        res = rc[Experiment.RESULTS]
        self.assertEqual(len(res), 2)
        for rc in res:
            self.assertEqual(rc[Experiment.RESULTS]['c'], params['c'])
       
if __name__ == '__main__':
    unittest.main()
