# Tests of in-memory notebooks
#
# Copyright (C) 2016 Simon Dobson
# 
# Licensed under the GNU General Public Licence v.2.0
#

from epyc import *

import unittest
import os


class SampleExperiment(Experiment):
    '''A very simple experiment that adds up its parameters.'''

    def do( self, param ):
        total = 0
        for k in param:
            total = total + param[k]
        return dict(total = total)

    
class LabNotebookTests(unittest.TestCase):

    def testEmptyNotebook( self ):
        '''Test creating an empty notebook'''
        nb = LabNotebook("test")
        self.assertEqual(nb.name(), "test")
        self.assertFalse(nb.isPersistent())
        
    def testAddingResult( self ):
        '''Test adding and retrieving a result'''
        nb = LabNotebook()

        e = SampleExperiment()
        params = dict(a  = 1, b = 2)
        rc = e.set(params).run()

        nb.addResult(rc)

        self.assertNotEqual(nb.resultsFor(params), [])
        res = nb.results()
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0][Experiment.RESULTS]['total'], params['a'] + params['b'])

    def testPermuteParameters( self ):
        '''Test parameters are normalised properly.'''
        nb = LabNotebook()

        e = SampleExperiment()
        params1 = dict(a  = 1, b = 2)
        rc = e.set(params1).run()

        nb.addResult(rc)
        self.assertNotEqual(nb.resultsFor(params1), [])

        params2 = dict(b = 2, a  = 1)
        self.assertNotEqual(nb.resultsFor(params2), [])

        self.assertEqual(nb.resultsFor(params1), nb.resultsFor(params2))

    def testLatestResults( self ):
        '''Check that latest result works properly.'''
        nb = LabNotebook()

        e = SampleExperiment()
        params1 = dict(a  = 1, b = 2)
        rc = e.set(params1).run()

        self.assertEqual(nb.resultsFor(params1), [])
        self.assertEqual(nb.latestResultsFor(params1), None)

        nb.addResult(rc)
        self.assertEqual(len(nb.resultsFor(params1)), 1)
        self.assertEqual(nb.latestResultsFor(params1), rc)
        
    def testAddingPendingResult( self ):
        '''Test adding, finalising, and retrieving a pending result'''
        nb = LabNotebook()

        e = SampleExperiment()
        params = dict(a  = 1, b = 2)
        rc = e.set(params).run()
        
        nb.addPendingResult(params, 1)
        self.assertEqual(nb.resultsFor(params), [])
        self.assertEqual(len(nb.results()), 0)
        self.assertEqual(nb.pendingResults(), [ 1 ])

        nb.addResult(rc, 1)
        self.assertEqual(len(nb.resultsFor(params)), 1)
        self.assertEqual((nb.resultsFor(params))[0], rc)
        self.assertEqual(len(nb.results()), 1)
        self.assertEqual(len(nb.pendingResults()), 0)

    def testCancellingPendingResult( self ):
        '''Test cancelling a pending result'''
        nb = LabNotebook()

        params = dict(a  = 1, b = 2)
        nb.addPendingResult(params, 1)
        self.assertEqual(nb.resultsFor(params), [])
        self.assertEqual(len(nb.results()), 0)
        self.assertEqual(nb.pendingResults(), [ 1 ])

        nb.cancelPendingResult(1)
        self.assertEqual(nb.resultsFor(params), [])
        self.assertEqual(len(nb.results()), 0)
        self.assertEqual(len(nb.pendingResults()), 0)

    def testCancellingAllPendingResult( self ):
        '''Test cancelling of all pending result'''
        nb = LabNotebook()

        params1 = dict(a  = 1, b = 2)
        params2 = dict(a  = 1, b = 3)
        nb.addPendingResult(params1, 1)
        nb.addPendingResult(params2, 2)
        self.assertEqual(nb.resultsFor(params1), [])
        self.assertEqual(nb.resultsFor(params2), [])
        self.assertEqual(len(nb.results()), 0)
        self.assertIn(1, nb.pendingResults())
        self.assertIn(2, nb.pendingResults())

        nb.cancelAllPendingResults()
        self.assertEqual(nb.resultsFor(params1), [])
        self.assertEqual(len(nb.results()), 0)
        self.assertEqual(len(nb.pendingResults()), 0)
    
    def testRealAndPendingResults( self ):
        '''Test a sequence of real and pending results'''
        nb = LabNotebook()

        e = SampleExperiment()
        
        params1 = dict(a  = 1, b = 2)
        rc1 = e.set(params1).run()
        params2 = dict(a  = 10, b = 12)
        rc2 = e.set(params2).run()
        params3 = dict(a  = 45, b = 11)
        rc3 = e.set(params3).run()

        nb.addResult(rc1)
        self.assertEqual((nb.resultsFor(params1))[0], rc1)
        self.assertEqual(nb.resultsFor(params2), [])
        self.assertEqual(len(nb.results()), 1)
        self.assertEqual(nb.pendingResults(), [])
        
        nb.addPendingResult(params2, 2)
        self.assertEqual((nb.resultsFor(params1))[0], rc1)
        self.assertEqual(nb.resultsFor(params2), [])
        self.assertEqual(len(nb.results()), 1)
        self.assertEqual(nb.pendingResults(), [ 2 ])
        
        nb.addPendingResult(params3, 3)
        self.assertEqual((nb.resultsFor(params1))[0], rc1)
        self.assertEqual(nb.resultsFor(params2), [])
        self.assertEqual(nb.resultsFor(params3), [])
        self.assertEqual(len(nb.results()), 1)
        self.assertItemsEqual(nb.pendingResults(), [ 2, 3 ])

        nb.addResult(rc2, 2)
        self.assertEqual((nb.resultsFor(params1))[0], rc1)
        self.assertEqual((nb.resultsFor(params2))[0], rc2)
        self.assertEqual(nb.resultsFor(params3), [])
        self.assertEqual(len(nb.results()), 2)
        self.assertEqual(nb.pendingResults(), [ 3 ])

        nb.cancelPendingResult(3)
        self.assertEqual((nb.resultsFor(params1))[0], rc1)
        self.assertEqual((nb.resultsFor(params2))[0], rc2)
        self.assertEqual(nb.resultsFor(params3), [])
        self.assertEqual(len(nb.results()), 2)
        self.assertEqual(nb.pendingResults(), [])

        nb.addPendingResult(params3, 3)
        self.assertEqual((nb.resultsFor(params1))[0], rc1)
        self.assertEqual((nb.resultsFor(params2))[0], rc2)
        self.assertEqual(nb.resultsFor(params3), [])
        self.assertEqual(len(nb.results()), 2)
        self.assertEqual(nb.pendingResults(), [ 3 ])

        nb.cancelPendingResult(3)
        self.assertEqual((nb.resultsFor(params1))[0], rc1)
        self.assertEqual((nb.resultsFor(params2))[0], rc2)
        self.assertEqual(nb.resultsFor(params3), [])
        self.assertEqual(len(nb.results()), 2)
        self.assertEqual(nb.pendingResults(), [])

    def testCancellingAllPendingResults( self ):
        '''Test all results get cancelled properly.'''
        nb = LabNotebook()

        e = SampleExperiment()
        
        params1 = dict(a  = 1, b = 2)
        rc1 = e.set(params1).run()
        params2 = dict(a  = 10, b = 12)
        rc2 = e.set(params2).run()
        rc3 = e.set(params2).run()

        nb.addPendingResult(params1, 1)
        nb.addPendingResult(params2, 2)
        nb.addPendingResult(params2, 3)
        self.assertItemsEqual(nb.pendingResultsFor(params1), [ 1 ])
        self.assertItemsEqual(nb.pendingResultsFor(params2), [ 2, 3 ])
        self.assertItemsEqual(nb.pendingResults(), [ 1, 2, 3 ])

        nb.cancelAllPendingResultsFor(params2)
        self.assertItemsEqual(nb.pendingResultsFor(params1), [ 1 ])
        self.assertEqual(nb.pendingResultsFor(params2), [])
        self.assertItemsEqual(nb.pendingResults(), [ 1 ])

        nb.cancelAllPendingResults()
        self.assertEqual(nb.pendingResultsFor(params1), [])
        self.assertEqual(nb.pendingResultsFor(params2), [])
        self.assertEqual(nb.pendingResults(), [])

    def testAddResultList( self ):
        '''Test adding several results at once.'''
        nb = LabNotebook()

        e = SampleExperiment()
        
        params1 = dict(a  = 1, b = 2)
        rc1 = e.set(params1).run()
        params2 = dict(a  = 10, b = 12)
        rc2 = e.set(params2).run()
        rc3 = e.set(params2).run()

        nb.addResult([ rc1, rc2, rc3 ])
        self.assertEqual(nb.latestResultsFor(params1), rc1)
        self.assertItemsEqual(nb.resultsFor(params2), [ rc2, rc3 ])
        self.assertEqual(nb.latestResultsFor(params2), rc3)
        
        
    def testDataFrame( self ):
        '''Test creating a pandas DataFrame'''
        nb = LabNotebook()

        e = SampleExperiment()
        params1 = dict(a  = 1, b = 2)
        rc1 = e.set(params1).run()
        params2 = dict(a  = 10, b = 12)
        rc2 = e.set(params2).run()
        params3 = dict(a  = 45, b = 11)
        #rc4 = e.set(params2).run()

        nb.addResult(rc1)
        nb.addResult(rc2)
        nb.addPendingResult(params3, 1)
        #nb.addResult(rc4)

        df = nb.dataframe()

        self.assertTrue(len(df['a']), 2)
        self.assertTrue(len(df['b']), 2)
        self.assertTrue(len(df['total']), 2)
        self.assertEqual(df[df['a'] == 1]['b'].iloc[0], 2)
        self.assertEqual(df[df['b'] == 12]['a'].iloc[0], 10)
        self.assertEqual(df[(df['a'] == 10) & (df['b'] == 12)]['total'].iloc[0], 10 + 12)
        
