# Tests of standard experimental designs
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


class SampleExperiment(Experiment):

    def do(self, params):
        return dict()


class TestParameterUpdate(unittest.TestCase):

    def setUp(self):
        self._e = SampleExperiment()


    # ---------- General ----------

    def testOverriding(self):
        '''Test we can't call on the base class.'''
        d = Design()
        with self.assertRaises(NotImplementedError):
            d.experiments(self._e, dict)


    # ---------- Factorial design ----------

    def testEmptyFactorial(self):
        '''Test empty factorial design.'''
        params = dict()
        es = FactorialDesign().experiments(self._e, params)
        self.assertCountEqual(es, [])

    def testSingleParameterFactorial(self):
        '''Test single-parameter factorial design.'''
        params = dict(a=range(3))
        es = FactorialDesign().experiments(self._e, params)
        self.assertCountEqual(es, [(self._e, dict(a=0)), (self._e, dict(a=1)), (self._e, dict(a=2))])

    def testTwoParameterFactorial(self):
        '''Test two-parameter factorial design.'''
        params = dict(a=range(3),
                      b=[1, 2])
        es = FactorialDesign().experiments(self._e, params)
        self.assertCountEqual(es, [(self._e, dict(a=0, b=1)), (self._e, dict(a=1, b=1)), (self._e, dict(a=2, b=1)),
                                   (self._e, dict(a=0, b=2)), (self._e, dict(a=1, b=2)), (self._e, dict(a=2, b=2))])

    def testTwoParameterFactorialOneEmpty(self):
        '''Test two-parameter factorial design, one of which is empty.'''
        params = dict(a=range(3),
                      b=[])
        es = FactorialDesign().experiments(self._e, params)
        self.assertCountEqual(es, [(self._e, dict(a=0)), (self._e, dict(a=1)), (self._e, dict(a=2))])

    def testTwoParameterFactorialOnePointwise(self):
        '''Test two-parameter factorial design, one of which is a pointwise value.'''
        params = dict(a=range(3),
                      b=[6])
        es = FactorialDesign().experiments(self._e, params)
        self.assertCountEqual(es, [(self._e, dict(a=0, b=6)), (self._e, dict(a=1, b=6)), (self._e, dict(a=2, b=6))])


    # ---------- Pointwise design ----------

    def testEmptyPointwise(self):
        '''Test empty pointwise design.'''
        params = dict()
        es = PointwiseDesign().experiments(self._e, params)
        self.assertCountEqual(es, [])

    def testSingleParameterPointwise(self):
        '''Test single-parameter pointwise design.'''
        params = dict(a=range(3))
        es = PointwiseDesign().experiments(self._e, params)
        self.assertCountEqual(es, [(self._e, dict(a=0)), (self._e, dict(a=1)), (self._e, dict(a=2))])

    def testTwoParameterPointwise(self):
        '''Test two-parameter pointwise design.'''
        params = dict(a=range(3),
                      b=[4, 5, 6])
        es = PointwiseDesign().experiments(self._e, params)
        self.assertCountEqual(es, [(self._e, dict(a=0, b=4)), (self._e, dict(a=1, b=5)), (self._e, dict(a=2, b=6))])

    def testTwoParameterPointwiseUnequal(self):
        '''Test two-parameter pointwise design with unequal ranges.'''
        params = dict(a=range(3),
                      b=[4, 5])
        with self.assertRaises(DesignException):
            es = PointwiseDesign().experiments(self._e, params)

    def testTwoParameterPointwiseOneExtending(self):
        '''Test two-parameter pointwise design where one parameter is a singleton value.'''
        params = dict(a=range(3),
                      b=[4])
        es = PointwiseDesign().experiments(self._e, params)
        self.assertCountEqual(es, [(self._e, dict(a=0, b=4)), (self._e, dict(a=1, b=4)), (self._e, dict(a=2, b=4))])

    def testThreeParameterPointwiseTwoExtending(self):
        '''Test two-parameter pointwise design where two parameters are singleton values.'''
        params = dict(a=range(3),
                      b=[4],
                      c=[8])
        es = PointwiseDesign().experiments(self._e, params)
        self.assertCountEqual(es, [(self._e, dict(a=0, b=4, c=8)), (self._e, dict(a=1, b=4, c=8)), (self._e, dict(a=2, b=4, c=8))])

    def testThreeParameterPointwiseOneExtending(self):
        '''Test two-parameter pointwise design where two parameters are singleton values.'''
        params = dict(a=range(3),
                      b=[5, 6, 7],
                      c=[8])
        es = PointwiseDesign().experiments(self._e, params)
        self.assertCountEqual(es, [(self._e, dict(a=0, b=5, c=8)), (self._e, dict(a=1, b=6, c=8)), (self._e, dict(a=2, b=7, c=8))])


if __name__ == '__main__':
    unittest.main()
