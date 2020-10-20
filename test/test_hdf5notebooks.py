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
            self.assertCountEqual(rc1[d], rc[d])

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
        params = dict()
        params['k'] = 5
        nb.addPendingResult(params, '1234')
        params['k'] = 8
        nb.addPendingResult(params, '4567')
        self.assertCountEqual(nb.current().pendingResults(), [ '1234', '4567' ])
        nb.commit()

        nb = HDF5LabNotebook(self._fn)
        rc1 = SampleExperiment().set(params).run()
        nb.resolvePendingResult(rc1, '4567')
        self.assertEqual(nb.numberOfPendingResults(), 1)
        self.assertCountEqual(nb.current().pendingResults(), [ '1234' ])
        self.assertEqual(nb.numberOfResults(), 1)
        self.assertDictEqual(nb.results()[0], rc1)
        nb.commit()

        nb = HDF5LabNotebook(self._fn)
        self.assertEqual(nb.numberOfPendingResults(), 1)
        self.assertEqual(nb.numberOfResults(), 1)
        self.assertDictEqual(nb.results()[0], rc1)

        nb = HDF5LabNotebook(self._fn)
        params['k'] = 5
        rc2 = SampleExperiment().set(params).run()
        nb.resolvePendingResult(rc2, '1234')
        self.assertEqual(nb.numberOfPendingResults(), 0)
        self.assertEqual(nb.numberOfResults(), 2)
        res = nb.results()
        try:
            self.assertDictEqual(res[0], rc1)
            self.assertDictEqual(res[1], rc2)
        except Exception:
            self.assertDictEqual(res[0], rc2)
            self.assertDictEqual(res[1], rc1)
        nb.commit()

        nb = HDF5LabNotebook(self._fn)
        self.assertEqual(nb.numberOfPendingResults(), 0)
        self.assertEqual(nb.numberOfResults(), 2)

    def testReadWriteEmpty(self):
        '''Test an empty notebook is still empty after saving.'''
        nb = HDF5LabNotebook(self._fn)
        nb.commit()

        nb = HDF5LabNotebook(self._fn)
        self.assertEqual(nb.numberOfResultSets(), 1)
        self.assertEqual(nb.numberOfResults(), 0)
        self.assertEqual(nb.numberOfPendingResults(), 0)

    def testAddResultToEmpty(self):
        '''Test we can add to an empty notebook after saving.'''
        nb = HDF5LabNotebook(self._fn)
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
        nb = HDF5LabNotebook(self._fn)
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


if __name__ == '__main__':
    unittest.main()




