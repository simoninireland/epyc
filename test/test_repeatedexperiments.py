# Tests of repeated experiments combinator
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


class SampleExperiment1(Experiment):
        
    def do( self, params ):
        return dict(result = params['x'])

    
class RepeatedExperimentTests(unittest.TestCase):

    def setUp( self ):
        self._lab = Lab()
        
    def testRepetitionsOnePoint( self ):
        '''Test we can repeat an experiment at a single point'''
        N = 10
        
        self._lab['x'] = [ 5 ]
        
        e = SampleExperiment1()
        er = RepeatedExperiment(e, N)

        self._lab.runExperiment(er)
        self.assertTrue(er.success())

        df = self._lab.dataframe()
        self.assertEqual(len(df), N * len(self._lab['x']))
        self.assertTrue(df['result'].eq(self._lab['x'][0]).all())
        self.assertTrue(df[RepeatedExperiment.REPETITIONS].eq(N).all())
        self.assertCountEqual(df[RepeatedExperiment.I].values, range(N))
        
    def testRepetitionsMultiplePoint( self ):
        '''Test we can repeat an experiment across a parameter space'''
        N = 10
        
        self._lab['x'] = [ 5, 10, 15 ]
        
        e = SampleExperiment1()
        er = RepeatedExperiment(e, N)

        self._lab.runExperiment(er)
        self.assertTrue(er.success())

        df = self._lab.dataframe()
        self.assertEqual(len(df), N * len(self._lab['x']))

        for x in self._lab['x']:
            dfx = df[df['x'] == x]
            self.assertEqual(len(dfx), N)
            self.assertTrue(dfx['result'].eq(x).all())
            self.assertTrue(dfx[RepeatedExperiment.REPETITIONS].eq(N).all())
            self.assertCountEqual(dfx[RepeatedExperiment.I].values, range(N))

    # TODO: check nesting for repeated repetitions

if __name__ == '__main__':
    unittest.main()


