# Tests of cluster-driven lab class
#
# Copyright (C) 2016--2020 Simon Dobson
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
import numpy
import time
import os
import subprocess
from tempfile import NamedTemporaryFile


# open-up logging for testing the cluster
import logging
logger = logging.getLogger(Logger)
logger.setLevel(logging.DEBUG)


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


# use the existence of a security/cluster-.json file in the epyctest IPython
# profile directory as a proxy for there being a cluster running
# that we can use for our tests
# (cluster is created by running `make cluster` in the project Makefile)
profile = 'epyctest'
try:
    profile_dir = subprocess.check_output(f'ipython locate profile {profile}', shell=True).rstrip().decode()
    pid_file = os.path.join(profile_dir, 'security/cluster-.json')
    cluster_running = os.path.isfile(pid_file)
except:
    cluster_running = False
@unittest.skipUnless(cluster_running,
                     f'No {profile} cluster running')
class ClusterLabTests(unittest.TestCase):

    def setUp( self ):
        '''Create a lab in which to perform tests and a tempfile for HDF5 tests.'''
        self._lab = ClusterLab(profile=profile)
        #self._lab = ClusterLab(url_file='ipcontroller-client.json')
        tf = NamedTemporaryFile()
        tf.close()
        self._fn = tf.name
        #self._fn = 'test.h5'

    def tearDown( self ):
        '''Close the conection to the cluster and delete the test HDF5 file.'''
        self._lab.close()
        self._lab = None
        try:
            os.remove(self._fn)
            #pass
        except OSError:
            pass

    def _results(self):
        '''Retrieve results as a list of dicts, for easier comparisons.'''
        df = self._lab.dataframe()
        res = []
        for i in df.index:
            row = dict()
            for k in df.columns:
                row[k] = df.loc[i][k]
            res.append(row)
        return res

    def testEmpty( self ):
        '''Test that things work for an empty lab'''
        self.assertEqual(self._lab.notebook().readyFraction(), 1.0)
        self.assertEqual(len(self._lab.dataframe()), 0)

    def testRunExprimentSync( self ):
        '''Test running an experiment and grabbing all the results by sleeping for a while.'''
        n = 20

        r = numpy.arange(0, n)
        self._lab['a'] = r
        self._lab.runExperiment(SampleExperiment())
        time.sleep(n * 2.5 / self._lab.numberOfEngines())
        self.assertTrue(self._lab.ready())
        res = self._results()

        # check that the whole parameter space has a result
        self.assertEqual(len(res), n)
        for p in res:
            self.assertIn(p['a'], r)

        # check that each result corresponds to its parameter
        for p in res:
            self.assertEqual(p['a'], p['total'])

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
        self.assertFalse(self._lab.wait(timeout=5))
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
        res = self._results()

        # check that the whole parameter space has a result
        self.assertEqual(len(res), n)
        for p in res:
            self.assertIn(p['a'], r)

        # check that each result corresponds to its parameter
        for p in res:
            self.assertEqual(p['a'], p['total'])

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

        # cancel a job, check we retained them all
        params = dict(a = int(n / 2))
        jobids = self._lab.notebook().current().pendingResultsFor(params)
        for j in jobids:
            self._lab.notebook().cancelPendingResult(j)
        self._lab.wait()
        self.assertEqual(self._lab.notebook().current().numberOfResults(), n)
        self.assertEqual(self._lab.notebook().current().numberOfPendingResults(), 0)

        # check cancelled job had a marker exception
        for rc in self._lab.notebook().results():
            if rc[Experiment.PARAMETERS]['a'] == int(n / 2):
                self.assertTrue(isinstance(rc[Experiment.METADATA][Experiment.EXCEPTION], CancelledException))


    def testCancelAllJobs( self ):
        '''Test we can cancel all jobs.'''
        n = 20

        r = numpy.arange(0, n)
        self._lab['a'] = r
        self._lab.runExperiment(SampleExperiment2())

        # cancel all jobs
        for j in self._lab.notebook().allPendingResults():
            self._lab.notebook().cancelPendingResult(j)
        self._lab.wait()
        self.assertEqual(self._lab.notebook().current().numberOfResults(), 20)
        self.assertEqual(self._lab.notebook().current().numberOfPendingResults(), 0)

        # make sure all jobs have a marker
        for rc in self._lab.notebook().results():
            self.assertTrue(isinstance(rc[Experiment.METADATA][Experiment.EXCEPTION], CancelledException))


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
        self.assertEqual(len(self._lab.notebook().dataframe()), 2 * n)
        self.assertEqual(self._lab.notebook().current().numberOfPendingResults(), 0)

    def testClusterAndHDF5(self):
        '''Test that a cluster works with HDF5 properly.'''
        self._lab = ClusterLab(profile=profile,
                               notebook=HDF5LabNotebook(self._fn, create=True))
        self._lab.notebook().addResultSet('mydata')

        # run an experiment, with all the trimmings
        n = 20
        r = numpy.arange(0, n)
        self._lab['a'] = r
        self._lab.runExperiment(SampleExperiment2())
        self._lab.wait()
        self._lab.notebook().commit()

        with self._lab.notebook().open() as nb:
            self.assertEqual(len(nb), 2)         # number of result sets
            self.assertEqual(len(nb.current()), n)
            self.assertEqual(nb.numberOfResults(), n)
            self.assertEqual(nb.numberOfPendingResults(), 0)


# TODO: Test we can run pending jobs from different result sets

if __name__ == '__main__':
    unittest.main()
