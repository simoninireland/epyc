# Tests of HDF5 notebooks
#
# Copyright (C) 2020 Simon Dobson
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

# Remote HDF5 file for testiong URL behaviour
testFileURL = 'https://raw.githubusercontent.com/simoninireland/epyc/dev/test/test.h5'

class SampleExperiment(Experiment):
    '''A very simple experiment that adds up its parameters.'''
    
    def do( self, param ):
        return dict(total=param['k'] + 10)

class SampleExperiment1(Experiment):
    '''An experiment that fails.'''
    
    def do( self, param ):
        raise Exception('A (deliberate) failure')

class SampleExperiment2(Experiment):
    '''An experiment whose results contain a list.'''
    
    def do( self, param ):
        k = param['k']
        return dict(list=[k] * k)

  
class HDF5LabNotebookTests(unittest.TestCase):

    def setUp( self ):
        '''Set up with a temporary file.'''
        tf = NamedTemporaryFile()
        tf.close()
        self._fn = tf.name
        #self._fn = 'test.h5'

    def tearDown( self ):
        '''Delete the temporary file.'''
        try:
            os.remove(self._fn)
            #pass
        except OSError:
            pass
        
    def testCreate( self ):
        '''Test creation of empty notebook (which will create a backing file too)'''
        nb = HDF5LabNotebook(self._fn)
        self.assertTrue(nb.isPersistent())
        self.assertEqual(nb.name(), self._fn)
        self.assertTrue(os.path.isfile(self._fn))

    def testTypeDescription(self):
        '''Test we can extract the type description of an experiment.'''
        nb = HDF5LabNotebook(self._fn, create=True)
        params = dict()
        params['k'] = 3
        rc = SampleExperiment().set(params).run()
        nb.addResult(rc)

    def testReadWrite(self):
        '''Test we can read and write results.'''
        nb = HDF5LabNotebook(self._fn, create=True)
        params = dict()
        params['k'] = 3
        rc = SampleExperiment().set(params).run()
        nb.addResult(rc)
        nb.commit()

        # check we read back the same results
        nb = HDF5LabNotebook(self._fn)
        res = nb.dataframe().iloc[0]
        for d in [ Experiment.METADATA, Experiment.PARAMETERS, Experiment.RESULTS ]:
            for k in rc[d].keys():
                self.assertEqual(res[k], rc[d][k])

        # check we reconstruct the results dict form correctly too
        # (indirectly checks writing and reading dataset attributes)
        rc1 = nb.results()[0]
        for d in [ Experiment.METADATA, Experiment.PARAMETERS, Experiment.RESULTS ]:
            for k in rc1[d].keys():
                self.assertEqual(res[k], rc1[d][k])

    def testReadWritePending(self):
        '''Test we can read and write result sets with pending results.'''
        nb = HDF5LabNotebook(self._fn, create=True)
        params = dict()
        params['k'] = 3
        rc = SampleExperiment().set(params).run()
        nb.addResult(rc)
        params['k'] = 5
        nb.addPendingResult(params, '1234')
        nb.commit()

        nb = HDF5LabNotebook(self._fn)
        self.assertEqual(nb.numberOfPendingResults(), 1)
        self.assertCountEqual(nb.current().pendingResults(), [ '1234' ])

    def testReadWriteAllPending(self):
        '''Test reading and writing a result set with just pending results,'''
        nb = HDF5LabNotebook(self._fn, create=True)
        params = dict()
        params['k'] = 5
        nb.addPendingResult(params, '1234')
        params['k'] = 8
        nb.addPendingResult(params, '4567')
        nb.commit()

        nb = HDF5LabNotebook(self._fn)
        self.assertEqual(nb.numberOfPendingResults(), 2)
        self.assertCountEqual(nb.current().pendingResults(), [ '1234', '4567' ])
        self.assertEqual(nb.numberOfResults(), 0)

    def testResolveAcrossReadWrite(self):
        '''Test we can resolve a pending result across a read/write cycle.'''
        nb = HDF5LabNotebook(self._fn, create=True)

        # set up two pending results and save them
        params = dict()
        params['k'] = 5
        nb.addPendingResult(params, '1234')
        params['k'] = 8
        nb.addPendingResult(params, '4567')
        self.assertCountEqual(nb.current().pendingResults(), [ '1234', '4567' ])
        nb.commit()

        # re-load the notebook and resolve one of the results, saving again
        nb = HDF5LabNotebook(self._fn)
        params['k'] = 8
        rc1 = SampleExperiment().set(params).run()
        nb.resolvePendingResult(rc1, '4567')
        self.assertEqual(nb.numberOfPendingResults(), 1)
        self.assertCountEqual(nb.current().pendingResults(), [ '1234' ])
        self.assertEqual(nb.numberOfResults(), 1)
        rc1p = nb.results()[0]
        for d in [ Experiment.PARAMETERS, Experiment.RESULTS ]:
            for k in rc1p[d].keys():
                self.assertEqual(rc1p[d][k], rc1[d][k])
        nb.commit()

        # check the next save went OK
        nb = HDF5LabNotebook(self._fn)
        self.assertEqual(nb.numberOfPendingResults(), 1)
        self.assertEqual(nb.numberOfResults(), 1)
        rc1p = nb.results()[0]
        for d in [ Experiment.PARAMETERS, Experiment.RESULTS ]:
            for k in rc1p[d].keys():
                self.assertEqual(rc1p[d][k], rc1[d][k])

        # resolve the second result, check their integrity, and save again
        nb = HDF5LabNotebook(self._fn)
        params['k'] = 5
        rc2 = SampleExperiment().set(params).run()
        nb.resolvePendingResult(rc2, '1234')
        self.assertEqual(nb.numberOfPendingResults(), 0)
        self.assertEqual(nb.numberOfResults(), 2)
        res = nb.results()
        if res[0][Experiment.PARAMETERS]['k'] == 5:
            ts = [ (res[0], rc2), (res[1], rc1) ]
        else:
            ts = [ (res[0], rc1), (res[1], rc2) ]
        for (resp, rcp) in ts:
            for d in [ Experiment.PARAMETERS, Experiment.RESULTS ]:
                for k in rcp[d].keys():
                    self.assertEqual(rcp[d][k], resp[d][k])
        nb.commit()

        # final reload and sanity check
        nb = HDF5LabNotebook(self._fn)
        self.assertEqual(nb.numberOfPendingResults(), 0)
        self.assertEqual(nb.numberOfResults(), 2)

    def testReadWriteEmpty(self):
        '''Test an empty notebook is still empty after saving.'''
        nb = HDF5LabNotebook(self._fn, create=True)
        nb.commit()

        nb = HDF5LabNotebook(self._fn)
        self.assertEqual(nb.numberOfResultSets(), 1)
        self.assertEqual(nb.numberOfResults(), 0)
        self.assertEqual(nb.numberOfPendingResults(), 0)

    def testAddResultToEmpty(self):
        '''Test we can add to an empty notebook after saving.'''
        nb = HDF5LabNotebook(self._fn, create=True)
        nb.commit()

        nb = HDF5LabNotebook(self._fn)
        params = dict()
        params['k'] = 3
        rc = SampleExperiment().set(params).run()
        nb.addResult(rc)
        self.assertEqual(nb.numberOfResults(), 1)
        self.assertEqual(nb.numberOfPendingResults(), 0)

    def testAddPendingResultToEmpty(self):
        '''Test we can add a pending result to an empty notebook after saving.'''
        nb = HDF5LabNotebook(self._fn, create=True)
        nb.commit()

        nb = HDF5LabNotebook(self._fn)
        params = dict()
        params['k'] = 3
        nb.addPendingResult(params, '1234')
        self.assertEqual(nb.numberOfResults(), 0)
        self.assertEqual(nb.numberOfPendingResults(), 1)
        nb.commit()

        nb = HDF5LabNotebook(self._fn)
        self.assertEqual(nb.numberOfResults(), 0)
        self.assertEqual(nb.numberOfPendingResults(), 1)

    def testFailure(self):
        '''Test we can add successful and failed results.'''
        nb = HDF5LabNotebook(self._fn, create=True)

        # add the successful result
        params = dict()
        params['k'] = 3
        rc = SampleExperiment().set(params).run()
        nb.addResult(rc)
        nb.commit()
        t = rc[Experiment.RESULTS]['total']   # grab for later test

        # add the failed result
        rc[Experiment.METADATA][Experiment.STATUS] = False
        rc[Experiment.METADATA][Experiment.EXCEPTION] = 'An exception'
        rc[Experiment.METADATA][Experiment.TRACEBACK] = 'Called from somewhere'
        rc[Experiment.RESULTS] = dict()
        nb.addResult(rc)
        nb.commit()

        # check the results were stored correctly
        nb = HDF5LabNotebook(self._fn)
        for rc in nb.results():
            if rc[Experiment.METADATA][Experiment.STATUS]:
                # the successful result, check we have all result fields
                self.assertCountEqual(rc[Experiment.RESULTS].keys(), ['total'])
                self.assertEqual(rc[Experiment.RESULTS]['total'], t)

                # make sure the missing exception and traceback fields were properly zeroed
                self.assertEqual(rc[Experiment.METADATA][Experiment.EXCEPTION], '')
                self.assertEqual(rc[Experiment.METADATA][Experiment.TRACEBACK], '')
            else:
                # failed result, shouldn't be any result fields
                self.assertCountEqual(rc[Experiment.RESULTS].keys(), [])

    def testMaintainType(self):
        '''Test we can add several results without rebuilding the file unnecessarily.'''
        nb = HDF5LabNotebook(self._fn, create=True)

        # add two results, same type
        params = dict()
        params['k'] = 3
        rc = SampleExperiment().set(params).run()
        nb.addResult(rc)
        self.assertTrue(nb.current().isTypeChanged())
        params['k'] = 4
        rc = SampleExperiment().set(params).run()
        nb.addResult(rc)
        self.assertTrue(nb.current().isTypeChanged())

        # check commitment clears the flags
        nb.commit()
        self.assertFalse(nb.current().isTypeChanged())
        self.assertFalse(nb.current().isDirty())

        # add another value and check the type isn't changed
        params['k'] = 5
        rc = SampleExperiment().set(params).run()
        nb.addResult(rc)
        self.assertFalse(nb.current().isTypeChanged())

    def testExtraMetadata(self):
        '''Test we can add and save extra metadata fields.'''
        nb = HDF5LabNotebook(self._fn, create=True)

        # create a result and add some extra metadata
        params = dict()
        params['k'] = 3
        rc = SampleExperiment().set(params).run()
        rc[Experiment.METADATA]['extra'] = 'some more'
        nb.addResult(rc)
        nb.commit()

        # check the extra field comes back in
        nb = HDF5LabNotebook(self._fn)
        rc1 = nb.results()[0]
        self.assertEqual(rc1[Experiment.METADATA]['extra'], rc[Experiment.METADATA]['extra'])

    def testTwoResultSets(self):
        '''Test we can maintain two result sets without interference.'''
        nb = HDF5LabNotebook(self._fn, create=True)

        # create a couple of results and pending results in the first result set
        params = dict()
        params['k'] = 3
        rc = SampleExperiment().set(params).run()
        nb.addResult(rc)
        params['k'] = 4
        rc = SampleExperiment().set(params).run()
        nb.addResult(rc)
        params['k'] = 5
        nb.addPendingResult(params, '1234')
        nb.commit()

        # create more results with a different type in a new result set
        nb.addResultSet('second')
        params['k'] = 40
        params['s'] = 60
        rc = SampleExperiment().set(params).run()
        rc[Experiment.METADATA]['extra'] = 'some more'
        nb.addResult(rc)
        params['k'] = 50
        params['s'] = 70
        rc = SampleExperiment().set(params).run()
        rc[Experiment.METADATA]['extra'] = 'some more'
        nb.addResult(rc)
        nb.commit()

        # check the file has the same structure
        nb = HDF5LabNotebook(self._fn)
        self.assertCountEqual(nb.resultSets(), [ LabNotebook.DEFAULT_RESULTSET, 'second' ])
        self.assertEqual(nb.currentTag(), 'second')   # the current set when we committed
        nb.select(LabNotebook.DEFAULT_RESULTSET)
        self.assertEqual(nb.current().numberOfResults(), 2)
        self.assertEqual(nb.current().numberOfPendingResults(), 1)
        res = nb.results()[0]
        res = nb.results()[0]
        self.assertIn('k', res[Experiment.PARAMETERS])
        self.assertNotIn('s', res[Experiment.PARAMETERS])
        self.assertNotIn('extra', res[Experiment.METADATA])
        nb.select('second')
        self.assertEqual(nb.current().numberOfResults(), 2)
        self.assertEqual(nb.current().numberOfPendingResults(), 0)
        res = nb.results()[0]
        self.assertIn('k', res[Experiment.PARAMETERS])
        self.assertIn('s', res[Experiment.PARAMETERS])
        self.assertIn('extra', res[Experiment.METADATA])

    def testCurrentWithoutChange(self):
        '''Test we record a change of current result set with no other action.'''
        nb = HDF5LabNotebook(self._fn, create=True)

        # create a couple of results sets
        params = dict()
        params['k'] = 3
        rc = SampleExperiment().set(params).run()
        nb.addResult(rc)
        params['k'] = 4
        rc = SampleExperiment().set(params).run()
        nb.addResult(rc)
        nb.addResultSet('second')
        params['k'] = 40
        params['s'] = 60
        rc = SampleExperiment().set(params).run()
        nb.addResult(rc)
        params['k'] = 50
        params['s'] = 70
        rc = SampleExperiment().set(params).run()
        nb.addResult(rc)
        nb.commit()

        # check the current set
        nb = HDF5LabNotebook(self._fn)
        self.assertCountEqual(nb.resultSets(), [ LabNotebook.DEFAULT_RESULTSET, 'second' ])
        self.assertEqual(nb.currentTag(), 'second')

        # change the current set, save, re-load, and check
        nb.select(LabNotebook.DEFAULT_RESULTSET)
        nb.commit()
        nb = HDF5LabNotebook(self._fn)
        self.assertEqual(nb.currentTag(), LabNotebook.DEFAULT_RESULTSET)
       
    def testInferList(self):
        '''Test we can add results that contain lists.'''
        nb = HDF5LabNotebook(self._fn, create=True)

        # add a result with a list
        params = dict()
        params['k'] = 3
        rc = SampleExperiment2().set(params).run()
        nb.addResult(rc)
        
        # add another with the same shape1
        params['k'] = 3
        rc = SampleExperiment2().set(params).run()
        nb.addResult(rc)
        nb.commit()

        # check the values have the right shapes
        nb = HDF5LabNotebook(self._fn)
        params['k'] = 3
        rc = nb.resultsFor(params)[0]
        self.assertCountEqual(rc[Experiment.RESULTS]['list'], [ 3, 3, 3 ])

    def testContextManager(self):
        '''Test that the conext manager works as inteneded.'''
        nb = HDF5LabNotebook(self._fn, create=True) 
        with nb.open():
            # add two results, same type
            params = dict()
            params['k'] = 3
            rc = SampleExperiment().set(params).run()
            nb.addResult(rc)
            params['k'] = 4
            rc = SampleExperiment().set(params).run()
            nb.addResult(rc)

        # re-load and check we have the last result
        nb = HDF5LabNotebook(self._fn)
        self.assertEqual(nb.numberOfResults(), 2)
        self.assertEqual(len(nb.dataframeFor(params)), 1)

    def testContextManagerExceptions(self):
        '''Test that the context manager is robust to exceptions.'''
        nb = HDF5LabNotebook(self._fn, create=True)
        try:
            with nb.open():
                # add two results, same type -- but jump out before the second one gets added
                params = dict()
                params['k'] = 3
                rc = SampleExperiment().set(params).run()
                nb.addResult(rc)
                params['k'] = 4
                raise Exception('second one is skipped')

                # this is what we then shouldn't see, because of the exception
                rc = SampleExperiment().set(params).run()
                nb.addResult(rc)
        except:
            pass

        # re-load and check we have the first result (and not the second)
        nb = HDF5LabNotebook(self._fn)
        self.assertEqual(nb.numberOfResults(), 1)
        params = dict()
        params['k'] = 3
        self.assertEqual(len(nb.dataframeFor(params)), 1)
        params['k'] = 4
        self.assertEqual(len(nb.dataframeFor(params)), 0)

    def testAttributes(self):
        '''Test we can read and write attributes.'''
        nb = HDF5LabNotebook(self._fn, description='A test notebook', create=True)
        
        # attributes of a result set but no results dataset
        rs = nb.current()
        rs['number1'] = '1'
        rs['number2'] = 2
        nb.commit()
        nb = HDF5LabNotebook(self._fn)
        rs = nb.current()
        self.assertEqual(rs['number1'], '1')
        self.assertEqual(rs['number2'], '2')    # all attributes stored as strings at present

        # check we pulled the description as well
        self.assertEqual(nb.description(), 'A test notebook')

        # add a new result set and some results, check attributes
        nb.addResultSet('new', 'Another result set')
        rs = nb.current()
        rs['number1'] = '4'
        rs['number3'] = '3'
        params = dict()
        params['k'] = 3
        rc = SampleExperiment().set(params).run()
        nb.addResult(rc)
        nb.commit()
        nb = HDF5LabNotebook(self._fn)
        rs = nb.current()
        self.assertEqual(rs.description(), 'Another result set')
        self.assertEqual(len(rs), 1)
        self.assertEqual(rs['number3'], '3')
        self.assertEqual(rs['number1'], '4')
        rs = nb.select(LabNotebook.DEFAULT_RESULTSET)
        self.assertEqual(rs['number1'], '1')
        self.assertEqual(rs['number2'], '2')    # all attributes stored as strings at present

        # test that deleting attributes from the result set deletes them from the file
        del rs['number1']
        nb.commit()
        nb = HDF5LabNotebook(self._fn)
        rs = nb.current()
        self.assertCountEqual(rs.keys(), ['number2'])

    def testChangeAttributes(self):
        '''Test we can change attributes, descriptions, etc.'''
        with HDF5LabNotebook(self._fn, description='A test notebook', create=True).open() as nb:
            pass

        # check the description matches
        with HDF5LabNotebook(self._fn).open() as nb:
            self.assertEqual(nb.description(), 'A test notebook')

            # check we can change the description
            nb.setDescription('A new description')
        with HDF5LabNotebook(self._fn).open() as nb:
            self.assertEqual(nb.description(), 'A new description')

        # check we can set and change a result set description
        with HDF5LabNotebook(self._fn).open() as nb:
            nb.addResultSet('second', 'A result set')
        with HDF5LabNotebook(self._fn).open() as nb:
            rs = nb.current()
            self.assertEqual(rs.description(), 'A result set')
            rs.setDescription('Changed')
        with HDF5LabNotebook(self._fn).open() as nb:
            self.assertEqual(rs.description(), 'Changed')

        # check we can set, change, and delete result set attributes
        with HDF5LabNotebook(self._fn).open() as nb:
            rs = nb.current()
            rs['name'] = 'an attribute'
            rs['date'] = 'today'
        with HDF5LabNotebook(self._fn).open() as nb:
            rs = nb.current()
            self.assertEqual(rs['name'], 'an attribute')
            self.assertEqual(rs['date'], 'today')
            rs['date'] = 'tomorrow'
            del rs['name']
        with HDF5LabNotebook(self._fn).open() as nb:
            rs = nb.current()
            self.assertCountEqual(rs.keys(), [ 'date' ])
            self.assertEqual(rs['date'], 'tomorrow')

    def testNoDefault(self):
        '''Test things work when the default resultset is left empty.'''

        # get some results for later
        params = dict()
        params['k'] = 3
        rc = SampleExperiment().set(params).run()

        # put a pending result into a new dataset, then commit
        with HDF5LabNotebook(self._fn, create=True).open() as nb:
            nb.addResultSet('another')
            nb.addPendingResult(params, '1234')

        # resolve the result, then commit
        with HDF5LabNotebook(self._fn).open() as nb:
            nb.resolvePendingResult(rc, '1234')

        # check everything went to the right place
        with HDF5LabNotebook(self._fn).open() as nb:
            self.assertEqual(nb.currentTag(), 'another')
            self.assertEqual(nb.numberOfResults(), 1)
            self.assertEqual(nb.numberOfPendingResults(), 0)
            nb.select(nb.DEFAULT_RESULTSET)
            self.assertEqual(nb.numberOfResults(), 0)
            self.assertEqual(nb.numberOfPendingResults(), 0)

    def testLockingResultSets(self):
        '''Test that a locked result set stays locked.'''
        e = SampleExperiment()
        nb = HDF5LabNotebook(self._fn, create=True)

        # put some results into the default result set
        params1 = dict(k=10)
        rc1 = e.set(params1).run()
        nb.addResult(rc1)
        params1['k'] = 40
        rc1 = e.set(params1).run()
        nb.addResult(rc1)
        nb.commit()

        # put other results into another set and lock it
        nb.addResultSet('second')
        params2 = dict(k=11)
        rc2 = e.set(params2).run()
        nb.addResult(rc2)
        params3 = dict(k=16)
        nb.addPendingResult(params3, '1234')
        nb.current().finish()
        nb.commit()

        # load the notebook and make sure it's got the correct structure
        nb1 = HDF5LabNotebook(self._fn)
        self.assertEqual(nb1.currentTag(), 'second')
        self.assertTrue(nb1.current().isLocked())
        self.assertEqual(nb1.current().numberOfResults(), 2)
        self.assertEqual(nb1.current().numberOfPendingResults(), 0)
        nb1.select(LabNotebook.DEFAULT_RESULTSET)
        self.assertFalse(nb1.current().isLocked())

    def testLockingNotebook(self):
        '''Test notebook locking.'''
        e = SampleExperiment()
        nb = HDF5LabNotebook(self._fn, create=True)

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
        with HDF5LabNotebook(self._fn).open() as nb1:
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
        
    @unittest.skip('Seems to depend on exact config of the underlying filesystem')
    def testNoWriteWhenLocked(self):
        '''Test that no writing happens after a notebook is locked.'''
        nb = HDF5LabNotebook(self._fn, create=True)

        # commit the finished notebook
        nb.addResultSet('first')
        nb.finish()
        t1 = os.path.getmtime(self._fn)

        # reload and commit again, which shouldn't write anything
        with HDF5LabNotebook(self._fn).open() as nb1:
            nb1.commit()
        t2 = os.path.getmtime(self._fn)

        self.assertEqual(t1, t2)

    def testLoadingFromURL(self):
        '''Test we can load a read-only notebook from a URL.'''
        with HDF5LabNotebook(testFileURL).open() as nb1:
            self.assertIn('first', nb1.resultSets())
            self.assertTrue(nb1.isLocked())

    def testRagged(self):
        '''Test we can create ragged axes (i.e., variable length array results).'''
        nb = HDF5LabNotebook(self._fn, create=True)

        params = dict()
        params['k'] =  1
        e = SampleExperiment2()
        rc = e.set(params).run()
        nb.addResult(rc)

        params['k'] =  10
        rc = e.set(params).run()
        nb.addResult(rc)

        self.assertEqual(len(nb.dataframe()), 2)
        nb.commit()

        nb1 = HDF5LabNotebook(self._fn)
        self.assertEqual(len(nb1.dataframe()), 2)
        rcs = nb.resultsFor(dict(k=1))
        self.assertEqual(len(rcs), 1)
        rcs1 = nb1.resultsFor(dict(k=1))
        self.assertEqual(len(rcs1), 1)
        self.assertCountEqual(rcs[0][Experiment.RESULTS]['list'], rcs1[0][Experiment.RESULTS]['list'])
        rcs = nb.resultsFor(dict(k=10))
        self.assertEqual(len(rcs), 1)
        rcs1 = nb1.resultsFor(dict(k=10))
        self.assertEqual(len(rcs1), 1)
        self.assertCountEqual(rcs[0][Experiment.RESULTS]['list'], rcs1[0][Experiment.RESULTS]['list'])

if __name__ == '__main__':
    unittest.main()




