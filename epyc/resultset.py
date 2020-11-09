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
from datetime import datetime
from typing import Final, List, Dict, Set, Any, Type, Optional


class ResultSet(object):
    '''A "page" in a lab notebook for the results of a particular set
    of experiments. This will consist of metadata, notes, and a data table resulting from
    the execution of the experiment. Each experiment runs with a specific
    set of parameters: the parameter names are fixed once set initially, with
    the specific values being stored alongside each result. There
    may be multiple results for the same parameters, to allow for
    repetition of experiments at a data point.
    Result sets also record "pending" results, allowing us to record experiments
    in progress. A pending result can be finalised by providing it with a
    value, or can be deleted.

    Result sets are immutable: once entered, a result can't be deleted
    or changed. Pending results can however be cancelled.

    A result set can be used very Pythonically using a :term:`results dict` holding
    the metadata, parameters, and results of experiments. For larger experiment
    sets the results are automatically typed using ``numpy``'s ``dtype`` system,
    which both provides more checking and works well with more archival storage
    formats like HDF5 (see :class:`HDF5LabNotebook`).  

    :param nb: notebook this result set is part of
    :param title: (optional) title for the experiment (defaults to a datestamp)
    '''

    # Pending results management
    JOBID : Final[str] = 'epyc.resultset.pending-jobid'     #: Column name for pending result job identifier.

    # Typing
    TypeMapping : Dict[Type, numpy.dtype] = { int: numpy.int64, 
                                              float: numpy.float64,
                                              complex: numpy.complex128,
                                              bool: numpy.bool,
                                              str: numpy.str,
                                              datetime: numpy.str,
                                              Exception: numpy.str,
                                            }               #: Default type mapping from Python types to ``numpy`` ``dtypes``.


    def __init__(self, title : str =None):
        # generate a title from today's date is none is provided 
        if title is None:
            title = "{d}".format(d=datetime.now())

        self._title : str = title                              # title
        self._attributes : Dict[str, Any] = dict()             # attributes
        self._names : Dict[str, Optional[List[str]]] = dict()  # dict of names from the results dicts
        self._names[Experiment.METADATA] = None
        self._names[Experiment.PARAMETERS] = None
        self._names[Experiment.RESULTS] = None
        self._results : DataFrame = DataFrame()                # experimental results
        self._dtype : Optional[numpy.dtype] = None             # experimental results dtype
        self._pending : DataFrame = DataFrame()                # pending results
        self._pendingdtype : Optional[numpy.dtype] = None      # pending results dtype
        self._dirty: bool  = False                             # (pending) results need persisting
        self._typedirty: bool  = False                         # structure of results has changed


    # ---------- Metadata access ----------

    def title(self) -> str:
        '''Return the title of the experiment corresponding to this result set.

        :returns: the title'''
        return self._title
        
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


    # ---------- Attributes ----------

    def setAttribute(self, k : str, v : Any):
        '''Set the given attribute.

        :param k: the key
        :param v: the attribute value'''
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
        del self._attributes[k]
        self.dirty()

    def __setitem__(self, k : str, v : Any):
        '''Set the given attribute. The dict-like form of :meth:`setAttribute`.

        :param k: the key
        :param v: the attribute value'''
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
        '''Return the dtype of the given Python value. An exception
        is thrown if there is no appropriate mapping.

        :param t: the type
        :returns: the dtype of the value'''
        if issubclass(t, numpy.number):
            # numpy types are retained
            return t
        else:
            # Python types are translated through the type mapping
            return self.TypeMapping[t]

    def inferDtype(self, rc : ResultsDict):
        '''Infer the dtype of the given result dict. This will include all the
        standard and exceptional metedata dfined for an :class:`Experiment`, plus
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
                        t = Experiment.StandardMetadataTypes[k]
                    else:
                        # new metadata element, grab its type
                        t = type(rc[Experiment.METADATA][k])
                    try:
                        # map Python type to dtype
                        types[k] = self.typeToDtype(t)
                    except Exception:
                        raise Exception('No type mapping for metadata {k} (type {t})'.format(k=k, t=t))
            for d in [ Experiment.PARAMETERS, Experiment.RESULTS ]:
                if self._names[d] is not None:
                    for k in self._names[d]:
                        if k in oldnames:
                            # existing field, retain it
                            types[k] = oldfields[k][0]
                        elif k in rc[d]:
                            # new field, infer its type
                            t = type(rc[d][k])
                            try:
                                # map Python type to dtype
                                types[k] = self.typeToDtype(t)
                            except Exception:
                                raise Exception('No type mapping for {k} (type {t})'.format(k=k, t=t))

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
                            self._results[k] = [0] * nr
            else:
                # no results, create the table with the correct columns
                self._results = DataFrame(columns=types.keys())

            # if we had pending results, add the new columns
            nr = len(self._pending)
            if nr > 0:
                # add new columns to each element
                for k in self._names[Experiment.PARAMETERS]:
                    if k not in self._pending:
                        self._pending[k] = [0] * nr

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
                    t = type(params[k])
                    try:
                        # map Python type to dtype
                        types[k] = self.typeToDtype(t)
                    except Exception:
                        raise Exception('No type mapping for pending result {k} (type {t})'.format(k=k, t=t))

            # add the job id column
            types[self.JOBID] = self.typeToDtype(str)

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
                        self._results[k] = [0] * nr

            # if we had pending results, add the new columns
            nr = len(self._pending)
            if nr > 0:
                # add new columns to each element
                for k in parameterNames:
                    if k not in self._pending:
                        self._pending[k] = [0] * nr
            else:
                # no pending results, create the table with the correct columns
                self._pending = DataFrame(columns=types.keys())

            # our type has changed
            self.typechanged()

        # return the dtype
        return self._pendingdtype


    # ---------- Adding results ----------

    def addSingleResult(self, rc : ResultsDict):
        '''Add a single result. This should be a single :term:`results dict`
        as returned from an instance of :class:`Experiment`, that contains metadata,
        parameters, and result.

        The results dict may add metadata, parameters, or results to the result
        set, and these will be assumed to be present from then on. Missing values
        in previously-saved results will receive default values.

        :param rc: a results dict'''

        # match the types to the passed information
        self.inferDtype(rc)

        # flatten the key/value pairs in the results dict
        # (in case of clashes, results take precedence)
        row = dict()
        for d in [ Experiment.METADATA, Experiment.PARAMETERS, Experiment.RESULTS ]:
            for k in self._names[d]:
                if k not in rc[d]:
                    row[k] = 0  
                else:
                    row[k] = rc[d][k]

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

    def cancelSinglePendingResult(self, jobid : str):
        '''Cancel the given pending result. Note that cancellation doesn't imply failure:
        it's used by :meth:`LabNotebook.resolvePendingResult` to remove the pending result
        after it's been added to the "real" results.

        :param jobid: the job id'''
        df = self._pending

        # drop the job line from the pending table
        ids = df[df[self.JOBID] == jobid].index
        if len(ids) == 0:
            # identified job doesn't exist
            raise Exception('No pending result {j}'.format(j=jobid))
        elif len(ids) != 1:
            # shouldn't be more than one either....
            raise Exception('Internal data structure failure (job {j})'.format(j=jobid))
        df.drop(index=ids, inplace=True)
        print('Dropped {j}'.format(j=jobid))

        # mark us as dirty
        self.dirty()

    def ready(self) -> bool:
        '''Test whether there are pending results.

        :returns: True if all pending results have been either resolved or cancelled'''
        return (self.numberOfPendingResults() == 0)


    # ---------- Retrieving results ----------

    def dataframe(self) -> DataFrame:
        '''Return all the available results.
        The results are returned as a `pandas` DataFrame object, which is detached
        from the results held in the result set, thereby keeping the result set
        itself immutable.

        You can pre-filter the contents of the dataframe to only include results
        for specific parameter values using :meth:`dataframeFor`.

        :returns: a dataframe of results'''
        return self._results.copy()

    def dataframeFor(self, params : Dict[str, Any]) -> DataFrame:
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

        :param params: a dict of parameters and values
        :returns: a dataframe containing results matching the parameter constraints'''

        # if we have no results, exit immediately
        if self.numberOfResults() == 0:
            return DataFrame()

        # check the validity of the parameters requested
        dps = set(params).difference(set(self.parameterNames()))
        if len(dps) > 0:
            raise Exception('Unexpected experimental parameters: {dps}'.format(dps=dps))

        # project-out the rows with these values
        df = self._results
        for k in params.keys():
            try:
                _ = iter(params[k])    # will raise an exception if applied to a singleton

                # several possible parameter values, project them all out
                df = df[df.isin(params[k]).any(1)]
            except TypeError:
                # singleton value, just capture the results that match
                df = df[df[k] == params[k]]

        # return the dataframe with the projected-out results
        return df.copy()

    def _dataframeToDict(self, df : DataFrame) -> List[ResultsDict]:
        '''Convert all the rows in a dataframe into a results dict with the correct
        structure for this result set.

        :param df: the dataframe
        :returns: a list of results dicts'''
        results = []
        for i in df.index:
            res = df.loc[i]
            rc = Experiment.resultsdict()
            for d in [ Experiment.METADATA, Experiment.PARAMETERS, Experiment.RESULTS ]:
                for k in self._names[d]:
                    rc[d][k] = res[k]
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

