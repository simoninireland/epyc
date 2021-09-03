# Tests of local-parallel lab class
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
from multiprocessing import cpu_count


class SampleExperiment(Experiment):
    '''A very simple experiment that adds up its parameters.'''

    def do( self, param ):
        total = 0
        for k in param:
            total = total + param[k]
        return dict(total = total)


class SampleExperiment1(SampleExperiment):
    '''An experiment that adds a parameter.'''

    def setUp(self, params):
        super().setUp(params)
        params['additional'] = 10


class ParallelLabTests(unittest.TestCase):

    def testCoresSelection(self):
        '''Test that core selection works as expected.'''

        # default
        self._lab = ParallelLab()
        self.assertEqual(self._lab.numberOfCores(), cpu_count())

        # zero is the same
        self._lab = ParallelLab(cores=0)
        self.assertEqual(self._lab.numberOfCores(), cpu_count())

        # fixed numbers, possibly more than we have physical cores (which
        # will be capped)
        for i in range(1, cpu_count() + 2):
            self._lab = ParallelLab(cores=i)
            self.assertEqual(self._lab.numberOfCores(), min(i, cpu_count()))

    @unittest.skipIf(cpu_count() < 2, 'Need multiple cores to check free core selection')
    def testFreeCoresSelection(self):
        '''Test we can leave cores free.'''
        maxcores = cpu_count()

        # check we leave cores free
        for i in range(1, maxcores - 1):
            self._lab = ParallelLab(cores=-i)    # leave i cores free
            self.assertEqual(self._lab.numberOfCores(), maxcores - i)

        # check we always have at least 1
        self._lab = ParallelLab(cores=-(maxcores + 1))
        self.assertEqual(self._lab.numberOfCores(), 1)

    def testSequential(self):
        '''Test a sequential run.'''
        self._lab = ParallelLab(cores=1)
        self._lab['k'] = range(10)
        self._lab.runExperiment(SampleExperiment())

        # check what we got back
        rcs = self._lab.results()
        self.assertEqual(len(rcs), 10)
        self.assertCountEqual(list(map(lambda rc: rc[Experiment.RESULTS]['total'], rcs)), range(10))

    @unittest.skipIf(cpu_count() < 2, 'Need multiple cores to check parallel execution')
    def testParallel(self):
        '''Test we can run in parallel.'''
        self._lab = ParallelLab()
        self._lab['k'] = range(10)
        self._lab.runExperiment(SampleExperiment())

        # check what we got back
        rcs = self._lab.results()
        self.assertEqual(len(rcs), 10)
        self.assertCountEqual(list(map(lambda rc: rc[Experiment.RESULTS]['total'], rcs)), range(10))

    def testAddParameters(self):
        '''Test that adding experimental parameters works.'''
        self._lab = ParallelLab()
        self._lab['k'] = range(10)
        self._lab.runExperiment(SampleExperiment1())

        # check what we got back
        rcs = self._lab.results()
        self.assertEqual(len(rcs), 10)
        for rc in rcs:
            self.assertIn('additional', rc[Experiment.PARAMETERS])
        self.assertCountEqual(list(map(lambda rc: rc[Experiment.RESULTS]['total'], rcs)),
                              [i + 10 for i in range(10)])


if __name__ == '__main__':
    unittest.main()
