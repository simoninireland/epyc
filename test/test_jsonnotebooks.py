# Tests of JSON notebooks
#
# Copyright (C) 2016 Simon Dobson
# 
# Licensed under the GNU General Public Licence v.2.0
#

from epyc import *

import six
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

class SampleExperiment1(Experiment):
    '''An experiment that fails.'''
    
    def do( self, param ):
        raise Exception('A (deliberate) failure')

    
class JSONLabNotebookTests(unittest.TestCase):

    def setUp( self ):
        '''Set up with a temporary file.'''
        tf = NamedTemporaryFile()
        tf.close()
        self._fn = tf.name

    def tearDown( self ):
        '''Delete the temporary file.'''
        try:
            os.remove(self._fn)
        except OSError:
            pass
        
    def testCreate( self ):
        '''Test creation of empty notebook (which won't create file)'''
        js = JSONLabNotebook(self._fn)
        self.assertTrue(js.isPersistent())
        self.assertEqual(js.name(), self._fn)

    def testCreateAndSave( self ):
        '''Test creation and saving of notebook'''
        e = SampleExperiment()
        params1 = dict( a = 1, b = 2 )
        rc1 = e.set(params1).run()
        params2 = dict( a = 1, b = 3 )
        rc2 = e.set(params2).run()
        
        js = JSONLabNotebook(self._fn, description = "A test notebook")
        js.addResult(rc1)
        js.addPendingResult(params2, 2)
        js.commit()
        
        jsr = JSONLabNotebook(self._fn)
        self.assertEqual(jsr.description(), "A test notebook")
        six.assertCountEqual(self, map(int, jsr.pendingResults()), js.pendingResults())
        six.assertCountEqual(self, jsr.results(), js.results())
 
    def testCreateAndUpdate( self ):
        '''Test creation and updating of notebook'''
        e = SampleExperiment()
        params1 = dict( a = 1, b = 2 )
        rc1 = e.set(params1).run()
        params2 = dict( a = 1, b = 3 )
        rc2 = e.set(params2).run()
        
        js = JSONLabNotebook(self._fn, description = "A test notebook")
        js.addResult(rc1)
        js.addPendingResult(params2, 2)
        js.commit()
        
        js.addResult(rc2, 2)
        js.commit()
        
        jsr = JSONLabNotebook(self._fn)
        self.assertEqual(jsr.description(), "A test notebook")
        self.assertEqual(len(jsr.pendingResults()), 0)
        six.assertCountEqual(self, jsr.results(), js.results())
        
    def testCreateOverwrite( self ):
        '''Test the create flag'''
        e = SampleExperiment()
        params1 = dict( a = 1, b = 2 )
        rc1 = e.set(params1).run()
        
        js = JSONLabNotebook(self._fn, description = "A test notebook")
        js.addResult(rc1)
        js.commit()
        
        jsr = JSONLabNotebook(self._fn, create = True, description = "Nothing to see")
        self.assertEqual(jsr.description(), "Nothing to see")
        self.assertEqual(len(jsr.results()), 0)
        self.assertEqual(len(jsr.pendingResults()), 0)
        
    def testCreateNoOverwrite( self ):
        '''Test that the create flag being false doesn't overwrite'''
        e = SampleExperiment()
        params1 = dict( a = 1, b = 2 )
        rc1 = e.set(params1).run()
        
        js = JSONLabNotebook(self._fn, description = "A test notebook")
        js.addResult(rc1)
        js.commit()
        
        jsr = JSONLabNotebook(self._fn, description = "Nothing to see")
        self.assertEqual(jsr.description(), "A test notebook")
        six.assertCountEqual(self, jsr.results(), js.results())
        self.assertEqual(len(jsr.pendingResults()), 0)
        
    def testReadEmpty( self ):
        '''Test we can correctly load an empty file, resulting in an empty notebook''' 
        e = SampleExperiment()
        params1 = dict( a = 1, b = 2 )
        rc1 = e.set(params1).run()
        
        js = JSONLabNotebook(self._fn, description = "A test notebook")
        js.addResult(rc1)
        js.commit()
        
        js2 = JSONLabNotebook(self._fn, create = True,
                              description = "Another test notebook")
        
        jsr = JSONLabNotebook(self._fn)
        self.assertEqual(jsr.description(), None)
        self.assertEqual(len(jsr.results()), 0)
        self.assertEqual(len(jsr.pendingResults()), 0)
        
        js2.commit()
        jsr = JSONLabNotebook(self._fn)
        self.assertEqual(jsr.description(), "Another test notebook")
        self.assertEqual(len(jsr.results()), 0)
        self.assertEqual(len(jsr.pendingResults()), 0)            

    def testTimePatching( self ):
        '''Check that the timing metadata is persisted correctly.'''
        e = SampleExperiment()
        params1 = dict( a = 1, b = 2 )
        rc1 = e.set(params1).run()
        
        js = JSONLabNotebook(self._fn, description = "A test notebook")
        js.addResult(rc1)
        js.commit()
        
        js2 = JSONLabNotebook(self._fn)
        rc2 = js2.latestResultsFor(params1)
        self.assertEqual(rc1[Experiment.METADATA][Experiment.START_TIME],
                         rc2[Experiment.METADATA][Experiment.START_TIME])
        self.assertEqual(rc1[Experiment.METADATA][Experiment.END_TIME],
                         rc2[Experiment.METADATA][Experiment.END_TIME])
                

    def testPersistingException( self ):
        '''Test we persist exceptions as strings.'''
        e = SampleExperiment1()
        params1 = dict(a = 1)
        rc1 = e.set(params1).run()
        
        js = JSONLabNotebook(self._fn, description = "A test notebook")
        js.addResult(rc1)
        js.commit()
        
        js2 = JSONLabNotebook(self._fn)
        rc2 = js2.latestResultsFor(params1)
        self.assertFalse(rc2[Experiment.METADATA][Experiment.STATUS])
        self.assertTrue(isinstance(rc2[Experiment.METADATA][Experiment.EXCEPTION], six.string_types))
