# Tests of result sets
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
import numpy
import pandas


class SampleExperiment(Experiment):
    '''A very simple experiment that adds up its parameters.'''

    def do( self, param ):
        total = 0
        for k in param:
            total = total + param[k]
        return dict(total = total)


class ResultSetTests(unittest.TestCase):

    def setUp(self):
        '''Populate a results dict for testing with.'''
        self._rs = ResultSet()

        # populate metadata of otherwise empty results dict
        self._rc = Experiment.resultsdict()
        self._rc[Experiment.METADATA][Experiment.EXPERIMENT] = str(self.__class__)
        self._rc[Experiment.METADATA][Experiment.START_TIME] = datetime.now()
        self._rc[Experiment.METADATA][Experiment.END_TIME] = datetime.now()
        self._rc[Experiment.METADATA][Experiment.SETUP_TIME] = 10
        self._rc[Experiment.METADATA][Experiment.EXPERIMENT_TIME] = 20
        self._rc[Experiment.METADATA][Experiment.TEARDOWN_TIME] = 10
        self._rc[Experiment.METADATA][Experiment.ELAPSED_TIME] = 40
        self._rc[Experiment.METADATA][Experiment.STATUS] = True
        self._rc[Experiment.METADATA][Experiment.STATUS] = True
        self._rc[Experiment.PARAMETERS]['singleton'] = 1
        self._rc[Experiment.RESULTS]['first'] = 1

    def testTitle(self):
        '''Test we can set descriptions, and get default ones.'''
        rs1 = ResultSet('My results')
        self.assertEqual(rs1.description(), 'My results')
        rs2 = ResultSet()
        self.assertIsNotNone(rs2.description())


    # ---------- Type inference ----------

    def testNoDtype(self):
        '''Test we initially have no dtype set.'''''
        with self.assertRaises(Exception):
            self._rs.dtype()

    def testInitialInferSuccess(self):
        '''Test we can infer the initial dtype for a successful results dict.'''
        self._rc[Experiment.METADATA][Experiment.STATUS] = True
        self._rc[Experiment.PARAMETERS]['k'] = 1
        self._rc[Experiment.RESULTS]['total'] = 2.0
        self._rc[Experiment.RESULTS]['flag'] = False
        dtype = self._rs.inferDtype(self._rc)
        self.assertCountEqual(self._rs.metadataNames(), Experiment.StandardMetadata)
        self.assertCountEqual(self._rs.parameterNames(), ['k', 'singleton'])
        self.assertCountEqual(self._rs.resultNames(), ['total', 'first', 'flag'])
        self.assertEqual(dtype.fields['k'][0], numpy.dtype(ResultSet.TypeMapping[int]))
        self.assertEqual(dtype.fields['total'][0], numpy.dtype(ResultSet.TypeMapping[float]))
        self.assertEqual(dtype.fields['singleton'][0], numpy.dtype(ResultSet.TypeMapping[int]))
        self.assertEqual(dtype.fields['first'][0], numpy.dtype(ResultSet.TypeMapping[int]))
        self.assertEqual(dtype.fields['flag'][0], numpy.dtype(ResultSet.TypeMapping[bool]))
        self.assertEqual(dtype.fields[Experiment.START_TIME][0], numpy.dtype(ResultSet.TypeMapping[datetime]))
        self.assertEqual(dtype.fields[Experiment.EXCEPTION][0], numpy.dtype(ResultSet.TypeMapping[str]))

    def testInitialInferFailure(self):
        '''Test we can infer the initial dtype for an unsuccessful results dict.'''
        self._rc[Experiment.METADATA][Experiment.STATUS] = False
        self._rc[Experiment.METADATA][Experiment.EXCEPTION] = str(Exception('wrong'))
        self._rc[Experiment.METADATA][Experiment.TRACEBACK] = '<backtrace>'
        self._rc[Experiment.PARAMETERS]['k'] = 1
        dtype = self._rs.inferDtype(self._rc)
        self.assertCountEqual(self._rs.metadataNames(), Experiment.StandardMetadata)
        self.assertCountEqual(self._rs.parameterNames(), ['k', 'singleton'])
        self.assertCountEqual(self._rs.resultNames(), [])
        self.assertEqual(dtype.fields['k'][0], numpy.dtype(ResultSet.TypeMapping[int]))
        self.assertEqual(dtype.fields[Experiment.START_TIME][0], numpy.dtype(ResultSet.TypeMapping[datetime]))
        self.assertEqual(dtype.fields[Experiment.EXCEPTION][0], numpy.dtype(ResultSet.TypeMapping[str]))
        self.assertEqual(dtype.fields[Experiment.TRACEBACK][0], numpy.dtype(ResultSet.TypeMapping[str]))

    def testAddMetadata(self):
        '''Test we can add metadata elements beyond the standard set.'''
        self._rc[Experiment.METADATA]['additional'] = True
        self._rc[Experiment.PARAMETERS]['k'] = 1
        dtype = self._rs.inferDtype(self._rc)
        self.assertCountEqual(self._rs.metadataNames(), Experiment.StandardMetadata.union(set(['additional'])))
        self.assertEqual(dtype.fields['additional'][0], numpy.dtype(ResultSet.TypeMapping[bool]))

        # check we can now extend the
        #  metadata
        self._rc[Experiment.METADATA]['andagain'] = 'here we go'
        dtype = self._rs.inferDtype(self._rc)
        self.assertCountEqual(self._rs.metadataNames(), Experiment.StandardMetadata.union(set(['additional', 'andagain'])))
        self.assertEqual(dtype.fields['andagain'][0], numpy.dtype(ResultSet.TypeMapping[str]))

    def testAddResults(self):
        '''Test we can add more results.'''

        # initial set of paramneters and results
        self._rc[Experiment.METADATA][Experiment.STATUS] = True
        self._rc[Experiment.PARAMETERS]['k'] = 1
        self._rc[Experiment.RESULTS]['total'] = 2.0
        self._rc[Experiment.RESULTS]['flag'] = False
        self._rs.inferDtype(self._rc)
        self.assertCountEqual(self._rs.resultNames(), ['total', 'first', 'flag'])

        # add a result with an extra field and no flag, dtype should be extended
        self._rc[Experiment.PARAMETERS]['k'] = 2
        self._rc[Experiment.RESULTS]['total'] = 3.0
        del self._rc[Experiment.RESULTS]['flag']
        self._rc[Experiment.RESULTS]['extra'] = 'hello'
        dtype = self._rs.inferDtype(self._rc)
        self.assertCountEqual(self._rs.metadataNames(), Experiment.StandardMetadata)
        self.assertCountEqual(self._rs.parameterNames(), ['k', 'singleton'])
        self.assertCountEqual(self._rs.resultNames(), ['total', 'first', 'flag', 'extra'])
        self.assertEqual(dtype.fields['flag'][0], numpy.dtype(ResultSet.TypeMapping[bool]))
        self.assertEqual(dtype.fields['extra'][0], numpy.dtype(ResultSet.TypeMapping[str]))

    def testAddParametersAndResults(self):
        '''Test we can add more parameters and more results.'''

        # initial set of parameters and results
        self._rc[Experiment.METADATA][Experiment.STATUS] = True
        self._rc[Experiment.PARAMETERS]['k'] = 1
        self._rc[Experiment.RESULTS]['total'] = 2.0
        self._rc[Experiment.RESULTS]['flag'] = False
        self._rs.inferDtype(self._rc)
        self.assertCountEqual(self._rs.parameterNames(), ['k', 'singleton'])
        self.assertCountEqual(self._rs.resultNames(), ['total', 'first', 'flag'])
        self.assertFalse(self._rs.isDirty())
        self.assertTrue(self._rs.isTypeChanged())

        # add a result with extra parameters and results
        self._rs.typechanged(False)
        self._rc[Experiment.PARAMETERS]['k'] = 2
        self._rc[Experiment.PARAMETERS]['j'] = 9
        self._rc[Experiment.RESULTS]['total'] = 3.0
        self._rc[Experiment.RESULTS]['flag'] = False
        self._rc[Experiment.RESULTS]['extra'] = 'hello'
        dtype = self._rs.inferDtype(self._rc)
        self.assertCountEqual(self._rs.metadataNames(), Experiment.StandardMetadata)
        self.assertCountEqual(self._rs.parameterNames(), ['k', 'j', 'singleton'])
        self.assertCountEqual(self._rs.resultNames(), ['total', 'first', 'flag', 'extra'])
        self.assertEqual(dtype.fields['extra'][0], numpy.dtype(ResultSet.TypeMapping[str]))
        self.assertTrue(self._rs.isTypeChanged())

    def testAddInfer(self):
        '''Test that adding a result does the inference operation.'''
        self._rc[Experiment.METADATA][Experiment.STATUS] = True
        self._rc[Experiment.PARAMETERS]['k'] = 1
        self._rc[Experiment.RESULTS]['total'] = 2.0
        self._rc[Experiment.RESULTS]['flag'] = False
        self._rs.addSingleResult(self._rc)
        dtype = self._rs.dtype()
        self.assertCountEqual(self._rs.parameterNames(), ['k', 'singleton'])
        self.assertCountEqual(self._rs.resultNames(), ['total', 'first', 'flag'])
        self.assertEqual(dtype.fields['k'][0], numpy.dtype(ResultSet.TypeMapping[int]))
        self.assertEqual(dtype.fields['total'][0], numpy.dtype(ResultSet.TypeMapping[float]))
        self.assertEqual(dtype.fields['flag'][0], numpy.dtype(ResultSet.TypeMapping[bool]))
        self.assertTrue(self._rs.isDirty())

    def testExtendDataframe(self):
        '''Test that extending the dtype extends the dataframe properly.'''

        # add first result
        self._rc[Experiment.METADATA][Experiment.STATUS] = True
        self._rc[Experiment.PARAMETERS]['k'] = 1
        self._rc[Experiment.RESULTS]['total'] = 2.0
        self._rc[Experiment.RESULTS]['flag'] = False
        self._rs.addSingleResult(self._rc)

        # add result with extra result elements, dataframe should gain columns
        # with default values in the existing rows
        self._rc[Experiment.PARAMETERS]['k'] = 2
        self._rc[Experiment.PARAMETERS]['j'] = 9
        self._rc[Experiment.RESULTS]['total'] = 3.0
        self._rc[Experiment.RESULTS]['flag'] = False
        self._rc[Experiment.RESULTS]['extra'] = 'hello'
        self._rs.addSingleResult(self._rc)
        df = self._rs.dataframe()
        self.assertTrue((df[df['k'] == 1]['extra'] == '').all())
        self.assertTrue((df[df['k'] == 2]['extra'] == 'hello').all())
        self.assertTrue(self._rs.isDirty())

    def testInferPending(self):
        '''Test we infer the dtype correct for pending results.'''
        self._rc[Experiment.PARAMETERS]['k'] = 1
        dtype = self._rs.inferPendingResultDtype(self._rc[Experiment.PARAMETERS])
        self.assertCountEqual(self._rs.metadataNames(), [])
        self.assertCountEqual(self._rs.parameterNames(), ['k', 'singleton'])
        self.assertCountEqual(self._rs.resultNames(), [])
        self.assertEqual(dtype.fields['k'][0], numpy.dtype(ResultSet.TypeMapping[int]))
        self.assertEqual(dtype.fields['singleton'][0], numpy.dtype(ResultSet.TypeMapping[int]))

    def testAddPendingParameters(self):
        '''Test we can add parameters to pending results.'''

        # add initial pending result
        self._rc[Experiment.PARAMETERS]['k'] = 1
        dtype = self._rs.inferPendingResultDtype(self._rc[Experiment.PARAMETERS])
        self.assertCountEqual(self._rs.metadataNames(), [])
        self.assertCountEqual(self._rs.parameterNames(), ['k', 'singleton'])
        self.assertCountEqual(self._rs.resultNames(), [])
        self.assertEqual(dtype.fields['k'][0], numpy.dtype(ResultSet.TypeMapping[int]))

        # add another pending result with extended parameters, dtype should be extended
        self._rc[Experiment.PARAMETERS]['k'] = 2
        self._rc[Experiment.PARAMETERS]['j'] = 34.56
        dtype = self._rs.inferPendingResultDtype(self._rc[Experiment.PARAMETERS])
        self.assertCountEqual(self._rs.metadataNames(), [])
        self.assertCountEqual(self._rs.parameterNames(), ['k', 'j', 'singleton'])
        self.assertCountEqual(self._rs.resultNames(), [])
        self.assertEqual(dtype.fields['k'][0], numpy.dtype(ResultSet.TypeMapping[int]))
        self.assertEqual(dtype.fields['j'][0], numpy.dtype(ResultSet.TypeMapping[float]))
        self.assertEqual(dtype.fields['singleton'][0], numpy.dtype(ResultSet.TypeMapping[int]))

    def testInferResolve(self):
        '''Test the interaction between pending and real results when inferring type.'''

        # set initial pending dtype from parameters
        self._rc[Experiment.PARAMETERS]['k'] = 1
        self._rs.inferPendingResultDtype(self._rc[Experiment.PARAMETERS])

        # results, same parameters
        self._rc[Experiment.RESULTS]['total'] = 2.0
        dtype = self._rs.inferDtype(self._rc)
        self.assertCountEqual(self._rs.metadataNames(), Experiment.StandardMetadata)
        self.assertCountEqual(self._rs.parameterNames(), ['k', 'singleton'])
        self.assertCountEqual(self._rs.resultNames(), ['total', 'first'])
        self.assertEqual(dtype.fields['k'][0], numpy.dtype(ResultSet.TypeMapping[int]))
        self.assertEqual(dtype.fields['total'][0], numpy.dtype(ResultSet.TypeMapping[float]))

        # more results, same types, shouldn't change the dtype
        self._rs.dirty(False)
        self._rc[Experiment.PARAMETERS]['k'] = 2
        self._rc[Experiment.RESULTS]['total'] = 3.0
        dtype2 = self._rs.inferDtype(self._rc)
        self.assertEqual(dtype, dtype2)
        self.assertFalse(self._rs.isDirty())

    def testInferResolveExtend(self):
        '''Test we can extend parameters in a real (resolving) result.'''

        # set initial pending dtype
        self._rc[Experiment.PARAMETERS]['k'] = 1
        dtype = self._rs.inferPendingResultDtype(self._rc[Experiment.PARAMETERS])

        # results, same types, extra parameters
        self._rc[Experiment.PARAMETERS]['j'] = 34.56
        self._rc[Experiment.RESULTS]['total'] = 2.0
        dtype = self._rs.inferDtype(self._rc)
        self.assertCountEqual(self._rs.metadataNames(), Experiment.StandardMetadata)
        self.assertCountEqual(self._rs.parameterNames(), ['k', 'j', 'singleton'])
        self.assertCountEqual(self._rs.resultNames(), ['total', 'first'])
        self.assertEqual(dtype.fields['k'][0], numpy.dtype(ResultSet.TypeMapping[int]))
        self.assertEqual(dtype.fields['j'][0], numpy.dtype(ResultSet.TypeMapping[float]))
        self.assertEqual(dtype.fields['total'][0], numpy.dtype(ResultSet.TypeMapping[float]))


    # ---------- Attributes ----------

    def testAttributes(self):
        '''Test all the attribute operators.'''''
        
        # set and get
        self._rs['number1'] = '1'
        self.assertEqual(self._rs['number1'], '1')
        self.assertEqual(len(self._rs.keys()), 1)
        self.assertEqual(len(self._rs), 0)              # len() refers to results

        # check contains
        self.assertIn('number1', self._rs)
        self.assertNotIn('number2', self._rs)

        # exceptions for undefined attributes
        with self.assertRaises(Exception):
            self._rs['result2']
 
         # check we can delete attributes
        del self._rs['number1']
        with self.assertRaises(Exception):
            self._rs['result1']
        self.assertEqual(len(self._rs.keys()), 0)
        self.assertNotIn('number1', self._rs)


    # ---------- Adding results ----------

    def testaddSingleResult(self):
        '''Test we can add results to the set.'''
        self.assertCountEqual(self._rs.parameterNames(), [])

        # test initial result sets parameter names
        self._rs.addSingleResult(self._rc)
        self.assertCountEqual(self._rc[Experiment.PARAMETERS].keys(), self._rs.parameterNames())

        # add another result with different values
        self._rc[Experiment.PARAMETERS]['singleton'] = 2
        self._rs.addSingleResult(self._rc)

        # add a result with an extra parameter, should extend the dataframe
        self._rc[Experiment.PARAMETERS]['singleton'] = 3
        self._rc[Experiment.PARAMETERS]['radically'] = 'wrong'
        self._rs.addSingleResult(self._rc)
        df = self._rs.dataframe()
        self.assertTrue((df[df['singleton'] == 3]['radically'] == 'wrong').all())
        self.assertTrue((df[df['singleton'] != 3]['radically'] == '').all())
 
    def testSingleResult(self):
        '''Test retrieval of a single result.'''
        self._rs.addSingleResult(self._rc)
        df = self._rs.dataframeFor(self._rc[Experiment.PARAMETERS])
        self.assertEqual(len(df.index), 1)

        # add another result with same parameters, check we get them both
        self._rc[Experiment.RESULTS]['first'] = 2
        self._rs.addSingleResult(self._rc)
        df = self._rs.dataframeFor(self._rc[Experiment.PARAMETERS])
        self.assertEqual(len(df.index), 2)

        # check we don't get results when there are none
        self._rc[Experiment.PARAMETERS]['singleton'] = 5
        df = self._rs.dataframeFor(self._rc[Experiment.PARAMETERS])
        self.assertEqual(len(df.index), 0)

    def testSingleResultExtended(self):
        '''Test we can retrieve a result when the dataframe was extended with another.'''
        # add initial result
        self._rs.addSingleResult(self._rc)
        params1 = self._rc[Experiment.PARAMETERS].copy()

        # add a result with an extra parameter
        self._rc[Experiment.PARAMETERS]['singleton'] = 3
        self._rc[Experiment.PARAMETERS]['radically'] = 'wrong'
        self._rs.addSingleResult(self._rc)

        # retrieve the first result without knowing about the extended parameters
        df = self._rs.dataframeFor(params1)
        self.assertEqual(len(df.index), 1)
        self.assertTrue((df[df['singleton'] == params1['singleton']]['first'] == 1).all())
        self.assertTrue((df[df['singleton'] == params1['singleton']]['radically'] == '').all())
        self.assertTrue((df[df['singleton'] == 3]['first'] == 1).all())
        self.assertTrue((df[df['singleton'] == 3]['radically'] == 'wrong').all())

    def testSmallerParameters(self):
        '''Test we can project out values properly with fewer parameters provided.'''

        # add some results
        self._rc[Experiment.PARAMETERS]['singleton'] = 1
        self._rc[Experiment.PARAMETERS]['additional'] = 0
        self._rs.addSingleResult(self._rc)
        self._rc[Experiment.PARAMETERS]['singleton'] = 5
        self._rc[Experiment.RESULTS]['first'] = 2
        self._rs.addSingleResult(self._rc)
        self._rc[Experiment.PARAMETERS]['additional'] = 1
        self._rc[Experiment.RESULTS]['first'] = 2
        self._rs.addSingleResult(self._rc)

        # first sub-set, extracts several results
        ps = dict()
        ps['additional'] = 0
        df = self._rs.dataframeFor(ps)
        self.assertEqual(len(df.index), 2)

        # second sub-set, extracts one result
        ps['additional'] = 1
        df = self._rs.dataframeFor(ps)
        self.assertEqual(len(df.index), 1)

    def testConjunction(self):
        '''Test we can project-out results.'''

        # add some results
        self._rc[Experiment.PARAMETERS]['singleton'] = 1
        self._rc[Experiment.PARAMETERS]['additional'] = 0
        self._rs.addSingleResult(self._rc)
        self._rc[Experiment.PARAMETERS]['singleton'] = 5
        self._rc[Experiment.RESULTS]['first'] = 2
        self._rs.addSingleResult(self._rc)
        self._rc[Experiment.PARAMETERS]['additional'] = 1
        self._rc[Experiment.RESULTS]['first'] = 2
        self._rs.addSingleResult(self._rc)

        # progressively refine query
        ps = dict()
        ps['additional'] = 0
        df = self._rs.dataframeFor(ps)
        self.assertEqual(len(df.index), 2)
        ps['singleton'] = 5
        df = self._rs.dataframeFor(ps)
        self.assertEqual(len(df.index), 1)
        ps['singleton'] = 0
        df = self._rs.dataframeFor(ps)
        self.assertEqual(len(df.index), 0)

    def testMultiple(self):
        '''Test we can project out multiple values of the same parameter.'''
        self._rc[Experiment.PARAMETERS]['singleton'] = 1
        self._rc[Experiment.PARAMETERS]['additional'] = 0
        self._rs.addSingleResult(self._rc)
        self._rc[Experiment.PARAMETERS]['singleton'] = 5
        self._rc[Experiment.RESULTS]['first'] = 2
        self._rs.addSingleResult(self._rc)
        self._rc[Experiment.PARAMETERS]['additional'] = 1
        self._rc[Experiment.RESULTS]['first'] = 2
        self._rs.addSingleResult(self._rc)

        # extract all results with parameter in range
        ps = dict()
        ps['additional'] = [0, 1]
        df = self._rs.dataframeFor(ps)
        self.assertEqual(len(df.index), 3)

        # refine query to exclude some other results
        ps['singleton'] = 5
        df = self._rs.dataframeFor(ps)
        self.assertEqual(len(df.index), 2)

    def testImmutable(self):
        '''Test we can't update the results we get back.'''
        self._rs.addSingleResult(self._rc)
        df = self._rs.dataframeFor(self._rc[Experiment.PARAMETERS])

        # update-in-place on the dataframe we were passed
        v = self._rc[Experiment.RESULTS]['first']
        nv = v + 5
        df.loc[0, 'first'] = nv
        self.assertTrue((df['first'] == nv).all())

        # make sure we didn't affect the result set
        df = self._rs.dataframeFor(self._rc[Experiment.PARAMETERS])
        self.assertTrue((df['first'] == v).all())

    def testEmptyParameters(self):
        '''Test we get all results if we don't do any projection.'''
        self._rs.addSingleResult(self._rc)
        df = self._rs.dataframeFor(dict())
        self.assertEqual(len(df.index), 1)

    def testNumberOfResultsZero(self):
        '''Test we can handle zero results.'''
        self.assertEqual(self._rs.numberOfResults(), 0)        

    def testNumberOfResultsOne(self):
        '''Test we can count results.'''
        self._rs.addSingleResult(self._rc)
        self.assertEqual(self._rs.numberOfResults(), 1)        

    def testAddNoResults(self):
        '''Test we can correctly add the results of an experiment that doesn't have any actual results.'''
        self._rc[Experiment.RESULTS] = dict()
        self._rs.addSingleResult(self._rc)
        self.assertEqual(self._rs.numberOfResults(), 1)        
        self.assertCountEqual(self._rs.resultNames(), [])
        ress = self._rs.resultsFor(self._rc[Experiment.PARAMETERS])
        self.assertEqual(len(ress), 1)
        res = ress[0]
        self.assertIn(Experiment.RESULTS, res)
        self.assertDictEqual(res[Experiment.RESULTS], dict())        

    def testInferList(self):
        '''Test we can infer a list type for a result.'''

        # add a result with a list
        self._rc[Experiment.PARAMETERS]['singleton'] = 1
        self._rc[Experiment.RESULTS]['list'] = [ 1, 2, 3 ]
        self._rs.addSingleResult(self._rc)
        
        # add another with the same shape1
        self._rc[Experiment.PARAMETERS]['singleton'] = 2
        self._rc[Experiment.RESULTS]['list'] = [ 4, 5, 6 ]
        self._rs.addSingleResult(self._rc)

        # add another with a different shape
        self._rc[Experiment.PARAMETERS]['singleton'] = 3
        self._rc[Experiment.RESULTS]['list'] = [ 14, 15, 16, 17, 18 ]
        self._rs.addSingleResult(self._rc)

        # check the values have the right shapes
        params = dict()
        params['singleton'] = 1
        rc = self._rs.resultsFor(params)[0]
        self.assertCountEqual(rc[Experiment.RESULTS]['list'], [ 1, 2, 3 ])


    # ---------- Pending results ----------

    def testPendingResults(self):
        '''Test we can add and resolve pending results.'''
        self._rs.addSinglePendingResult(self._rc[Experiment.PARAMETERS], '1234')
        self.assertCountEqual(self._rs.pendingResults(), [ '1234' ])

        self._rs.addSingleResult(self._rc)
        self._rs.cancelSinglePendingResult('1234')
        self.assertCountEqual(self._rs.pendingResults(), [])

        # check we have the cancelled result still
        rss = self._rs.dataframeFor(self._rc[Experiment.PARAMETERS])
        self.assertEqual(len(rss), 2)

        # check there's only one successful result
        rss = self._rs.dataframeFor(self._rc[Experiment.PARAMETERS], only_successful=True)
        self.assertEqual(len(rss), 1)
        self.assertEqual(rss['first'][0], 1)

    def testPendingResultsFor(self):
        '''Test we can retrieve pending results for a sub-set of parameters.'''
        params = dict()
        params['a'] = 10
        params['b'] = 50
        params['c'] = 'fifty'
        self.assertEqual(len(self._rs.pendingResultsFor(params)), 0)
        self._rs.addSinglePendingResult(params, '1234')
        self.assertEqual(len(self._rs.pendingResultsFor(params)), 1)
        params['b'] = 90
        params['c'] = 'ninety'
        self._rs.addSinglePendingResult(params, '5678')
        params['b'] = 90
        params['c'] = 'ninety'
        self._rs.addSinglePendingResult(params, '91011')
        self.assertEqual(len(self._rs.pendingResultsFor(dict(a=10))), 3)
        self.assertEqual(len(self._rs.pendingResultsFor(dict(b=50))), 1)
        self.assertEqual(len(self._rs.pendingResultsFor(dict(a=10, b=50))), 1)
        self.assertEqual(len(self._rs.pendingResultsFor(dict(a=15, b=50))), 0)

    def testNumberOfPendingResultsZero(self):
        '''Test we can handle zero pending results.'''
        self.assertEqual(self._rs.numberOfPendingResults(), 0)        

    def testNumberOfPendingResultsOne(self):
        '''Test we can count pending results.'''
        self._rs.addSinglePendingResult(self._rc[Experiment.PARAMETERS], '1234')
        self.assertEqual(self._rs.numberOfPendingResults(), 1)        

    def testJobId(self):
        '''Test we raise exceptions for unrecognised job ids.'''
        self._rs.addSinglePendingResult(self._rc[Experiment.PARAMETERS], '1234')
        with self.assertRaises(PendingResultException):
            self._rs.cancelSinglePendingResult('4567')
        with self.assertRaises(PendingResultException):
            self._rs.resolveSinglePendingResult('4567')

    def testDuplicateJobs(self):
        '''Test we catch addition of duplicate job ids.'''
        self._rs.addSinglePendingResult(self._rc[Experiment.PARAMETERS], '1234')
        self._rc[Experiment.PARAMETERS]['singleton'] = 3
        with self.assertRaises(Exception):
            self._rs.addSinglePendingResult(self._rc[Experiment.PARAMETERS], '1234')

    def testCancelNonExistentJob(self):
        '''Test we can't cancel non-existent job ids.'''
        self._rs.addSinglePendingResult(self._rc[Experiment.PARAMETERS], '1234')
        with self.assertRaises(Exception):
            self._rs.cancelSinglePendingResult('4567')

    def testCancelOnce(self):
        '''Test that a job can't be re-canceled.'''
        self._rs.addSinglePendingResult(self._rc[Experiment.PARAMETERS], '1234')
        self._rs.cancelSinglePendingResult('1234')
        with self.assertRaises(Exception):
            self._rs.cancelSinglePendingResult('1234')

    def testDuplicatePendingParameters(self):
        '''Test we can have multiple pending jobs with the same parameters.'''
        self._rs.addSinglePendingResult(self._rc[Experiment.PARAMETERS], '1234')
        self._rs.addSinglePendingResult(self._rc[Experiment.PARAMETERS], '4567')
        self.assertCountEqual(self._rs.pendingResults(), [ '1234', '4567' ])

        self._rc[Experiment.RESULTS]['first'] = 1
        self._rs.addSingleResult(self._rc)
        self._rs.cancelSinglePendingResult('1234')
        self._rc[Experiment.RESULTS]['first'] = 2
        self._rs.addSingleResult(self._rc)
        self._rs.cancelSinglePendingResult('4567')
        self.assertCountEqual(self._rs.pendingResults(), [])

        # check the two cancelled results were zeroed correctly
        rss = self._rs.dataframeFor(self._rc[Experiment.PARAMETERS])
        self.assertEqual(len(rss), 4)
        self.assertCountEqual(rss['first'], [ 0, 0, 1, 2 ])

        # check that we project out the right successes
        rsss = rss[rss[Experiment.STATUS] == True]
        self.assertEqual(len(rsss), 2)
        self.assertCountEqual(rsss['first'], [ 1, 2 ])

    def testPendingParameterNames(self):
        '''Test we have to respect parameter names when adding pending jobs.'''
        self._rc[Experiment.PARAMETERS]['duplicate'] = 10
        self._rs.addSingleResult(self._rc)

        # too many parameters, should be fine
        self._rc[Experiment.PARAMETERS]['triplicate'] = 20
        self._rs.addSinglePendingResult(self._rc[Experiment.PARAMETERS], '1234')

        # too few parameters, should fail
        del self._rc[Experiment.PARAMETERS]['triplicate']
        del self._rc[Experiment.PARAMETERS]['duplicate']
        with self.assertRaises(Exception):   
            self._rs.addSinglePendingResult(self._rc[Experiment.PARAMETERS], '1234')

    def testCancelJobById(self):
        '''Test we can cancel jobs by their identifier.'''
        self._rc[Experiment.PARAMETERS]['duplicate'] = 10
        self._rs.addSinglePendingResult(self._rc[Experiment.PARAMETERS], '1234')
        self._rc[Experiment.PARAMETERS]['duplicate'] = 20
        self._rs.addSinglePendingResult(self._rc[Experiment.PARAMETERS], '4567')
        self.assertCountEqual(self._rs.pendingResults(), [ '1234', '4567' ])

        # check job gets cancelled
        self._rs.cancelSinglePendingResult('1234')
        self.assertCountEqual(self._rs.pendingResults(), [ '4567' ])

        # check the exception is correct
        rcs = self._rs.resultsFor(dict(duplicate=10))
        self.assertEqual(len(rcs), 1)
        rc = rcs[0]
        self.assertTrue(isinstance(rc[Experiment.METADATA][Experiment.EXCEPTION], CancelledException))

    def testFailedResult(self):
        '''Test we can save a failed result, i.e., with an exception and no results.'''
        self._rc[Experiment.METADATA][Experiment.STATUS] = False
        self._rc[Experiment.METADATA][Experiment.EXCEPTION] = "An exception"
        self._rc[Experiment.METADATA][Experiment.TRACEBACK] = "...happened somewhere..."
        del self._rc[Experiment.RESULTS]
        self._rs.addSingleResult(self._rc)
        self.assertEqual(len(self._rs), 1)
        rcs = self._rs.resultsFor(self._rc[Experiment.PARAMETERS])
        self.assertEqual(len(rcs), 1)
        rc = rcs[0]
        self.assertDictEqual(self._rc[Experiment.METADATA], rc[Experiment.METADATA])
        self.assertDictEqual(self._rc[Experiment.PARAMETERS], rc[Experiment.PARAMETERS])

    def _resultsEqual(self, df, rc):
        '''Check that the dataframe contains a row with the given results.

        :param df: the dataframe
        :param rc: the results dict
        :returns: True if there's a corresponding row'''
        for d in [ Experiment.PARAMETERS, Experiment.RESULTS ]:  # ignore metadata
            for k in rc[d].keys():
                df = df[df[k] == rc[d][k]]
        return (len(df) > 0)

    def testRealAndPendingResults( self ):
        '''Test a sequence of real and pending results'''
        e = SampleExperiment()
        
        # create three results
        params1 = dict(a  = 1, b = 2)
        rc1 = e.set(params1).run()
        params2 = dict(a  = 10, b = 12)
        rc2 = e.set(params2).run()
        params3 = dict(a  = 45, b = 11)
        rc3 = e.set(params3).run()

        # add first result
        self._rs.addSingleResult(rc1)
        self.assertTrue(self._resultsEqual(self._rs.dataframeFor(params1), rc1))
        self.assertEqual(len(self._rs.dataframeFor(params2)), 0)
        self.assertEqual(len(self._rs.results()), 1)
        self.assertCountEqual(self._rs.pendingResults(), [])
        self.assertTrue(self._rs.ready())
        
        # add second result as pending
        self._rs.addSinglePendingResult(params2, '2')
        self.assertTrue(self._resultsEqual(self._rs.dataframeFor(params1), rc1))
        self.assertEqual(len(self._rs.dataframeFor(params2)), 0)
        self.assertEqual(len(self._rs.results()), 1)
        self.assertCountEqual(self._rs.pendingResults(), [ '2' ])
        self.assertFalse(self._rs.ready())
        
        # add third result as pending
        self._rs.addSinglePendingResult(params3, '3')
        self.assertTrue(self._resultsEqual(self._rs.dataframeFor(params1), rc1))
        self.assertEqual(len(self._rs.dataframeFor(params2)), 0)
        self.assertEqual(len(self._rs.dataframeFor(params3)), 0)
        self.assertEqual(len(self._rs.results()), 1)
        self.assertCountEqual(self._rs.pendingResults(), [ '2', '3' ])
        self.assertFalse(self._rs.ready())

        # resolve second result
        self._rs.addSingleResult(rc2)
        self._rs.cancelSinglePendingResult('2')
        self.assertTrue(self._resultsEqual(self._rs.dataframeFor(params1), rc1))
        self.assertTrue(self._resultsEqual(self._rs.dataframeFor(params2), rc2))
        self.assertEqual(len(self._rs.dataframeFor(params3)), 0)
        self.assertEqual(len(self._rs.results()), 3)
        self.assertCountEqual(self._rs.pendingResults(), [ '3' ])
        self.assertFalse(self._rs.ready())

        # cancel third result
        self._rs.cancelSinglePendingResult('3')
        self.assertTrue(self._resultsEqual(self._rs.dataframeFor(params1), rc1))
        self.assertTrue(self._resultsEqual(self._rs.dataframeFor(params2), rc2))
        self.assertEqual(len(self._rs.dataframeFor(params3)), 1)
        self.assertEqual(len(self._rs.dataframeFor(params3, only_successful=True)), 0)
        self.assertEqual(len(self._rs.results()), 4)
        self.assertCountEqual(self._rs.pendingResults(), [])
        self.assertTrue(self._rs.ready())

        # add pending result again under the same job id
        self._rs.addSinglePendingResult(params3, '3')
        self.assertTrue(self._resultsEqual(self._rs.dataframeFor(params1), rc1))
        self.assertTrue(self._resultsEqual(self._rs.dataframeFor(params2), rc2))
        self.assertEqual(len(self._rs.dataframeFor(params3)), 1)
        self.assertEqual(len(self._rs.results()), 4)
        self.assertCountEqual(self._rs.pendingResults(), [ '3' ])
        self.assertFalse(self._rs.ready())

        # cancel it again
        self._rs.cancelSinglePendingResult('3')
        self.assertTrue(self._resultsEqual(self._rs.dataframeFor(params1), rc1))
        self.assertTrue(self._resultsEqual(self._rs.dataframeFor(params2), rc2))
        self.assertEqual(len(self._rs.dataframeFor(params3)), 2)
        self.assertEqual(len(self._rs.results()), 5)
        self.assertCountEqual(self._rs.pendingResults(), [])
        self.assertTrue(self._rs.ready())

    def testLocking(self):
        '''Test we can lock result sets.'''
        e = SampleExperiment()
        
        # create three results
        params1 = dict(a  = 1, b = 2)
        rc1 = e.set(params1).run()
        params2 = dict(a  = 10, b = 12)
        rc2 = e.set(params2).run()
        params3 = dict(a  = 45, b = 11)
        rc3 = e.set(params3).run()

        # add first result, with second pending
        self.assertFalse(self._rs.isLocked())
        self._rs.addSingleResult(rc1)
        self._rs.addSinglePendingResult(params2, '1234')

        # finish and lock the result set
        self._rs.finish()
        self.assertEqual(self._rs.numberOfResults(), 2)
        self.assertEqual(self._rs.numberOfPendingResults(), 0)
        self.assertTrue(self._rs.isLocked())

        # make sure we can't add further jobs or otherwise change the result set
        with self.assertRaises(ResultSetLockedException):
            self._rs.addSingleResult(rc3)
        with self.assertRaises(ResultSetLockedException):
            self._rs.addSinglePendingResult(rc3, '3456')
        with self.assertRaises(ResultSetLockedException):
            self._rs['attribute'] = 'not saved'

        # make sure we still have access
        self.assertEqual(len(self._rs.results()), 2)


if __name__ == '__main__':
    unittest.main()





