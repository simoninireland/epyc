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

from epyc import *

import unittest
import numpy


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


if __name__ == '__main__':
    unittest.main()
