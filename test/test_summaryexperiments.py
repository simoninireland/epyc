# Tests of summarising experiments combinator
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
import os
from tempfile import NamedTemporaryFile


class SampleExperiment1(Experiment):

    def do( self, params ):
        return dict(result = params['x'],
                    dummy = 1)


class SampleExperiment2(Experiment):

    def __init__( self ):
        super(SampleExperiment2, self).__init__()
        self._rng = numpy.random.default_rng()
        self._allvalues = []

    def do( self, params ):
        v = self._rng.random()
        self._allvalues.append(v)
        return dict(result = v)

    def values( self ):
        return self._allvalues


class SampleExperiment3(SampleExperiment2):

    def __init__( self ):
        super(SampleExperiment3, self).__init__()
        self._ran = 0

    def do( self, params ):
        v = self._rng.random()
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


class SampleExperiment4(Experiment):
    '''A more exercising experiment.'''

    def do( self, param ):
        total = 0
        for k in param:
            total = total + param[k]
        return dict(total = total,
                    nestedArray = [ 1, 2, 3 ],
                    nestedDict = dict(a = 1, b = 'two'))


class SampleExperiment5(Experiment):

    def __init__( self ):
        super(SampleExperiment5, self).__init__()
        self._rng = numpy.random.default_rng()
        self._values = []

    def do( self, params ):
        v = self._rng.random()
        self._values.append(v)
        return dict(result = v)


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
        self.assertTrue(es.success())
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
        self.assertTrue(es.success())
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
        self.assertTrue(es.success())
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
        self.assertTrue(es.success())
        res = (self._lab.results())[0]

        self.assertTrue(res[Experiment.METADATA][Experiment.STATUS])
        self.assertCountEqual(res[Experiment.RESULTS].keys(), [ 'dummy_mean',
                                                                'dummy_median',
                                                                'dummy_variance',
                                                                'dummy_min',
                                                                'dummy_max' ])
        self.assertEqual(res[Experiment.RESULTS]['dummy_mean'], 1)
        self.assertEqual(res[Experiment.RESULTS]['dummy_median'], 1)
        self.assertEqual(res[Experiment.RESULTS]['dummy_variance'], 0)
        self.assertEqual(res[Experiment.RESULTS]['dummy_min'], 1)
        self.assertEqual(res[Experiment.RESULTS]['dummy_max'], 1)

    def testIgnoring( self ):
        '''Test that we ignore failed experiments'''
        N = 10

        self._lab['x'] = [ 5 ]

        e = SampleExperiment3()
        es = SummaryExperiment(RepeatedExperiment(e, N))

        self._lab.runExperiment(es)
        self.assertTrue(es.success())
        res = (self._lab.results())[0]

        self.assertTrue(res[Experiment.METADATA][Experiment.STATUS])
        self.assertEqual(res[Experiment.METADATA][SummaryExperiment.UNDERLYING_RESULTS], N)
        self.assertEqual(res[Experiment.METADATA][SummaryExperiment.UNDERLYING_SUCCESSFUL_RESULTS], e.ran())
        self.assertEqual(res[Experiment.RESULTS]['result_mean'],
                         numpy.mean(e.values()))
        self.assertEqual(res[Experiment.RESULTS]['result_variance'],
                         numpy.var(e.values()))

    def testSingle( self ):
        '''Test against a non-list-returning underlying experiment.'''

        self._lab['x'] = [ 5 ]

        e = SampleExperiment1()
        es = SummaryExperiment(e)

        self._lab.runExperiment(es)
        self.assertTrue(es.success())
        self.assertEqual(len(self._lab.results()), 1)
        res = (self._lab.results())[0]

        self.assertTrue(res[Experiment.METADATA][Experiment.STATUS])
        self.assertEqual(res[Experiment.METADATA][SummaryExperiment.UNDERLYING_RESULTS], 1)
        self.assertEqual(res[Experiment.METADATA][SummaryExperiment.UNDERLYING_SUCCESSFUL_RESULTS], 1)

    def testJSON( self ):
        '''Test that we can persist repeated results in JSON format.'''

        # reset the lab we're using to use a JSON notebook
        tf = NamedTemporaryFile()
        tf.close()
        self._lab = Lab(notebook = JSONLabNotebook(tf.name, create = True))

        repetitions = 5
        self._lab['a'] = [ 1, 2, 3 ]
        try:
            re = RepeatedExperiment(SampleExperiment4(),
                                    repetitions)
            self._lab.runExperiment(SummaryExperiment(re,
                                                      summarised_results = [ 'total', 'nestedArray' ]))

            self.assertTrue(re.success())
            res = self._lab.results()

            # getting here is enough to exercise the persistence regime
        finally:
            try:
                os.remove(tf.name)
            except OSError:
                pass

    def testSummaryExceptions( self ):
        '''Test we handle illegal summary keys.'''
        N = 10

        self._lab['x'] = 'hello'

        e = SampleExperiment1()
        es = SummaryExperiment(RepeatedExperiment(e, N))

        self._lab.runExperiment(es)
        self.assertEqual(len(self._lab.results()), 1)
        rc = (self._lab.results())[0]
        self.assertNotIn(es._mean('e'), rc[Experiment.RESULTS])

    def testNoPoint( self ):
        '''Test we do nothing if we have an empty parameter space.'''
        e = SampleExperiment5()
        self._lab.runExperiment(e)
        self.assertEqual(len(self._lab.results()), 0)

    def testExtrema( self ):
        '''Test we capture the extrema correctly.'''
        N = 10
        self._lab['x'] = [ 5 ]    # dummy data point, we don't use it

        e = SampleExperiment5()
        es = SummaryExperiment(RepeatedExperiment(e, N))

        self._lab.runExperiment(es)
        self.assertTrue(es.success())
        res = (self._lab.results())[0]

        self.assertEqual(res[Experiment.METADATA][SummaryExperiment.UNDERLYING_SUCCESSFUL_RESULTS], 10)
        self.assertEqual(res[Experiment.RESULTS]['result_min'], numpy.min(e._values))
        self.assertEqual(res[Experiment.RESULTS]['result_max'], numpy.max(e._values))
