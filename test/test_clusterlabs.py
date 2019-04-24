# Tests of cluster-driven lab class
#
# Copyright (C) 2016 Simon Dobson
# 
# Licensed under the GNU General Public Licence v.2.0
#

from epyc import *

import unittest
import numpy
import time
import os
import subprocess
from tempfile import NamedTemporaryFile

# set limit low for testing purposes
ClusterLab.WaitingTime = 10


class SampleExperiment(Experiment):
    '''A very simple experiment that adds up its parameters.'''

    def do( self, param ):
        total = 0
        for k in param:
            total = total + param[k]
        return dict(total = total)

class SampleExperiment2(Experiment):
    '''Add up after waiting.'''

    def do( self, param ):
        time.sleep(2)
        total = 0
        for k in param:
            total = total + param[k]
        return dict(total = total)

    
# use the existence of an ipcontroller-client.json file in the IPython
# default profile's directory as a proxy for there being a cluster running
# that we can use for our tests
default_profile_dir = str(subprocess.check_output('ipython locate profile default', shell = True)).strip('\n')
connection_file = os.path.join(default_profile_dir, 'security/ipcontroller-client.json')
@unittest.skipUnless(os.path.isfile(connection_file),
                     "No default cluster running (no {fn})".format(fn = connection_file))
class ClusterLabTests(unittest.TestCase):

    def setUp( self ):
        '''Create a lab in which to perform tests.'''
        self._lab = ClusterLab()
        #self._lab._use_dill()
        with self._lab.sync_imports():
            import time

    def tearDown( self ):
        '''Close the conection to the cluster.'''
        self._lab.close()
        self._lab = None
        
    def testMixup( self ):
        '''Test that parameter spaces are suitably mixed, defined as not
        more than 0.5% of elements landing in their original place.'''
        n = 1000
        
        l = numpy.arange(0, n)
        self._lab._mixup(l)
        sp = [ v for v in (l == numpy.arange(0, n)) if v ]
        self.assertTrue(len(sp) <= (n * 0.005))

    def testEmpty( self ):
        '''Test that things work for an empty lab'''
        self.assertEqual(self._lab.readyFraction(), 0)
        self.assertEqual(self._lab.results(), [])
        
    def testRunExprimentSync( self ):
        '''Test running an experiment and grabbing all the results by sleeping for a while.'''
        n = 20

        r = numpy.arange(0, n)
        self._lab['a'] = r
        self._lab.runExperiment(SampleExperiment())
        time.sleep(n * 2.5 / self._lab.numberOfEngines())
        self.assertTrue(self._lab.ready())
        res = self._lab.results()
        
        # check that the whole parameter space has a result
        self.assertEqual(len(res), n)
        for p in res:
            self.assertIn(p[Experiment.PARAMETERS]['a'], r)

        # check that each result corresponds to its parameter
        for p in res:
            self.assertEqual(p[Experiment.PARAMETERS]['a'], p[Experiment.RESULTS]['total'])
            
    def testWait( self ):
        '''Test waiting for all jobs to complete.'''
        n = 20

        r = numpy.arange(0, n)
        self._lab['a'] = r
        self._lab.runExperiment(SampleExperiment())
        self.assertTrue(self._lab.wait())
        self.assertTrue(self._lab.ready())
            
    def testWaitShortTimeout( self ):
        '''Test short-timeout (and short-latency) waiting.'''
        n = 20
        self._lab.WaitingTime = 5
        
        r = numpy.arange(0, n)
        self._lab['a'] = r
        self._lab.runExperiment(SampleExperiment2())
        self.assertFalse(self._lab.wait(timeout = 5))
        self.assertFalse(self._lab.ready())
        self.assertTrue(self._lab.wait())
        self.assertTrue(self._lab.ready())

    def testRunExprimentAsync( self ):
        '''Test running an experiment and check the results come in piecemeal.'''
        n = 20

        r = numpy.arange(0, n)
        self._lab['a'] = r
        self._lab.runExperiment(SampleExperiment())

        # watch results coming in
        f = 0.0
        while f < 1:
            f1 = self._lab.readyFraction()
            #print self._lab._availableResults(), f1
            self.assertTrue(f1 >= f)
            f = f1
        self.assertTrue(self._lab.ready())
        self.assertEqual(self._lab.notebook().numberOfPendingResults(), 0)
        res = self._lab.results()
        
        # check that the whole parameter space has a result
        self.assertEqual(len(res), n)
        for p in res:
            self.assertIn(p[Experiment.PARAMETERS]['a'], r)

        # check that each result corresponds to its parameter
        for p in res:
            self.assertEqual(p[Experiment.PARAMETERS]['a'], p[Experiment.RESULTS]['total'])

    def testReturnWithNoJobs( self ):
        '''Test wait() returns True when there are no jobs pending.'''
        n = 20
          
        r = numpy.arange(0, n)
        self._lab['a'] = r
        self._lab.runExperiment(SampleExperiment())
        self.assertTrue(self._lab.wait())
        
        # calling wait() again should also be true (with no delay, which we don't check for)
        self.assertTrue(self._lab.wait())

    def testCancelSomeJobs( self ):
        '''Test we can cancel some jobs while keeping the rest.'''
        n = 20
          
        r = numpy.arange(0, n)
        self._lab['a'] = r
        self._lab.runExperiment(SampleExperiment2())

        params = dict(a = int(n / 2))
        self._lab.cancelPendingResultsFor(params)
        self._lab.wait()
        self.assertEqual(self._lab.numberOfResults(), n - 1)
        self.assertEqual(self._lab.numberOfPendingResults(), 0)
        self.assertEqual(self._lab.notebook().latestResultsFor(params), None)

    def testCancelAllJobs( self ):
        '''Test we can cancel all jobs.'''
        n = 20
          
        r = numpy.arange(0, n)
        self._lab['a'] = r
        self._lab.runExperiment(SampleExperiment2())

        self._lab.cancelAllPendingResults()
        self._lab.wait()
        self.assertEqual(self._lab.numberOfResults(), 0)
        self.assertEqual(self._lab.numberOfPendingResults(), 0)

    def testAddExperiments( self ):
        '''Test we can add experiments while some are running, without locking up.'''
        n = 20

        # run the first experiment
        r = numpy.arange(0, n)
        self._lab['a'] = r
        self._lab.runExperiment(SampleExperiment2())

        # while this is waiting, run another
        r = numpy.arange(n, 2 * n)
        self._lab['a'] = r
        self._lab.runExperiment(SampleExperiment2())

        self._lab.wait()
        self.assertEqual(self._lab.numberOfResults(), 2 * n)
        self.assertEqual(self._lab.numberOfPendingResults(), 0)

        
       
