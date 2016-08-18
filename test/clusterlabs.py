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


class SampleExperiment(Experiment):
    '''A very simple experiment that adds up its parameters.'''

    def do( self, param ):
        total = 0
        for k in param:
            total = total + param[k]
        return dict(total = total)

class SampleExperiment1(Experiment):
    '''A more exercising experiment.'''

    def do( self, param ):
        total = 0
        for k in param:
            total = total + param[k]
        return dict(total = total,
                    nestedArray = [ 1, 2, 3 ],
                    nestedDict = dict(a = 1, b = 'two'))

    
# use the existence of an ipcontroller-client.json file in the IPython
# default profile's directory as a proxy for there being a cluster running
# that we can use for our tests
default_profile_dir = subprocess.check_output('ipython locate profile default'.split()).strip('\n')
connection_file = default_profile_dir + '/security/ipcontroller-client.json'
@unittest.skipUnless(os.path.isfile(connection_file),
                     "No default cluster running (no {fn})".format(fn = connection_file))
class ClusterLabTests(unittest.TestCase):

    def setUp( self ):
        '''Create a lab in which to perform tests.'''
        self._lab = ClusterLab()

    def tearDown( self ):
        '''Close the conection to the cluster.'''
        self._lab.close()
        self._lab = None
        
    def testMixup( self ):
        '''Test that parameter spaces are suitably mixed, defined as not
        more than 0.5% of elements landing in their original place'''
        n = 1000
        
        l = numpy.arange(0, n)
        self._lab._mixup(l)
        sp = [ v for v in (l == numpy.arange(0, n)) if v ]
        self.assertTrue(len(sp) <= (n * 0.005))

    def testEmpty( self ):
        '''Test that things work for an empty lab.'''
        self.assertEqual(self._lab.readyFraction(), 0)
        self.assertEqual(self._lab.results(), [])
        
    def testRunExprimentSync( self ):
        '''Test running an experiment and grabbing all the results by waiting'''
        n = 100

        r = numpy.arange(0, n)
        self._lab['a'] = r
        self._lab.runExperiment(SampleExperiment())
        time.sleep(5)
        self.assertTrue(self._lab.ready())
        res = self._lab.results()
        
        # check that the whole parameter space has a result
        self.assertEqual(len(res), n)
        for p in res:
            self.assertIn(p[Experiment.PARAMETERS]['a'], r)

        # check that each result corresponds to its parameter
        for p in res:
            self.assertEqual(p[Experiment.PARAMETERS]['a'], p[Experiment.RESULTS]['total'])

    def testRunExprimentAsync( self ):
        '''Test running an experiment and check the results come in piecemeal'''
        n = 100

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
        res = self._lab.results()
        
        # check that the whole parameter space has a result
        self.assertEqual(len(res), n)
        for p in res:
            self.assertIn(p[Experiment.PARAMETERS]['a'], r)

        # check that each result corresponds to its parameter
        for p in res:
            self.assertEqual(p[Experiment.PARAMETERS]['a'], p[Experiment.RESULTS]['total'])

    def testJSON( self ):
        '''Test that we can persist repeated results in JSON format.'''

        # reset the lab we're using to use a JSON notebook
        tf = NamedTemporaryFile()
        tf.close()
        self._lab = ClusterLab(notebook = JSONLabNotebook(tf.name, create = True))
        
        repetitions = 5
        self._lab['a'] = [ 1, 2, 3 ]
        try:
            self._lab.runExperiment(SummaryExperiment(RepeatedExperiment(SampleExperiment1(),
                                                                         repetitions),
                                                      summarised_results = [ 'total', 'nestedArray' ]))
                                    
            while not self._lab.ready():
                print "..."
                time.sleep(5)
            res = self._lab.results()

            # getting here is enough to exercise the persistence regime
        finally:
            try:
                os.remove(tf.name)
            except OSError:
                pass

        
        
