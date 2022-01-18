# Tests of sequential lab class
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

import unittest
from datetime import datetime
import numpy
from epyc import *


class SampleExperiment(Experiment):
    '''A very simple experiment that adds up its parameters.'''

    def do( self, param ):
        total = 0
        for k in param:
            total = total + param[k]
        return dict(total = total)


class NullExperiment(Experiment):
    '''An experiment that just returns the value of its (one)
    parameter as its result.'''

    def do( self, param ):
        k = list(param.keys())[0]
        return dict(result = param[k])


class LabTests(unittest.TestCase):

    def setUp( self ):
        '''Create a lab in which to perform tests.'''
        self._lab = Lab()

    def testDefaultDesign(self):
        '''Test the default design is a factorial design.'''
        self.assertTrue(isinstance(self._lab.design(), FactorialDesign))

    def testParameterOne( self ):
        '''Test that we can set a single parameter.'''
        self._lab['a'] = numpy.arange(0, 100)

        self.assertEqual(len(self._lab['a']), len(numpy.arange(0, 100)))
        for i in numpy.arange(0, 100):
            self.assertIn(i, self._lab['a'])

    def testParameterThree( self ):
        '''Test that we can set several parameters.'''
        self._lab['a'] = numpy.arange(0, 100)
        self._lab['b'] = numpy.arange(0, 1000)
        self._lab['c'] = numpy.arange(10, 50, 10)

        self.assertCountEqual(self._lab['a'], numpy.arange(0, 100))
        self.assertCountEqual(self._lab['b'], numpy.arange(0, 1000))
        self.assertCountEqual(self._lab['c'], numpy.arange(10, 50, 10))

    def testRunOne( self ):
        '''Test that a simple experiment runs against a 1D parameter space.'''
        n = 100

        r = numpy.arange(0, n)
        self._lab['a'] = r
        self._lab.runExperiment(SampleExperiment())
        res = self._lab.results()

        # check that the whole parameter space has a result
        self.assertEqual(len(res), n)
        for p in res:
            self.assertIn(p[Experiment.PARAMETERS]['a'], r)

        # check that each result corresponds to its parameter
        for p in res:
            self.assertEqual(p[Experiment.PARAMETERS]['a'], p[Experiment.RESULTS]['total'])

    def testRunTwo( self ):
        '''Test that a simple experiment runs against a 2D parameter space.'''
        n = 10

        r = numpy.arange(0, n)
        self._lab['a'] = r
        self._lab['b'] = r
        self._lab.runExperiment(SampleExperiment())
        res = self._lab.results()

        # check that the whole parameter space has a result
        self.assertEqual(len(res), n * n)
        for p in res:
            self.assertIn(p[Experiment.PARAMETERS]['a'], r)
            self.assertIn(p[Experiment.PARAMETERS]['b'], r)

        # check that each result corresponds to its parameter
        for p in res:
            self.assertEqual(p[Experiment.PARAMETERS]['a'] + p[Experiment.PARAMETERS]['b'], p[Experiment.RESULTS]['total'])

    def testReady(self):
        '''Test we can check readiness correctly.'''
        n = 10

        r = numpy.arange(0, n)
        self._lab['a'] = r
        self._lab['b'] = r
        self._lab.runExperiment(SampleExperiment())
        self.assertTrue(self._lab.ready())
        self.assertEqual(self._lab.readyFraction(), 1.0)

    def testSinglePoint( self ):
        '''Test that using a single point as a range still works.'''
        n = 100

        r = numpy.arange(0, n)
        self._lab['a'] = r
        self._lab['b'] = 0
        self._lab.runExperiment(SampleExperiment())
        res = self._lab.results()

        # check that the whole parameter space has a result
        self.assertEqual(len(res), n)
        for p in res:
            self.assertIn(p[Experiment.PARAMETERS]['a'], r)
            self.assertEqual(p[Experiment.PARAMETERS]['b'], 0)

        # check that each result corresponds to its parameter
        for p in res:
            self.assertEqual(p[Experiment.PARAMETERS]['a'] + p[Experiment.PARAMETERS]['b'], p[Experiment.RESULTS]['total'])

    def testStringsNotUnpacked( self ):
        '''Test we don't unpack strings, even though they're iterable'''
        v = 'A string'

        self._lab['s'] = v
        self._lab.runExperiment(NullExperiment())
        res = self._lab.results()
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0][Experiment.RESULTS]['result'], v)

    def testContains(self):
        '''Test the contains operator.'''
        self._lab['a'] = 10
        self._lab['b'] = range(10)
        self.assertIn('a', self._lab)
        self.assertIn('b', self._lab)
        del self._lab['a']
        self.assertNotIn('a', self._lab)
        self.assertIn('b', self._lab)

    def testDeletion(self):
        '''Test we can delete parameters.'''
        self.assertCountEqual(self._lab.parameters(), [])

        # delete one
        self._lab['a'] = 10
        self._lab['b'] = range(10)
        self.assertCountEqual(self._lab.parameters(), ['a', 'b'])
        del self._lab['a']
        self.assertCountEqual(self._lab.parameters(), ['b'])

        # delete all
        self._lab['c'] = range(10)
        self._lab.deleteAllParameters()
        self.assertCountEqual(self._lab.parameters(), [])

    def testLength(self):
        '''Test lengths of the various designs.'''

        # under a factorial design
        self._lab = Lab(design=FactorialDesign())
        self._lab['a'] = range(10)
        self._lab['b'] = range(20)
        self.assertEqual(len(self._lab), len(self._lab['a']) * len(self._lab['b']))

        # under a pointwise design
        self._lab = Lab(design=PointwiseDesign())
        self._lab['a'] = range(10)
        self._lab['b'] = range(10)
        self.assertEqual(len(self._lab), len(self._lab['a']))


    # ---------- createWith ----------

    def _resultsdict(self):
        '''Set up a results dict populated with plausible metadata.'''
        _rc = Experiment.resultsdict()
        _rc[Experiment.METADATA][Experiment.EXPERIMENT] = str(self.__class__)
        _rc[Experiment.METADATA][Experiment.START_TIME] = datetime.now()
        _rc[Experiment.METADATA][Experiment.END_TIME] = datetime.now()
        _rc[Experiment.METADATA][Experiment.SETUP_TIME] = 10
        _rc[Experiment.METADATA][Experiment.EXPERIMENT_TIME] = 20
        _rc[Experiment.METADATA][Experiment.TEARDOWN_TIME] = 10
        _rc[Experiment.METADATA][Experiment.ELAPSED_TIME] = 40
        _rc[Experiment.METADATA][Experiment.STATUS] = True
        return _rc

    def create(self, lab):
        '''Create some results into the current result set.'''
        rc1 = self._resultsdict()
        rc1[Experiment.PARAMETERS]['a'] = 1
        rc1[Experiment.PARAMETERS]['b'] = 2
        rc1[Experiment.RESULTS]['first'] = 3
        self._lab.notebook().addResult(rc1)

    def createFail(self, lab):
        '''Fail to create results.'''
        raise Exception('Failed!')

    def createEmpty(self, lab):
        '''Test we have no parameters in the lab.'''
        self.assertEqual(len(lab.parameters()), 0)

    def createMess(self, lab):
        '''Delete the result set we were expecting to revert to.'''
        lab.notebook().deleteResultSet('one')
        raise Exception('Failed (after creating mess)!')

    def testBasicCreateWith(self):
        '''Test createWith works.'''
        rc = self._lab.createWith('test1', self.create, description='A first set')
        self.assertTrue(rc)
        self.assertEqual(self._lab.notebook().current().description(), 'A first set')
        self.assertIn('test1', self._lab.notebook().resultSets())
        self.assertFalse(self._lab.notebook().current().isLocked())

    def testCreateWithFinishes(self):
        '''Test createWith finishes a result set when requested.'''
        rc = self._lab.createWith('test1', self.create, finish=True)
        self.assertTrue(rc)
        self.assertTrue(self._lab.notebook().current().isLocked())

    def testCreateWithFail(self):
        '''Test createWith handles deletion on failure.'''
        with self.assertRaises(Exception):
            rc = self._lab.createWith('test1', self.createFail)
        self.assertNotIn('test1', self._lab.notebook().resultSets())

    def testCreateWithFailNoDelete(self):
        '''Test createWith can be prevented from deleting on failure.'''
        with self.assertRaises(Exception):
            rc = self._lab.createWith('test1', self.createFail, delete=False)
        self.assertIn('test1', self._lab.notebook().resultSets())
        self.assertFalse(self._lab.notebook().current().isLocked())

    def testCreateWithFailNoDeleteNotFinished(self):
        '''Test createWith doesn't lock a partial result set.'''
        with self.assertRaises(Exception):
            rc = self._lab.createWith('test1', self.createFail,
                                      delete=False, finish=True)
        self.assertIn('test1', self._lab.notebook().resultSets())
        self.assertFalse(self._lab.notebook().current().isLocked())

    def testCreateWithNoPropagate(self):
        '''Test createWith hides the exception on failure.'''
        rc = self._lab.createWith('test1', self.createFail, propagate=False)
        self.assertFalse(rc)
        self.assertNotIn('test1', self._lab.notebook().resultSets())

    def testClearParameterSpace(self):
        '''Test the parameter space is blanked before calling the creation function.'''
        self._lab['a'] = 10
        rc = self._lab.createWith('test1', self.createEmpty)

    def testDontClearParameterSpace(self):
        '''Test the parameter space blanking can be inhibited.'''
        self._lab['a'] = 10
        with self.assertRaises(Exception):
            rc = self._lab.createWith('test1', self.createEmpty,
                                      deleteAllParameters=False)

    def testRevertResultSetOnFailure(self):
        '''Test we revert to the correct result set on failure.'''
        self._lab.notebook().addResultSet('one')
        self._lab.notebook().addResultSet('two')
        self._lab.notebook().select('one')
        with self.assertRaises(Exception):
            rc = self._lab.createWith('test1', self.createFail)
        self.assertEqual(self._lab.notebook().currentTag(), 'one')
        self.assertCountEqual(self._lab.notebook().resultSets(),
                              ['one', 'two', LabNotebook.DEFAULT_RESULTSET])

    def testMess(self):
        '''Test we deal with reversion problems.'''
        self._lab.notebook().addResultSet('one')
        self.assertCountEqual(self._lab.notebook().resultSets(),
                              ['one', LabNotebook.DEFAULT_RESULTSET])
        with self.assertRaises(Exception):
            rc = self._lab.createWith('test1', self.createMess)
        self.assertEqual(self._lab.notebook().currentTag(), LabNotebook.DEFAULT_RESULTSET)
        self.assertCountEqual(self._lab.notebook().resultSets(),
                              [LabNotebook.DEFAULT_RESULTSET])


if __name__ == '__main__':
    unittest.main()
