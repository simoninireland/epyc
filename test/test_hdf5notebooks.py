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

from os import sendfile
from epyc import *
import unittest
import tables
import os
from tempfile import NamedTemporaryFile


class SampleExperiment(Experiment):
    '''A very simple experiment that adds up its parameters.'''
    
    def do( self, param ):
        return dict(total=param['k'] + 10)

class SampleExperiment1(Experiment):
    '''An experiment that fails.'''
    
    def do( self, param ):
        raise Exception('A (deliberate) failure')

    
class HDF5LabNotebookTests(unittest.TestCase):

    def setUp( self ):
        '''Set up with a temporary file.'''
        #tf = NamedTemporaryFile()
        #tf.close()
        #self._fn = tf.name
        self._fn = 'test.h5'

    def tearDown( self ):
        '''Delete the temporary file.'''
        try:
            #os.remove(self._fn)
            pass
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

        # add the failed result
        rc[Experiment.METADATA][Experiment.STATUS] = False
        rc[Experiment.METADATA][Experiment.EXCEPTION] = 'An exception'
        rc[Experiment.METADATA][Experiment.TRACEBACK] = 'Called from somewhere'
        rc[Experiment.RESULTS] = dict()
        nb.addResult(rc)
        nb.commit()

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
       






if __name__ == '__main__':
    unittest.main()




