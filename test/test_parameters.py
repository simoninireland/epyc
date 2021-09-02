# Tests of setting parameters from within experiments
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


class SampleExperiment1(Experiment):
    '''Update parameters from do().'''

    def do(self, params):
        params['k'] = 10
        return dict()


class SampleExperiment2(Experiment):
    '''Update parameters from setUp().'''

    def setUp(self, params):
        super().setUp(params)
        params['k'] = 20


class TestParameterUpdate(unittest.TestCase):

    def testFromDo(self):
        '''Test we can update parameters from do().'''
        params = dict()
        params['a'] = 1
        e = SampleExperiment1()
        rc = e.set(params).run()
        self.assertEqual(rc[Experiment.PARAMETERS]['a'], 1)
        self.assertIn('k', rc[Experiment.PARAMETERS])
        self.assertEqual(rc[Experiment.PARAMETERS]['k'], 10)

    def testFromSetUp(self):
        '''Test we can update parameters from setUp().'''
        params = dict()
        params['a'] = 1
        e = SampleExperiment2()
        rc = e.set(params).run()
        self.assertEqual(rc[Experiment.PARAMETERS]['a'], 1)
        self.assertIn('k', rc[Experiment.PARAMETERS])
        self.assertEqual(rc[Experiment.PARAMETERS]['k'], 20)


if __name__ == '__main__':
    unittest.main()
