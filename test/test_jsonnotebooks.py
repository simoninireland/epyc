# Tests of JSON notebooks
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
        #self._fn = 'test.json'

    def tearDown( self ):
        '''Delete the temporary file.'''
        try:
            os.remove(self._fn)
            #pass
        except OSError:
            pass
        
    def testCreate( self ):
        '''Test creation of empty notebook (which won't create file)'''
        js = JSONLabNotebook(self._fn, description="A test notebook", create=True)
        self.assertTrue(js.isPersistent())
        self.assertEqual(js.name(), self._fn)

    def testCreateAndSave( self ):
        '''Test creation and saving of notebook'''
        e = SampleExperiment()
        params1 = dict( a = 1, b = 2 )
        rc1 = e.set(params1).run()
        params2 = dict( a = 1, b = 3 )
        rc2 = e.set(params2).run()
        
        js = JSONLabNotebook(self._fn, description="A test notebook", create=True)
        js.addResult(rc1)
        js.addPendingResult(params2, '2')
        js.commit()
        
        jsr = JSONLabNotebook(self._fn)
        self.assertEqual(jsr.description(), "A test notebook")
        self.assertCountEqual(jsr.pendingResults(), js.pendingResults())
        self.assertCountEqual(jsr.results(), js.results())
 
    def testCreateAndUpdate( self ):
        '''Test creation and updating of notebook'''
        e = SampleExperiment()
        params1 = dict( a = 1, b = 2 )
        rc1 = e.set(params1).run()
        params2 = dict( a = 1, b = 3 )
        rc2 = e.set(params2).run()
        
        js = JSONLabNotebook(self._fn, description="A test notebook", create=True)
        js.addResult(rc1)
        js.addPendingResult(params2, '2')
        js.commit()
        
        js.resolvePendingResult(rc2, '2')
        js.commit()
        
        jsr = JSONLabNotebook(self._fn)
        self.assertEqual(jsr.description(), "A test notebook")
        self.assertEqual(len(jsr.pendingResults()), 0)
        self.assertCountEqual(jsr.results(), js.results())
        
    def testCreateOverwrite( self ):
        '''Test the create flag'''
        e = SampleExperiment()
        params1 = dict( a = 1, b = 2 )
        rc1 = e.set(params1).run()
        
        js = JSONLabNotebook(self._fn, description="A test notebook", create=True)
        js.addResult(rc1)
        js.commit()
        
        jsr = JSONLabNotebook(self._fn, description="A test notebook", create=True)
        self.assertEqual(jsr.description(), "A test notebook")
        self.assertEqual(len(jsr.results()), 0)
        self.assertEqual(len(jsr.pendingResults()), 0)
        
    def testCreateNoOverwrite( self ):
        '''Test that the create flag being false doesn't overwrite'''
        e = SampleExperiment()
        params1 = dict( a = 1, b = 2 )
        rc1 = e.set(params1).run()
        
        js = JSONLabNotebook(self._fn, description="A test notebook", create=True)
        js.addResult(rc1)
        js.commit()
        
        # check we keep the results but change the description
        jsr = JSONLabNotebook(self._fn, description = "Nothing to see")
        self.assertEqual(jsr.description(), "Nothing to see")
        self.assertCountEqual(jsr.results(), js.results())
        self.assertEqual(len(jsr.pendingResults()), 0)
        
    def testReadEmpty( self ):
        '''Test we can correctly load an empty file, resulting in an empty notebook''' 
        e = SampleExperiment()
        params1 = dict( a = 1, b = 2 )
        rc1 = e.set(params1).run()
        
        # notebook with a result
        js = JSONLabNotebook(self._fn, description="A test notebook", create=True)
        js.addResult(rc1)
        js.commit()
        
        # ...which we then wipe out by re-creating it
        js2 = JSONLabNotebook(self._fn, create=True,
                              description="Another test notebook")
        
        # ...and check we did
        jsr = JSONLabNotebook(self._fn)
        self.assertEqual(len(jsr.results()), 0)
        self.assertEqual(len(jsr.pendingResults()), 0)

        # ...and that it commits and reloads properly        
        js2.commit()
        jsr = JSONLabNotebook(self._fn)
        self.assertEqual(len(jsr.results()), 0)
        self.assertEqual(len(jsr.pendingResults()), 0)            

    def testTimePatching( self ):
        '''Check that the timing metadata is persisted correctly.'''
        e = SampleExperiment()
        params1 = dict( a = 1, b = 2 )
        rc1 = e.set(params1).run()
        
        js = JSONLabNotebook(self._fn, description="A test notebook", create=True)
        js.addResult(rc1)
        js.commit()
        
        js2 = JSONLabNotebook(self._fn)
        rc2 = (js2.results())[0]
        self.assertEqual(rc1[Experiment.METADATA][Experiment.START_TIME],
                         rc2[Experiment.METADATA][Experiment.START_TIME])
        self.assertEqual(rc1[Experiment.METADATA][Experiment.END_TIME],
                         rc2[Experiment.METADATA][Experiment.END_TIME])
                

    def testPersistingException( self ):
        '''Test we persist exceptions as strings.'''
        e = SampleExperiment1()
        params1 = dict(a = 1)
        rc1 = e.set(params1).run()
        
        js = JSONLabNotebook(self._fn, description="A test notebook", create=True)
        js.addResult(rc1)
        js.commit()
        
        js2 = JSONLabNotebook(self._fn)
        rc2 = (js2.results())[0]
        self.assertFalse(rc2[Experiment.METADATA][Experiment.STATUS])
        self.assertTrue(isinstance(rc2[Experiment.METADATA][Experiment.EXCEPTION], str))

    def testMultipleResultSets(self):
        '''Check we keep results sets separate.'''
        e = SampleExperiment()
        js = JSONLabNotebook(self._fn, create=True)

        # put some results into the default result set
        params1 = dict(a=10, b=20)
        rc1 = e.set(params1).run()
        js.addResult(rc1)
        params1['b'] = 40
        rc1 = e.set(params1).run()
        js.addResult(rc1)

        # put more results, with different type, into a different result set
        js.addResultSet('second')
        params2 = dict(c=10, d=20, e=90)
        rc2 = e.set(params2).run()
        js.addResult(rc2)
        params2['d'] = 40
        js.addPendingResult(params2, '123')
        js.commit()

        # check we've maintained the correct current result set
        js = JSONLabNotebook(self._fn)
        self.assertEqual(js.currentTag(), 'second')

        # check we've kept the results separate
        self.assertEqual(js.numberOfResults(), 1)
        self.assertEqual(js.numberOfPendingResults(), 1)
        self.assertEqual(len(js.resultsFor(dict(d=20))), 1)
        js.select(LabNotebook.DEFAULT_RESULTSET)
        self.assertEqual(js.numberOfResults(), 2)
        self.assertEqual(js.numberOfPendingResults(), 0)
        self.assertEqual(len(js.resultsFor(dict(a=10))), 2)
        self.assertEqual(len(js.resultsFor(dict(b=20))), 1)

    def testLocking(self):
        '''Test that a locked result set stays locked.'''
        e = SampleExperiment()
        js = JSONLabNotebook(self._fn, create=True)

        # put some results into the default result set
        params1 = dict(a=10, b=20)
        rc1 = e.set(params1).run()
        js.addResult(rc1)
        params1['b'] = 40
        rc1 = e.set(params1).run()
        js.addResult(rc1)
        js.commit()

        # put other results into another set and lock it
        js.addResultSet('second')
        params2 = dict(a=11, b=22)
        rc2 = e.set(params2).run()
        js.addResult(rc2)
        params3 = dict(a=11, b=24)
        js.addPendingResult(params3, '1234')
        js.current().finish()
        js.commit()

        # load the notebook and makle sure it's got the correct structure
        js1 = JSONLabNotebook(self._fn)
        self.assertEqual(js1.currentTag(), 'second')
        self.assertTrue(js1.current().isLocked())
        self.assertEqual(js1.current().numberOfResults(), 2)
        self.assertEqual(js1.current().numberOfPendingResults(), 0)
        js1.select(LabNotebook.DEFAULT_RESULTSET)
        self.assertFalse(js1.current().isLocked())

    def testLockingNotebook(self):
        '''Test notebook locking.'''
        e = SampleExperiment()
        nb = JSONLabNotebook(self._fn, create=True)

        rc1 = e.set(dict(k=10)).run()
        rc2 = e.set(dict(k=20)).run()
        rc3 = e.set(dict(k=30)).run()
        rc4 = e.set(dict(k=40)).run()

        # first result set
        nb.addResultSet('first')
        nb.addResult(rc1)
        nb.addResult(rc2)

        # second
        nb.addResultSet('second')
        nb.addResult(rc3)
        nb.addPendingResult(rc4[Experiment.PARAMETERS], '2345')

        # lock the notebook
        nb.finish()

        # check we can't add new result sets
        with self.assertRaises(LabNotebookLockedException):
            nb.addResultSet('third')

        # check the notebook in still  locked when reloaded
        nb.commit()
        with JSONLabNotebook(self._fn).open() as nb1:
            self.assertTrue(nb1.isLocked())
            with self.assertRaises(LabNotebookLockedException):
                nb.addResultSet('third')
            rs = nb1.select('first')
            self.assertTrue(rs.isLocked())
            self.assertEqual(rs.numberOfResults(), 2)
            rs = nb1.select('second')
            self.assertTrue(rs.isLocked())
            self.assertEqual(rs.numberOfPendingResults(), 0)
            self.assertEqual(rs.numberOfResults(), 2)
            rcs = nb1.resultsFor(rc4[Experiment.PARAMETERS])
            self.assertEqual(len(rcs), 1)

if __name__ == '__main__':
    unittest.main()
