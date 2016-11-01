# Simulation "lab notebook" for collecting results, in-memory version
#
# Copyright (C) 2016 Simon Dobson
# 
# Licensed under the GNU General Public Licence v.2.0
#

from epyc import *
from pandas import DataFrame


class LabNotebook(object):
    '''A "laboratory notebook" recording the results of a set of
    experiments conducted across a parameter space. The intention is
    to record both results and all the metadata necessary to
    re-conduct the experiment.

    A notebook maps points in a parameter space to a set of results. There
    may be multiple results mapped to the same point, to allow for
    repetition of experiments: the notbook can re-cquire all, or only the
    most recent, results for a given parameter point.

    Notebooks are immutable: once entered, a result can't be deleted
    or changed.

    Notebooks support "pending" results, llowing us to record experiments
    in progress. A pending result can be finalised by providing it with a
    value, or can be deleted.

    Notebooks support both len() and iterator access, both referring to their
    complete results.'''

    def __init__( self, name = None, description = None ):
        '''Create an empty notebook.

        :param name: the notebook's name
        :param description: a free text description'''
        self._name = name
        self._description = description
        self._results = dict()
        self._pending = dict()

    def name( self ):
        '''Return the name of the notebook. If the notebook is persistent,
        this likely relates to its storage in some way (for example a
        file name).

        :returns: the notebook name'''
        return self._name

    def description( self ):
        '''Return the free text description of the notebook.

        :returns: the notebook description'''
        return self._description

    def isPersistent( self ):
        '''By default notebooks are not persistent.

        :returns: False'''
        return False

    def commit( self ):
        '''Commit to persistent form. By default does nothing. This should
        be called periodically to save intermediate results: it may happen
        automatically in some sub-classes, depending on their implementation.'''
        pass
    
    def _parametersAsIndex( self, ps ):
        '''Private method to turn a parameter dict into a string suitable for
        keying a dict.

        ps: the parameters as a hash
        returns: a string key'''
        k = ""
        for p in sorted(ps.keys()):       # normalise the parameters
            v = ps[p]
            k = k + "{p}=[[{v}]];".format(p = p, v = v)
        return k

    def _flatten( self, es ):
        '''Private method to flatten an arbitrarily nested list structure
        (including a non-list) into a single flat list.

        es: the list (or not)
        returns: a flat list of elemnents'''
        if isinstance(es, list):
            if len(es) == 0:
                return [ ]
            else:
                return self._flatten(es[0]) + self._flatten(es[1:])
        else:
            return [ es ]
        
    def addResult( self, results, jobids = None ):
        '''Add a result. This should be :term:`results dict` as returned from
        an instance of :class:`Experiment`, that contains metadata,
        parameters, and result. Results cannot be overridden, as
        notebooks are immutable: adding more results simply adds
        another result set.

        If results is a list of result dicts, they are added in order: the last result in
        the list is assumed to be the latest. The result dicts can be embedded in any depth
        of list structure: they're flattened and added in order, left to right.

        If the jobid is present, this result resolves the corresponding pending result.
        As with result, jobid can be a list. (The two lists need not be the same
        length, to allow for experiments that return lists of result dicts.)

        :param result: the results (or a list of results)
        :param jobid: the pending result job id(s) (defaults to no jobs)
        '''

        # add each result
        for result in self._flatten(results):
            k = self._parametersAsIndex(result[Experiment.PARAMETERS])
            
            # retrieve or create the result list
            if k in self._results.keys():
                rs = self._results[k]
            else:
                rs = []
                self._results[k] = rs

            # store the result
            rs.insert(0, result)

        # if there is are job ids provided, cancel the corresponding pending jobs
        if jobids is not None:
            for jobid in self._flatten(jobids):
                if jobid in self._pending.keys():
                    # grab the results list for which this is a pending job
                    k = self._pending[jobid]
                    if k in self._results.keys():
                        # delete job id from current results
                        rs = self._results[k]
                        j = rs.index(jobid)
                        del rs[j]
                    
                        # ...and from the set of pending results
                        del self._pending[jobid]
                    else:
                        # we've screwed-up the internal data structures
                        raise RuntimeError('Internal structure error for {j} -> {ps}'.format(j = jobid,
                                                                                             ps = k))
                else:
                    # we've screwed-up the internal data structures
                    raise RuntimeError('Internal structure error for {j} -> {ps}'.format(j = jobid,
                                                                                         ps = k))
        
    def addPendingResult( self, ps, jobid ):
        '''Add a "pending" result that we expect to get results for.

        :param ps: the parameters for the result
        :param jobid: an identifier for the pending result'''
        k = self._parametersAsIndex(ps)

        # retrieve or create the result list
        if k in self._results.keys():
            rs = self._results[k]
        else:
            rs = []
            self._results[k] = rs

        # append the pending result's jobid
        rs.insert(0, jobid)

        # map job id to parameters to which it refers
        self._pending[jobid] = k

    def cancelPendingResult( self, jobid ):
        '''Cancel a particular pending result. Note that this only affects the
        notebook's record, not any job running in a lab.

        :param jobid: job id for pending result'''
        if jobid in self._pending.keys():
            k = self._pending[jobid]
            del self._pending[jobid]
            if k in self._results.keys():
                rs = self._results[k]
                j = rs.index(jobid)
                del rs[j]
            else:
                # we've screwed-up the internal data structures
                raise RuntimeError('Internal structure error for {j} -> {ps}'.format(j = jobid,
                                                                                     ps = k))
        else:
            # no such job
            # sd: should this just fail silently?
            raise KeyError('No pending result with id {j}'.format(j = jobid))
        
    def pendingResultsFor( self, ps ):
        '''Retrieve a list of all pending results associated with the given parameters.

        :param ps: the parameters
        :returns: a list of pending result job ids, which may be empty'''
        k = self._parametersAsIndex(ps)
        if k in self._results.keys():
            # filter out pending job ids, which can be anything except dicts
            return [ j for j in self._results[k] if not isinstance(j, dict) ]
        else:
            return []
                
    def cancelPendingResultsFor( self, ps ):
        '''Cancel all pending results for the given parameters. Note that
        this only affects the notebook's record, not any job running in a lab.

        :param ps: the parameters'''
        k = self._parametersAsIndex(ps)

        if k in self._results.keys():
            # remove from results
            rs = self._results[k]
            js = [ j for j in rs if not isinstance(j, dict) ]
            self._results[k] = [ rc for rc in rs if isinstance(rc, dict) ]

            # ...and from pending jobs list
            for j in js:
                del self._pending[j]

    def cancelAllPendingResults( self ):
        '''Cancel all pending results. Note that this only affects the
        notebook's record, not any job running in a lab.'''
        for k in self._results.keys():
            rs = self._results[k]
            self._results[k] = [ j for j in rs if isinstance(j, dict) ]
        self._pending = dict()

    def pendingResults( self ):
        '''Return the job ids of all pending results.

        returns: a list of job ids, which may be empty'''
        return self._pending.keys()
        
    def resultsFor( self, ps ):
        '''Retrieve a list of all results associated with the given parameters.

        :param ps: the parameters
        :returns: a list of results, which may be empty'''
        k = self._parametersAsIndex(ps)
        if k in self._results.keys():
            # filter out pending job ids, which can be anything except dicts
            return [ res for res in self._results[k] if isinstance(res, dict) ]
        else:
            return []

    def latestResultsFor( self, ps ):
        '''Retrieve only the latest result for the given parameters.

        :param ps: the parameters
        :returns: a single result, or None if there are none'''
        rs = self.resultsFor(ps)
        if rs is None:
            return None
        else:
            if len(rs) == 0:
                return None
            else:
                return rs[0]
        
    def results( self ):
        '''Return a list of all the results currently available. This
        excludes pending results. Results are returned as a single flat
        list, so any repetition structure is lost.

        :returns: a list of results'''
        rs = []
        for k in self._results.keys():
            # filter out pending job ids, which can be anything except dicts
            ars = [ res for res in self._results[k] if isinstance(res, dict) ]
            rs.extend(ars)
        return rs

    def numberOfResults( self ):
        '''Return the number of results we have.

        returns: number of results available'''
        return len(self.results())

    def numberOfPendingResults( self ):
        '''Return ther number of addiitonal results we expect.

        returns: number of pending results'''
        return len(self.pendingResults())
    
    def __len__( self ):
        '''The length of a notebook is the number of results it currently
        has available. A synonym for numberOfResults().

        :returns: the number of results available'''
        return self.numberOfResults()
    
    def __iter__( self ):
        '''Return an iterator over the results available.

        :returns: an iteration over the results'''
        return self.results().__iter__()
    
    def dataframe( self, only_successful = True ):
        '''Return the results as a pandas DataFrame. Note that there is a danger
        of duplicate labels here, for example if the results contain a value
        with the same name as one of the parameters. To resolve this, parameter names
        take precedence over metadata values, and result names take precedence over
        parameter names.
 
        If the only_successful flag is set (the default), then the DataFrame will
        only include results that completed without an exception; if it is set to
        False, the DataFrame will include all results and also the exception details.

        :param only_successful: include only successful experiments (defaults to True)
        :returns: the parameters, results, and metadata in a DataFrame'''

        def extract( r ):
            if r[Experiment.METADATA][Experiment.STATUS]:
                # experiment was a success, include it
                rd = r[Experiment.METADATA].copy()
                rd.update(r[Experiment.PARAMETERS])
                rd.update(r[Experiment.RESULTS])
            else:
                # experiment returned an exception
                if not only_successful:
                    # ...but we want it anyway
                    rd = r[Experiment.METADATA].copy()
                    rd.update(r[Experiment.PARAMETERS])
            
                    # ...and there are no results to add
                else:
                    rd = None
            return rd

        records = [ r for r in map(extract, self.results()) if r is not None ]
        return DataFrame.from_records(records)
    
