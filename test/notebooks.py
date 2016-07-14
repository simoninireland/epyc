# Tests of in-memory notebooks
#
# Copyright (C) 2016 Simon Dobson
# 
# Licensed under the GNU General Public Licence v.2.0
#

from epyc import *

import unittest
import os
from tempfile import NamedTemporaryFile


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
        rc = e.runExperiment(params)

        nb.addResult(rc)

        self.assertFalse(nb.resultPending(params))
        self.assertNotEqual(nb.result(params), None)

        params2 = dict(b = 2, a  = 1)
        self.assertNotEqual(nb.result(params2), None)

        res = nb.results()
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0][Experiment.RESULTS]['total'], params['a'] + params['b'])

    def testAddingPendingResult( self ):
        '''Test adding, finalising, and retrieving a pending result'''
        nb = LabNotebook()

        e = SampleExperiment()
        params = dict(a  = 1, b = 2)
        rc = e.runExperiment(params)

        nb.addPendingResult(params, 1)
        self.assertEqual(nb.result(params), None)
        self.assertEqual(len(nb.results()), 0)
        self.assertEqual(nb.pendingResults(), [ 1 ])

        nb.addResult(rc)
        self.assertEqual(nb.result(params), rc)
        self.assertEqual(len(nb.results()), 1)
        self.assertEqual(len(nb.pendingResults()), 0)

    def testCancellingPendingResult( self ):
        '''Test cancelling a pending result'''
        nb = LabNotebook()

        params = dict(a  = 1, b = 2)
        nb.addPendingResult(params, 1)
        self.assertEqual(nb.result(params), None)
        self.assertEqual(len(nb.results()), 0)
        self.assertEqual(nb.pendingResults(), [ 1 ])

        nb.cancelPendingResult(params)
        self.assertEqual(nb.result(params), None)
        self.assertEqual(len(nb.results()), 0)
        self.assertEqual(len(nb.pendingResults()), 0)
    
    def testRealAndPendingResults( self ):
        '''Test a sequence of real and pending results'''
        nb = LabNotebook()

        e = SampleExperiment()
        
        params1 = dict(a  = 1, b = 2)
        rc1 = e.runExperiment(params1)

        params2 = dict(a  = 10, b = 12)
        rc2 = e.runExperiment(params2)

        params3 = dict(a  = 45, b = 11)
        rc3 = e.runExperiment(params3)

        nb.addResult(rc1)
        self.assertEqual(nb.result(params1), rc1)
        self.assertEqual(len(nb.results()), 1)
        self.assertEqual(nb.pendingResults(), [ ])
        
        nb.addPendingResult(params2, 2)
        self.assertEqual(nb.result(params1), rc1)
        self.assertEqual(nb.result(params2), None)
        self.assertEqual(len(nb.results()), 1)
        self.assertEqual(nb.pendingResults(), [ 2 ])
        
        nb.addPendingResult(params3, 3)
        self.assertEqual(nb.result(params1), rc1)
        self.assertEqual(nb.result(params2), None)
        self.assertEqual(nb.result(params3), None)
        self.assertEqual(len(nb.results()), 1)
        self.assertEqual(len(nb.pendingResults()), 2)

        nb.addResult(rc2)
        self.assertEqual(nb.result(params1), rc1)
        self.assertEqual(nb.result(params2), rc2)
        self.assertEqual(nb.result(params3), None)
        self.assertEqual(len(nb.results()), 2)
        self.assertEqual(nb.pendingResults(), [ 3 ])

        nb.cancelPendingResult(3)
        self.assertEqual(nb.result(params1), rc1)
        self.assertEqual(nb.result(params2), rc2)
        self.assertEqual(nb.result(params3), None)
        self.assertEqual(len(nb.results()), 2)
        self.assertEqual(nb.pendingResults(), [ ])

        nb.addPendingResult(params3, 3)
        self.assertEqual(nb.result(params1), rc1)
        self.assertEqual(nb.result(params2), rc2)
        self.assertEqual(nb.result(params3), None)
        self.assertEqual(len(nb.results()), 2)
        self.assertEqual(nb.pendingResults(), [ 3 ])

        nb.cancelPendingResult(params3)
        self.assertEqual(nb.result(params1), rc1)
        self.assertEqual(nb.result(params2), rc2)
        self.assertEqual(nb.result(params3), None)
        self.assertEqual(len(nb.results()), 2)
        self.assertEqual(nb.pendingResults(), [ ])

    def testDataFrame( self ):
        '''Test creating a pandas DataFrame'''
        nb = LabNotebook()

        e = SampleExperiment()
        params1 = dict(a  = 1, b = 2)
        rc1 = e.runExperiment(params1)
        params2 = dict(a  = 10, b = 12)
        rc2 = e.runExperiment(params2)
        params3 = dict(a  = 45, b = 11)

        nb.addResult(rc1)
        nb.addResult(rc2)
        nb.addPendingResult(params3)

        df = nb.dataframe()

        self.assertTrue(len(df['a']), 2)
        self.assertTrue(len(df['b']), 2)
        self.assertTrue(len(df['total']), 2)
        self.assertEqual(df[df['a'] == 1]['b'].iloc[0], 2)
        self.assertEqual(df[df['b'] == 12]['a'].iloc[0], 10)
        self.assertEqual(df[(df['a'] == 10) & (df['b'] == 12)]['total'].iloc[0], 10 + 12)
        
    def testOverwrite( self ):
        '''Test we can't overwrite a result'''
        nb = LabNotebook()

        e = SampleExperiment()
        params1 = dict(a  = 1, b = 2)
        rc1 = e.runExperiment(params1)
        nb.addResult(rc1)

        with self.assertRaises(KeyError):
            rc2 = e.runExperiment(params1)
            nb.addResult(rc2)
