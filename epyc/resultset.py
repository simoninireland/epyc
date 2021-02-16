# A set of results for experiments in a given parameter space
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

from epyc import Experiment, ResultsDict
import numpy                       # type: ignore
from pandas import DataFrame       # type: ignore
import sys
import traceback
from datetime import datetime
if sys.version_info >= (3, 8):
    from typing import Final, List, Dict, Set, Any, Type, Optional
else:
    # backwards compatibility with Python 35, Python36, and Python37 
    from typing import List, Dict, Set, Any, Type, Optional
    from typing_extensions import Final


class CancelledException(Exception):
    '''An exception stored within the :class:`Experiment` :term:`results dict`
    when a pending result is cancelled without completeing the experiment.
    This means that all experiments started either complete successfully (and
    have their results recorded), or fail within the experiment itself
    (and have that exception stored, without results), or are cancelled
    (and have this exception and a traceback stored).'''

    def __init__(self):
        super(CancelledException, self).__init__('Cancelled')


class ResultSetLockedException(Exception):
    '''An exception raised if an attempt is made to write new results to a result
    set that's been locked by a call to :meth:`ResultSet.finish`.'''

    def __init__(self):
        super(ResultSetLockedException, self).__init__('Result set locked')


class PendingResultException(Exception):
    '''An exception raised if an invalid pending result job identifier is used. A common
    cause of this is a pending result that failed on submission and so was never actually started.

    :param jobid: the job id'''

    def __init__(self, jobid : str):
        super(PendingResultException, self).__init__('Unrecognised pending result job identifier {j}'.format(j=jobid))
        self._jobid = jobid

    def jobid(self) -> str:
        '''Return the uinrecopgnised job id.

        :returns: the job id'''
        return self._jobid


