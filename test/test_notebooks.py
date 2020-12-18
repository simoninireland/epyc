# Tests of in-memory notebooks
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
from datetime import datetime

    
class LabNotebookTests(unittest.TestCase):

    def setUp(self):
        '''Set up a notebook.'''
        self._nb = LabNotebook()

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

    def testEmptyNotebook( self ):
        '''Test creating an empty notebook'''
        nb = LabNotebook("test")
        self.assertEqual(nb.name(), "test")
        self.assertFalse(nb.isPersistent())
        
    def testOneResultSet(self):
        '''Test we can ignore result sets if we want to.'''
        self.assertIsNotNone(self._nb.current())
        self.assertCountEqual(self._nb.resultSets(), [ LabNotebook.DEFAULT_RESULTSET ])

    def testAddingResultSets(self):
        '''Test we can add result sets .'''
        self._nb.addResultSet('second')
        self.assertCountEqual(self._nb.resultSets(), [ LabNotebook.DEFAULT_RESULTSET, 'second' ])
        self.assertEqual(self._nb.numberOfResultSets(), 2)
        self.assertEqual(len(self._nb), 2)

    def _resultsEqual(self, df, rc):
        '''Check that the dataframe contains a row with the given results.

        :param df: the dataframe
        :param rc: the results dict
        :returns: True if there's a corresponding row'''
        for d in [ Experiment.PARAMETERS, Experiment.RESULTS ]:  # ignore metadata
            for k in rc[d].keys():
                df = df[df[k] == rc[d][k]]
        return (len(df) > 0)

    def testDifferentParameters(self):
        '''Test different rule sets maintain different parameter sets.'''
        rc1 = self._resultsdict()
        rc1[Experiment.PARAMETERS]['a'] = 1
        rc1[Experiment.PARAMETERS]['b'] = 2
        rc1[Experiment.RESULTS]['first'] = 3
        self._nb.addResult(rc1)

        self._nb.addResultSet('other')
        rc2 = self._resultsdict()
        rc2[Experiment.PARAMETERS]['c'] = 6
        rc2[Experiment.PARAMETERS]['b'] = 1
        rc2[Experiment.RESULTS]['second'] = 12
        self._nb.addResult(rc2)

        self._nb.select(LabNotebook.DEFAULT_RESULTSET)
        self.assertTrue(self._resultsEqual(self._nb.current().dataframeFor(rc1[Experiment.PARAMETERS]), rc1))
        with self.assertRaises(Exception):
            self._nb.resultsFor(rc2[Experiment.PARAMETERS])

        self._nb.select('other')
        self.assertTrue(self._resultsEqual(self._nb.current().dataframeFor(rc2[Experiment.PARAMETERS]), rc2))
        with self.assertRaises(Exception):
            self._nb.resultsFor(rc1[Experiment.PARAMETERS])
        
    def testPendingResultsAreNotified(self):
        '''Test the notebook records pending results correctly.'''
        rc1 = self._resultsdict()
        rc1[Experiment.PARAMETERS]['a'] = 1
        rc1[Experiment.PARAMETERS]['b'] = 2
        rc1[Experiment.RESULTS]['first'] = 3

        self._nb.addPendingResult(rc1[Experiment.PARAMETERS], '1234')
        self.assertFalse(self._nb.ready())

        self._nb.resolvePendingResult(rc1, '1234')
        with self.assertRaises(Exception):
            self._nb.resolvePendingResult(rc1, '1234')
        self.assertTrue(self._nb.ready())

        self._nb.addPendingResult(rc1[Experiment.PARAMETERS], '4567')
        self._nb.cancelPendingResult('4567')
        with self.assertRaises(Exception):
            self._nb.resolvePendingResult(rc1, '4567')
        self.assertTrue(self._nb.ready())

    def testDataframe(self):
        '''Test dataframe access gets all results and respects success flag.'''
        rc1 = self._resultsdict()
        rc1[Experiment.METADATA][Experiment.STATUS] = True
        rc1[Experiment.PARAMETERS]['a'] = 1
        rc1[Experiment.PARAMETERS]['b'] = 2
        rc1[Experiment.RESULTS]['first'] = 3
        self._nb.addResult(rc1)
        rc1[Experiment.PARAMETERS]['b'] = 6
        rc1[Experiment.RESULTS]['first'] = 12
        self._nb.addResult(rc1)
        rc1[Experiment.METADATA][Experiment.STATUS] = False
        rc1[Experiment.PARAMETERS]['b'] = 8
        del rc1[Experiment.RESULTS]['first']
        self._nb.addResult(rc1)

        self.assertEqual(self._nb.numberOfResults(), 3)
        self.assertEqual(len(self._nb.results()), 3)
        self.assertEqual(len(self._nb.dataframe(only_successful=False)), 3)
        self.assertEqual(len(self._nb.dataframe()), 2)

    def testResultFraction(self):
        '''Test we compute the result fractions properly.'''
        rc1 = self._resultsdict()
        rc1[Experiment.PARAMETERS]['a'] = 10
        rc2 = self._resultsdict()
        rc2[Experiment.PARAMETERS]['a'] = 20
        rc3 = self._resultsdict()
        rc3[Experiment.PARAMETERS]['a'] = 30

        # check with only results
        self._nb.addResult(rc1)
        self.assertEqual(self._nb.readyFraction(), 1.0)

        # check with a pending result as well
        self._nb.addPendingResult(rc2[Experiment.PARAMETERS], '1234')
        self.assertEqual(self._nb.readyFraction(), 0.5)

        # check per-result set behaviour
        self._nb.addResultSet('second')
        self.assertEqual(self._nb.readyFraction(), 1.0)
        self._nb.addResult(rc3)
        self._nb.select(LabNotebook.DEFAULT_RESULTSET)
        self.assertEqual(self._nb.readyFraction(), 0.5)

    def testPendingResultsByTag(self):
        '''Test we can identify a result set by tag when querying.'''
        rc1 = self._resultsdict()
        rc1[Experiment.PARAMETERS]['a'] = 10
        rc2 = self._resultsdict()
        rc2[Experiment.PARAMETERS]['a'] = 20
        rc3 = self._resultsdict()
        rc3[Experiment.PARAMETERS]['a'] = 30

        # first result set
        self._nb.addResultSet('first')
        self._nb.addResult(rc1)
        self._nb.addResult(rc2)
        self._nb.addPendingResult(rc2[Experiment.PARAMETERS], '1234')

        # second
        self._nb.addResultSet('second')
        self._nb.addResult(rc3)

        # test default and tagged behaviour
        self.assertEqual(self._nb.numberOfResults(), 1)
        self.assertEqual(self._nb.numberOfPendingResults(), 0)
        self.assertEqual(self._nb.numberOfResults('first'), 2)
        self.assertEqual(self._nb.numberOfPendingResults('first'), 1)
        self.assertEqual(self._nb.numberOfResults('second'), 1)
        self.assertEqual(self._nb.numberOfPendingResults('second'), 0)
        self.assertEqual(len(self._nb.pendingResults()), 0)
        self.assertEqual(len(self._nb.pendingResults('first')), 1)

    def testAllPendingResults(self):
        '''Test we can retrieve all the penging results from across a notebook.'''
        rc1 = self._resultsdict()
        rc1[Experiment.PARAMETERS]['a'] = 10
        rc2 = self._resultsdict()
        rc2[Experiment.PARAMETERS]['a'] = 20
        rc3 = self._resultsdict()
        rc3[Experiment.PARAMETERS]['a'] = 30
        rc4 = self._resultsdict()
        rc4[Experiment.PARAMETERS]['a'] = 40

        # first result set
        self._nb.addResultSet('first')
        self._nb.addResult(rc1)
        self._nb.addResult(rc2)
        self._nb.addPendingResult(rc2[Experiment.PARAMETERS], '1234')

        # second
        self._nb.addResultSet('second')
        self._nb.addResult(rc3)
        self._nb.addPendingResult(rc4[Experiment.PARAMETERS], '2345')

        # check we get them all
        self.assertCountEqual(self._nb.allPendingResults(), ['1234', '2345'])
        self.assertEqual(self._nb.numberOfAllPendingResults(), 2)

    def testTaggedResultsAndDataframes(self):
        '''Test we can retrieve correctly from different result sets.'''
        rc1 = self._resultsdict()
        rc1[Experiment.PARAMETERS]['a'] = 10
        rc2 = self._resultsdict()
        rc2[Experiment.PARAMETERS]['a'] = 20
        rc3 = self._resultsdict()
        rc3[Experiment.PARAMETERS]['a'] = 30
        rc4 = self._resultsdict()
        rc4[Experiment.PARAMETERS]['a'] = 40

        # first result set
        self._nb.addResultSet('first')
        self._nb.addResult(rc1)
        self._nb.addResult(rc2)
        self._nb.addPendingResult(rc2[Experiment.PARAMETERS], '1234')

        # second
        self._nb.addResultSet('second')
        self._nb.addResult(rc3)
        self._nb.addPendingResult(rc4[Experiment.PARAMETERS], '2345')

        # check retrieval
        self._nb.select(LabNotebook.DEFAULT_RESULTSET)
        self.assertEqual(len(self._nb.dataframe()), 0)
        self.assertEqual(len(self._nb.dataframe(tag=LabNotebook.DEFAULT_RESULTSET)), 0)
        self.assertEqual(len(self._nb.dataframe(tag='first')), 2)
        self.assertEqual(len(self._nb.dataframe(tag='second')), 1)
        self.assertEqual(len(self._nb.dataframeFor(dict(a=10), tag='first')), 1)
        self.assertEqual(len(self._nb.dataframeFor(dict(a=40), tag='first')), 0)
        self.assertEqual(len(self._nb.results(tag='first')), 2)
        self.assertEqual(len(self._nb.results(tag='second')), 1)
        self.assertEqual(len(self._nb.resultsFor(dict(a=20), tag='first')), 1)
        self.assertEqual(len(self._nb.resultsFor(dict(a=30), tag='first')), 0)

    def testAddList(self):
        '''Test we can add a list of results dicts.'''
        rc1 = self._resultsdict()
        rc1[Experiment.PARAMETERS]['a'] = 10
        rc2 = self._resultsdict()
        rc2[Experiment.PARAMETERS]['a'] = 20
        rc3 = self._resultsdict()
        rc3[Experiment.PARAMETERS]['a'] = 30
        self._nb.addResult([rc1, rc2, rc3])
        self.assertEqual(self._nb.numberOfResults(), 3)
        df = self._nb.dataframe()
        vals = df['a']
        self.assertCountEqual(vals, [10, 20, 30])

    def testAddNested(self):
        '''Test we can add a set of nested results, as we get from a repeated experiment.'''
        rc = self._resultsdict()
        rc1 = self._resultsdict()
        rc1[Experiment.PARAMETERS]['a'] = 10
        rc2 = self._resultsdict()
        rc2[Experiment.PARAMETERS]['a'] = 20
        rc3 = self._resultsdict()
        rc3[Experiment.PARAMETERS]['a'] = 30

        # construct the nested experiment
        rc[Experiment.RESULTS] = [rc1, rc2, rc3]
        self._nb.addResult([rc1, rc2, rc3])

        self.assertEqual(self._nb.numberOfResults(), 3)
        df = self._nb.dataframe()
        vals = df['a']
        self.assertCountEqual(vals, [10, 20, 30])

    def testFinish(self):
        '''Test we can finish (lock) an entire notebook.'''
        rc1 = self._resultsdict()
        rc1[Experiment.PARAMETERS]['a'] = 10
        rc2 = self._resultsdict()
        rc2[Experiment.PARAMETERS]['a'] = 20
        rc3 = self._resultsdict()
        rc3[Experiment.PARAMETERS]['a'] = 30
        rc4 = self._resultsdict()
        rc4[Experiment.PARAMETERS]['a'] = 40

        # first result set
        self._nb.addResultSet('first')
        self._nb.addResult(rc1)
        self._nb.addResult(rc2)

        # second
        self._nb.addResultSet('second')
        self._nb.addResult(rc3)
        self._nb.addPendingResult(rc4[Experiment.PARAMETERS], '2345')

        # lock the notebook
        self._nb.finish()

        # check we can't add new result sets
        with self.assertRaises(LabNotebookLockedException):
            self._nb.addResultSet('third')

        # check the result sets are locked and finished correctly, with
        # any pending results cancelled
        rs = self._nb.select('first')
        self.assertTrue(rs.isLocked())
        self.assertEqual(rs.numberOfResults(), 2)
        rs = self._nb.select('second')
        self.assertTrue(rs.isLocked())
        self.assertEqual(rs.numberOfPendingResults(), 0)
        self.assertEqual(rs.numberOfResults(), 2)
        rcs = self._nb.resultsFor(rc4[Experiment.PARAMETERS])
        self.assertEqual(len(rcs), 1)
        self.assertFalse(rcs[0][Experiment.METADATA][Experiment.STATUS])

# TODO: Test we can add metadata

if __name__ == '__main__':
    unittest.main()

 