class ResultSet(object):
    '''A "page" in a lab notebook for the results of a particular set
    of experiments. This will consist of metadata, notes, and a data table resulting from
    the execution of the experiment. Each experiment runs with a specific
    set of parameters: the parameter names are fixed once set initially, with
    the specific values being stored alongside each result. There
    may be multiple results for the same parameters, to allow for
    repetition of experiments at a data point.
    Results committ5ed to result sets are immutable: once entered, a result can't be deleted
    or changed.

    Result sets also record "pending" results, allowing us to record experiments
    in progress. A pending result can be finalised by providing it with a
    value, or can be cancelled.

    A result set can be used very Pythonically using a :term:`results dict` holding
    the metadata, parameters, and results of experiments. For larger experiment
    sets the results are automatically typed using ``numpy``'s ``dtype`` system,
    which both provides more checking and works well with more archival storage
    formats like HDF5 (see :class:`HDF5LabNotebook`).  

    :param nb: notebook this result set is part of
    :param description: (optional) description for the result set (defaults to a datestamp)
    '''

    # Pending results management
    JOBID : Final[str] = 'epyc.resultset.pending-jobid'     #: Column name for pending result job identifier.

    # Typing
    TypeMapping : Dict[Type, numpy.dtype] = dict()          #: Default type mapping from Python types to ``numpy`` ``dtypes``.
    ZeroMapping : Dict[str, Any] = { 'i': 0,
                                     'f': 0.0,
                                     'c': 0 + 0j,
                                     'b': False,
                                     'U': '',
                                     'S': '',
                                   }                        #: Default ("zero") values for all the numpy type kinds we handle.

    @classmethod
    def _init_statics(cls):
        '''Initialise the static members that need complex constructors.'''
        cls.TypeMapping[int] = numpy.dtype(int)
        cls.TypeMapping[float] = numpy.dtype(float)
        cls.TypeMapping[complex] = numpy.dtype(complex)
        cls.TypeMapping[bool] = numpy.dtype(bool)
        cls.TypeMapping[str] = numpy.dtype(str)
        cls.TypeMapping[datetime] = numpy.dtype(str)
        cls.TypeMapping[Exception] = numpy.dtype(str)

    def __init__(self, description : str =None):
        # generate a description from today's date is none is provided 
        if description is None:
            description = "Results collected on {d}".format(d=datetime.now())

        self._description : str = description                  # free text description
        self._attributes : Dict[str, Any] = dict()             # attributes
        self._names : Dict[str, Optional[List[str]]] = dict()  # dict of names from the results dicts
        self._names[Experiment.METADATA] = None
        self._names[Experiment.PARAMETERS] = None
        self._names[Experiment.RESULTS] = None
        self._results : DataFrame = DataFrame()                # experimental results
        self._dtype : Optional[numpy.dtype] = None             # experimental results dtype
        self._pending : DataFrame = DataFrame()                # pending results
        self._pendingdtype : Optional[numpy.dtype] = None      # pending results dtype
        self._dirty: bool = False                              # (pending) results need persisting
        self._typedirty: bool  = False                         # structure of results has changed
        self._locked : bool = False                            # locked to further results


    # ---------- Metadata access ----------
    
    def description(self) -> str:
        '''Return the free text description of the result set.

        :returns: the description'''
        return self._description

    def setDescription(self, d : str):
        '''Set the free text description of the result set.

        :param d: the description'''
        self._description = d
        self.dirty()

    def names(self) -> Dict[str, Optional[List[str]]]:
        '''Return a dict of sets of names, corresponding to the entries in
        the results dicts for this result set. If only pending results have so far
        been added the :attr:`Experiment.METADATA` and :attr:`Experiment.RESULTS`
        sets will be empty.

        :returns: the dict of parameter names'''
        return self._names

    def metadataNames(self) -> List[str]:
        '''Return the set of metadata  names associated with this result set. If
        no results have been submitted, this set will be empty.

        :returns: the set of experimental metadata names'''
        ns = self._names[Experiment.METADATA]
        if ns is None:
            ns = []
        return ns

    def parameterNames(self) -> List[str]:
        '''Return the set of parameter names associated with this result set. If
        no results (pending or real) have been submitted, this set will be empty.

        :returns: the set of experimental parameter names'''
        ns = self._names[Experiment.PARAMETERS]
        if ns is None:
            ns = []
        return ns

    def resultNames(self) -> List[str]:
        '''Return the set of result names associated with this result set. If
        no results have been submitted, this set will be empty.

        :returns: the set of experimental result names'''
        ns = self._names[Experiment.RESULTS]
        if ns is None:
            ns = []
        return ns


    # ---------- locking ----------

    def finish(self):
        '''Finish and lock this result set. This cancels any pending results
        and locks the result set against future additions. This is useful to tidy up 
        after experiments are finished, and protects against accidentally re-using
        a result set for something else.'''
        if not self.isLocked():
            # cancel any peiding results
            for j in self.pendingResults():
                self.cancelSinglePendingResult(j)

            # lock the result set
            self._locked = True

    def isLocked(self) -> bool:
        '''Returns true if the result set is locked.

        :returns: True if the result set is locked'''
        return self._locked

    def assertUnlocked(self):
        '''Tests whether the result set is locked, and raises a :class:`ResultSetLockedException`
        if so. This is used to protect update methods, since locked result sets are never
        updated.'''
        if self.isLocked():
            raise ResultSetLockedException()


    # ---------- Attributes ----------

    def setAttribute(self, k : str, v : Any):
        '''Set the given attribute.

        :param k: the key
        :param v: the attribute value'''
        self.assertUnlocked()
        self._attributes[k] = v
        self.dirty()

    def getAttribute(self, k : str) -> Any:
        '''Retrieve the given attribute. A KeyException will be
        raised if the attribute doesn't exist.

        :param k: the attribute
        :returns: the attribute value'''
        return self._attributes[k]

    def keys(self) -> Set[str]:
        '''Return the set of attributes.

        :returns: the attribute keys'''
        return set(self._attributes.keys())

    def __delitem__(self, k : str):
        '''Delete the named attribute. This method is invoiked
        by the ``del`` operator. A KeyException will be
        raised if the attribute doesn't exist.

        :param k: the attribute'''
        self.assertUnlocked()
        del self._attributes[k]
        self.dirty()

    def __setitem__(self, k : str, v : Any):
        '''Set the given attribute. The dict-like form of :meth:`setAttribute`.

        :param k: the key
        :param v: the attribute value'''
        self.assertUnlocked()
        self.setAttribute(k, v)

    def __getitem__(self, k : str) -> Any:
        '''Retrieve the given attribute. The dict-like form of :meth:`getAttribute`.

        :param k: the attribute
        :returns: the attribute value'''
        return self.getAttribute(k)
        
    def __contains__(self, k):
        '''True if there is an attribute with the given name.

        :oparam k: the attribute
        :returns: True if that attribute exists'''
        return k in self._attributes


    # ---------- Dirtiness ----------

    def isDirty(self) -> bool:
        '''Test whether the result set is dirty, i.e., if its contents need persisting
        (if the containing notebook is persistent).

        :returns: True if the result set is dirty'''
        return self._dirty

    def dirty(self, f : bool =True):
        '''Mark the result set as dirty (the default) or clean.

        :param f: True if the result set is dirty'''
        self._dirty = f

    def isTypeChanged(self) -> bool:
        '''Test whether the result set has changed its metadata, parameters,
        or results. This is used by persistent notebooks to re-construct the
        backing storage.

        :returns: True if the result set has changed type'''
        return self._typedirty

    def typechanged(self, f : bool =True):
        '''Mark the result set as having changed type (the default) or not.

        :param f: True if the result set has changed type'''
        self._typedirty = f


    # ---------- Type management ----------

    def dtype(self) -> numpy.dtype:
        '''Return the dtype of the results, combining the metadata, parameters,
        and results elements.

        :returns: the dtype'''
        if self._dtype is None:
            raise Exception('No results dtype yet known')
        return self._dtype

    def setDtype(self, dtype) -> numpy.dtype:
        '''Set the dtype for the results. This should be done with care, ensuring that
        the element names all match. It does however allow precise control over the way
        data is stored (if required).

        :param dtype: the dtype'''
        self.assertUnlocked()
        self._dtype = dtype

    def pendingdtype(self) -> numpy.dtype:
        '''Return the dtype of pending results, using just parameter elements.

        :returns: the dtype'''
        if self._pendingdtype is None:
            raise Exception('No pending results dtype yet known')
        return self._pendingdtype

    def setPendingResultDtype(self, dtype) -> numpy.dtype:
        '''Set the dtype for pending results. This should be done with care, ensuring that
        the element names all match.

        :param dtype: the dtype'''
        self._pendingdtype = dtype

    def typeToDtype(self, t : type) -> numpy.dtype:
        '''Return the dtype of the given Python type. An exception
        is thrown if there is no appropriate mapping.

        :param t: the (Python) type
        :returns: the dtype of the value'''
        if issubclass(t, numpy.number) or issubclass(t, numpy.ndarray):
            # numpy types are retained
            return numpy.dtype(t)
        else:
            # Python types are translated through the type mapping
            return self.TypeMapping[t]

    def valueToDtype(self, v : Any) -> numpy.dtype:
        '''Return the dtype of a Python value. An exception
        is thrown if there is no appropriate mapping.

        :param v: the value
        :returns: the dtype'''
        if isinstance(v, list):
            et = self.valueToDtype(v[0])
            return numpy.dtype((et, (len(v),)))
        else:
            return self.typeToDtype(type(v))

    def inferDtype(self, rc : ResultsDict):
        '''Infer the dtype of the given result dict. This will include all the
        standard and exceptional metedata defined for an :class:`Experiment`, plus
        the parameters and results (if present) for the results dict.

        If more elements are provided than have previously been seen, the underlying
        results dataframe will be extended with new columns.

        This method will be called automatically if no explicit dtype has been provided 
        for the result set by a call to :meth:`setDtype`.

        :returns: the dtype'''
        rebuild = False

        # extract parameter names (should always be present)
        parameterNames = list(rc[Experiment.PARAMETERS].keys())
        pns = self._names[Experiment.PARAMETERS]
        if pns is None:
            # first set, capture
            parameterNames.sort()
            self._names[Experiment.PARAMETERS] = parameterNames
            rebuild = True
        else:
            # additional set, check for extensions
            dps = set(parameterNames).difference(set(pns))
            if len(dps) > 0:
                # extend the names
                parameterNames = list(set(parameterNames).union(set(pns)))
                parameterNames.sort()
                self._names[Experiment.PARAMETERS] = parameterNames
                rebuild = True

        # extract results if the experiment was successful
        if rc[Experiment.METADATA][Experiment.STATUS]:
            resultNames = list(rc[Experiment.RESULTS].keys())
            rns = self._names[Experiment.RESULTS] 
            if rns is None:
                # first set, capture
                resultNames.sort()
                self._names[Experiment.RESULTS] = resultNames
                rebuild = True
            else:
                # additional set, check for extensions
                dps = set(resultNames).difference(set(rns))
                if len(dps) > 0:
                    # extend the names
                    resultNames = list(set(resultNames).union(set(rns)))
                    resultNames.sort()
                    self._names[Experiment.RESULTS] = resultNames
                    rebuild = True

        # extract metadata names, including all standard and exceptional values
        metadataNames = list(rc[Experiment.METADATA].keys())
        mns = self._names[Experiment.METADATA]
        if mns is None:
            # first set, capture
            metadataNames = list(set(metadataNames).union(Experiment.StandardMetadata))
            metadataNames.sort()
            self._names[Experiment.METADATA] = metadataNames
            rebuild = True
        else:
            # additional set, check for extensions
            dps = set(metadataNames).difference(set(mns))
            if len(dps) > 0:
                # extend the names
                metadataNames = list(set(metadataNames).union(set(mns)))
                metadataNames.sort()
                self._names[Experiment.METADATA] = metadataNames
                rebuild = True
        
        # (re-)construct the dtype if needed
        if rebuild:
            if self._dtype is None:
                # no existing dtype, use a blank one
                oldnames = set()
                oldfields = dict()
            else:
                # the old dtype, for extensions
                olddtype = self._dtype
                oldnames = olddtype.names
                oldfields = olddtype.fields

            # extract all the names in canonical order
            names = []
            for d in [ Experiment.METADATA, Experiment.PARAMETERS, Experiment.RESULTS ]:
                ns = self._names[d]
                if ns is not None:
                    names.extend(ns.copy())

            # infer the types associated with each element using the type mapping
            types = dict()
            for k in self._names[Experiment.METADATA]:
                if k in oldnames:
                    # existing field, retain it
                    types[k] = oldfields[k][0]
                else:
                    if k in Experiment.StandardMetadata:
                        # standard element, get its type from the type mapping
                        # (this gives the Python-level type, not the dtype)
                        types[k] = self.typeToDtype(Experiment.StandardMetadataTypes[k])
                    else:
                        # new metadata element, grab its type
                        v = rc[Experiment.METADATA][k]
                        try:
                            types[k] = self.valueToDtype(v)
                        except Exception:
                            raise Exception('No type mapping for metadata {k} ({v})'.format(k=k, v=v))
            for d in [ Experiment.PARAMETERS, Experiment.RESULTS ]:
                if self._names[d] is not None:
                    for k in self._names[d]:
                        if k in oldnames:
                            # existing field, retain it
                            types[k] = oldfields[k][0]
                        elif k in rc[d]:
                            # new field, infer its type
                            v = rc[d][k]
                            try:
                                types[k] = self.valueToDtype(v)
                            except Exception:
                                raise Exception('No type mapping for {k} ({v})'.format(k=k, v=v))

            # form the dtype
            elements = []
            for d in [ Experiment.METADATA, Experiment.PARAMETERS, Experiment.RESULTS ]:
                if self._names[d] is not None:
                    for k in self._names[d]:
                        if k in types:
                            elements.append((k, types[k]))
            self._dtype = numpy.dtype(elements)

            # if we had results, add the new columns
            nr = len(self._results)
            if nr > 0:
                # add new columns to each element
                for d in [ Experiment.METADATA, Experiment.PARAMETERS, Experiment.RESULTS ]:
                    for k in self._names[d]:
                        if k not in self._results:
                            self._results[k] = [self.zero(types[k])] * nr
            else:
                # no results, create the table with the correct columns
                self._results = DataFrame(columns=types.keys())

            # if we had pending results, add the new columns
            nr = len(self._pending)
            if nr > 0:
                # add new columns to each element
                for k in self._names[Experiment.PARAMETERS]:
                    if k not in self._pending:
                        self._pending[k] = [self.zero(types[k])] * nr

            # our type has changed
            self.typechanged()

        # return the dtype
        return self._dtype

    def inferPendingResultDtype(self, params : Dict[str, Any]):
        '''Infer the dtype of the pending results of
        given dict of experimental parameters. This is essentially the same operation as
        :meth:`inferDtype` but restricted to experimental parameters and including
        a string job identifier.

        :param params: the experimental parameters
        :returns: the pending results dtype'''
        rebuild = False

        # extract parameter names
        parameterNames = list(params.keys())
        pns = self._names[Experiment.PARAMETERS]
        if pns is None:
            # first set, capture
            parameterNames.sort()
            self._names[Experiment.PARAMETERS] = parameterNames
            rebuild = True
        else:
            # additional set, check for extensions
            dps = set(parameterNames).difference(set(pns))
            if len(dps) > 0:
                # extend the names
                parameterNames = list(set(parameterNames).union(set(pns)))
                parameterNames.sort()
                self._names[Experiment.PARAMETERS] = parameterNames
                rebuild = True

        # (re-)construct the dtype and pending table if needed
        if rebuild or self._pendingdtype is None:
            parameterNames = self._names[Experiment.PARAMETERS]

            if self._pendingdtype is None:
                # no existing dtype, use a blank one
                oldnames = set()
                oldfields = dict()
            else:
                # the old dtype, for extensions
                olddtype = self._pendingdtype
                oldnames = olddtype.names
                oldfields = olddtype.fields

            # infer the types associated with each element using the type mapping
            types = dict()
            for k in parameterNames:
                if k in oldnames:
                    # existing field, retain it
                    types[k] = oldfields[k][0]
                else:
                    # new field, infer its type
                    v = params[k]
                    try:
                        types[k] = self.valueToDtype(v)
                    except Exception:
                        raise Exception('No type mapping for pending result {k} ({v})'.format(k=k, v=v))

            # add the job id column
            types[self.JOBID] = self.typeToDtype(str)    # job ids are expected to be strings

            # form the dtype
            elements = []
            for k in parameterNames:
                elements.append((k, types[k]))
            elements.append((self.JOBID, types[self.JOBID]))
            self._pendingdtype = numpy.dtype(elements)

            # if we had results, add the new columns
            nr = len(self._results)
            if nr > 0:
                # add new columns to each element
                for k in parameterNames:
                    if k not in self._results:
                        self._results[k] = [self.zero(types[k])] * nr

            # if we had pending results, add the new columns
            nr = len(self._pending)
            if nr > 0:
                # add new columns to each element
                for k in parameterNames:
                    if k not in self._pending:
                        self._pending[k] = [self.zero(types[k])] * nr
            else:
                # no pending results, create the table with the correct columns
                self._pending = DataFrame(columns=types.keys())

            # our type has changed
            self.typechanged()

        # return the dtype
        return self._pendingdtype

    def zero(self, dtype : numpy.dtype) -> Any:
        '''Return the appropriate "zero" for the given simple dtype.

        :param dtype: the dtype
        :returns: "zero"'''
        if dtype.kind in self.ZeroMapping:
            return self.ZeroMapping[dtype.kind]
        else:
            print('No zero value for type {dt}, using 0.0'.format(dt=dtype), file=sys.stderr)
            return 0.0     # and hope for the best


    # ---------- Adding results ----------

    def addSingleResult(self, rc : ResultsDict):
        '''Add a single result. This should be a single :term:`results dict`
        as returned from an instance of :class:`Experiment`, that contains metadata,
        parameters, and result.

        The results dict may add metadata, parameters, or results to the result
        set, and these will be assumed to be present from then on. Missing values
        in previously-saved results will receive default values.

        :param rc: a results dict'''
        self.assertUnlocked()

        # match the types to the passed information
        dt = self.inferDtype(rc)

        # flatten the key/value pairs in the results dict
        # (in case of clashes, results take precedence)
        row = dict()
        for d in [ Experiment.METADATA, Experiment.PARAMETERS ]:
            for k in self._names[d]:
                if k not in rc[d]:
                    row[k] = self.zero(dt[k])
                else:
                    row[k] = rc[d][k]
        if self._names[Experiment.RESULTS] is not None:
            for k in self._names[Experiment.RESULTS]:
                if not rc[Experiment.METADATA][Experiment.STATUS] or k not in rc[Experiment.RESULTS]:
                    # failed results and missing fields are zeroed
                    row[k] = self.zero(dt[k])
                else:
                    row[k] = rc[Experiment.RESULTS][k]

        # add the results to the dataframe
        df = self._results
        df.loc[len(df.index)] = row

        # mark as dirty
        self.dirty()


    # ---------- Manage pending results ----------

    def addSinglePendingResult(self, params : Dict[str, Any], jobid : str):
        '''Add a pending result for the given point in the parameter space
        under the given job identifier. The identifier will generally be
        meaningful to the lab that submitted the request. They must be unique.

        :param params: the experimental parameters
        :param jobid: the job id'''
        self.assertUnlocked()

        # match types
        self.inferPendingResultDtype(params)

        # check the validity of the parameters requested
        dps = set(self.parameterNames()).difference(set(params.keys()))
        if len(dps) > 0:
            raise Exception('Missing experimental parameters: {dps}'.format(dps=dps))

        # make sure we're not duplicating
        df = self._pending
        if jobid in df[self.JOBID].values:
            raise Exception('Duplicate pending result {j}'.format(j=jobid))

        # add a line to the pending dataframe
        row = params.copy()
        row[self.JOBID] = jobid
        df.loc[len(df.index)] = row

        # mark us as dirty
        self.dirty()

    def pendingResults(self) -> List[str]:
        '''Return the job identifiers of all pending results.

        :returns: a list of pending job identifiers'''
        if self.numberOfPendingResults() == 0:
            return []
        else:
            return list(self._pending[self.JOBID])

    def numberOfPendingResults(self) -> int:
        '''Return the number of pending results.

        :returns: the number of pending results'''
        return len(self._pending)

    def pendingResultsFor(self, params : Dict[str, Any]) -> List[str]:
        '''Return the ids of all pending results with the given parameters. Not all parameters
        have to be provided, allowing for partial matching.

        :param params: the experimental parameters
        :returns: a list of job ids'''

        # if we have no pending jobs, exit immediately
        if self.numberOfPendingResults() == 0:
            return []

        # check the validity of the parameters requested
        dps = set(params.keys()).difference(set(self.parameterNames()))
        if len(dps) > 0:
            raise Exception('Unexpected experimental parameters: {dps}'.format(dps=dps))

        # project-out the rows with these values
        df = self._pending
        for k in params.keys():
            try:
                _ = iter(params[k])    # will raise an exception if applied to a singleton

                # several possible parameter values, project them all out
                df = df[df.isin(params[k]).any(1)]
            except TypeError:
                # singleton value, just capture the results that match
                df = df[df[k] == params[k]]

        # return the ids
        return list(df[self.JOBID])

    def _dropPendingResult(self, jobid : str):
        '''Drop a pending result from the pending table.

        :param jobid: the job id'''

    def resolveSinglePendingResult(self, jobid : str):
        '''Resolve the given pending result. This drops the job from the
        pending results table. User code should call :meth:`LabNotebook.resolvePendingResult`
        rather than using this method directly, since this method doesn't actually
        store the completed pending result, it just manages its non-pending-ness.

        :param jobid: the job id'''
        self.assertUnlocked()

        # drop the job line from the pending table
        df = self._pending
        ids = df[df[self.JOBID] == jobid].index
        if len(ids) == 0:
            # identified job doesn't exist
            raise PendingResultException(jobid)
        elif len(ids) != 1:
            # shouldn't be more than one either....
            raise Exception('Internal data structure failure (job {j})'.format(j=jobid))
        df.drop(index=ids, inplace=True)
        #print('Resolved {j}'.format(j=jobid), file=sys.stderr)

        # mark us as dirty
        self.dirty()

    def cancelSinglePendingResult(self, jobid : str):
        '''Cancel a pending job, This records the cancellation using a
        :class:`CancelledException`, storing a traceback to show where the cancellation
        was triggered from. User code should call :meth:`LabNotebook.cancelPendingResult`
        rather than using this method directly.

        Cancelling a result generates a message to standard output.

        :param jobid: the job id'''
        self.assertUnlocked()

        # create the "marker" exception for the results dict
        rc = Experiment.resultsdict()
        try:
            raise CancelledException()
        except CancelledException as ex:
            # grab a traceback
            tb = traceback.format_exc()

            # fill in the limited metadata we have 
            rc[Experiment.METADATA][Experiment.STATUS] = False
            rc[Experiment.METADATA][Experiment.END_TIME] = datetime.now()
            rc[Experiment.METADATA][Experiment.EXCEPTION] = ex
            rc[Experiment.METADATA][Experiment.TRACEBACK] = tb

        # find the job line in the pending table
        df = self._pending
        ids = df[df[self.JOBID] == jobid].index
        if len(ids) == 0:
            # identified job doesn't exist
            raise PendingResultException(jobid)
        elif len(ids) != 1:
            # shouldn't be more than one either....
            raise Exception('Internal data structure failure (job {j})'.format(j=jobid))

        # extract the parameters
        id = ids[0]
        row = df.loc[id]
        for k in self._names[Experiment.PARAMETERS]:
            rc[Experiment.PARAMETERS][k] = row[k]
        
        # add the result to the results table
        self.addSingleResult(rc)

        # drop the line in the pending table
        df.drop(index=ids, inplace=True)
        print('Cancelled {j}'.format(j=jobid), file=sys.stderr)

        # mark us as dirty
        self.dirty()

    def ready(self) -> bool:
        '''Test whether there are pending results.

        :returns: True if all pending results have been either resolved or cancelled'''
        return (self.numberOfPendingResults() == 0)

    def pendingResultParameters(self, jobid : str) -> Dict[str, Any]:
        '''Return a dict of the parameters for the given pending result.

        :param jobid: the job id
        :returns: a dict of parameter values'''
        df = self._pending

        # retieve the line from the pending table for the given job
        df = df[df[self.JOBID] == jobid]
        if len(df) < 1:
            raise Exception('No pending job {j}'.format(j=jobid))
        elif len(df) > 1:
            raise Exception('Corrupted internal data structures for pending result {j}'.format(j=jobid))

        # unpack into a dict and return it
        js = df.iloc[0]
        params = dict()
        for k in self.parameterNames():
            params[k] = js[k]
        return params


    # ---------- Retrieving results ----------

    def dataframe(self, only_successful : bool =False) -> DataFrame:
        '''Return all the available results.
        The results are returned as a `pandas` DataFrame object, which is detached
        from the results held in the result set, thereby keeping the result set
        itself immutable.

        You can pre-filter the contents of the dataframe to only include results
        for specific parameter values using :meth:`dataframeFor`. You can also discard
        any unsuccessful results the using only_successful flag.

        :param only_successful: (optional) filter out any failed results (defaults to False)
        :returns: a dataframe of results'''
        df = self._results.copy()
        if len(df) > 0 and only_successful:
            # filter out only the successful runs (if there are any to start with)
            df = df[df[Experiment.STATUS] == True]
        return df

    def dataframeFor(self, params : Dict[str, Any], only_successful : bool =False) -> DataFrame:
        '''Extract a dataframe the results for only the given set of parameters. These need not be
        all the parameters for the experiments, so it's possible to project-out
        all results for a sub-set of the parameters. If a parameter is mapped to
        an iterator or list then these are treated as disjunctions and select
        *all* results with *any* of these values for that parameter.

        An empty set of parameters filters out nothing and so returns all the
        results. This is far less efficient that calling :meth:`dataframe`.

        The results are returned as a `pandas` DataFrame object, which is detached
        from the results held in the result set, thereby keeping the result set
        itself immutable.

        You can also discard any unsuccessful results the using only_successful flag.

        :param params: a dict of parameters and values
        :param only_successful: (optional) filter out any failed results (defaults to False)
        :returns: a dataframe containing results matching the parameter constraints'''

        # if we have no results, exit immediately
        if self.numberOfResults() == 0:
            return DataFrame()

        # check the validity of the parameters requested
        dps = set(params).difference(set(self.parameterNames()))
        if len(dps) > 0:
            raise Exception('Unexpected experimental parameters: {dps}'.format(dps=dps))

        # project-out the rows with these values
        df = self._results.copy()
        for k in params.keys():
            try:
                _ = iter(params[k])    # will raise an exception if applied to a singleton

                # several possible parameter values, project them all out
                df = df[df.isin(params[k]).any(1)]
            except TypeError:
                # singleton value, just capture the results that match
                df = df[df[k] == params[k]]

        # filter out only the successful runs (if there are any to start with)
        if len(df) > 0 and only_successful:
           df = df[df[Experiment.STATUS] == True]

        # return the dataframe with the projected-out results
        return df

    def _dataframeToDict(self, df : DataFrame) -> List[ResultsDict]:
        '''Convert all the rows in a dataframe into a results dict with the correct
        structure for this result set.

        :param df: the dataframe
        :returns: a list of results dicts'''
        results = []
        for i in df.index:
            res = df.loc[i]
            rc = Experiment.resultsdict()
            for d in [ Experiment.METADATA, Experiment.PARAMETERS ]:
                for k in self._names[d]:
                    rc[d][k] = res[k]
            if rc[Experiment.METADATA][Experiment.STATUS]:
                for k in self._names[Experiment.RESULTS]:
                    rc[Experiment.RESULTS][k] = res[k]
            results.append(rc)
        return results

    def results(self) -> List[ResultsDict]:
        '''Return all the results as a list of results dicts. This is useful for
        avoiding the use of ``pandas`` and having a more Pythonic interface -- which
        is also a lot less efficient and more memory-hungry.

        :returns: a list of results dicts'''
        return self._dataframeToDict(self.dataframe())

    def resultsFor(self, params : Dict[str, Any]) -> List[ResultsDict]:
        '''Return all the results for the given paramneters as a list of results dicts.
        This is useful for avoiding the use of ``pandas`` and having a more Pythonic
        interface -- which is also a lot less efficient and more memory-hungry. The
        parameters are interpreted as for :meth:`dataframeFor`, with lists or other
        iterators being converted into disjunctions of values.
        
        :param params: the parameters
        :returns: a list of results dicts'''
        return self._dataframeToDict(self.dataframeFor(params))

    def numberOfResults(self) -> int:
        '''Return the number of results in the results set, including any
        repetitions at the same parameter point.

        :returns: the total number of results'''
        return len(self._results.index)

    def __len__(self) -> int:
        '''Return the number of results in the results set, including any
        repetitions at the same parameter point.mEquivalent to :meth:`numberOfResults`.

        :returns: the number of results'''
        return self.numberOfResults()


    # ---------- Retrieving parameter names and values ----------

    def parameterRange(self, param : str) -> Set[Any]:
        '''Return all the values for this parameter for which we have results.

        :param param: the parameter name
        :returns: a collection of values for which we have data'''

        # check the parameter is legal
        if param not in self.parameterNames():
            raise Exception('No experimental paramater {p}'.format(p=param))

        # project out all the values
        df = self._results
        return set(df[param].unique())

    def parameterSpace(self) -> Dict[str, Any]:
        '''Return a dict mapping parameter names to all their values,
        which is the space of all possible paramater points at which results
        *could* have been collected.
        This does not guarantee that all combinations of values *have* results
        associated with them: that function is provided by :meth:`parameterCombinations`.

        :returns: a dict mapping parameter names to their ranges'''
        ps = dict()
        for k in self.parameterNames():
            ps[k] = self.parameterRange(k)
        return ps

    def parameterCombinations(self) -> List[Dict[str, Any]]:
        '''Return a list of all combinations of parameters for which we have results,
        as a list of dicts. This means that there are results (possible more than
        one set) associated with the combination of parameters in each dict.
        The ranges of the parameters can be found using :meth:`parameterSpace`.

        :returns: a list of dicts'''
        raise NotImplementedError('TBD')

