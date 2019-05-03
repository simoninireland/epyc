# Simulation "lab" experiment management, parallel cluster version
#
# Copyright (C) 2016--2019 Simon Dobson
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

from __future__ import print_function
import future
from builtins import range

import epyc

import numpy
import pickle
import dill
import time

from ipyparallel import Client, RemoteError


class ClusterLab(epyc.Lab):
    """A :class:`Lab` running on an ``pyparallel`` compute
    cluster.

    Experiments are submitted to engines in the cluster for
    execution in parallel, with the experiments being performed
    asynchronously to allow for disconnection and subsequent retrieval
    of results. Combined with a persistent :class:`LabNotebook`, this allows
    for fully decoupled access to an on-going computational experiment
    with piecewise retrieval of results.

    This class requires a cluster to already be set up and running, configured
    for persistent access, with access to the necessary code and libraries,
    and with appropriate security information available to the client.
    """

    # Tuning parameters
    WaitingTime = 30           #: Waiting time for checking for job completion. Lower values increase network traffic.

    
    def __init__( self, notebook = None, url_file = None, profile = None, profile_dir = None, ipython_dir = None, context = None, debug = False, sshserver = None, sshkey = None, password = None, paramiko = None, timeout = 10, cluster_id = None, use_dill = False, **extra_args ):
        """Create an empty lab attached to the given cluster. Most of the arguments
        are as expected by the ``pyparallel.Client`` class, and are used to create the
        underlying connection to the cluster. The connection is opened immediately,
        meaning the cluster must be up and accessible when creating a lab to use it.

        :param notebook: the notebook used to results (defaults to an empty :class:`LabNotebook`)
        :param url_file: file containing connection information for accessing cluster
        :param profile: name of the IPython profile to use
        :param profile_dir: directory containing the profile's connection information
        :param ipython_dir: directory containing profile directories
        :param context: ZMQ context
        :param debug: whether to issue debugging information (defaults to False)
        :param sshserver: username and machine for ssh connections
        :param sshkey: file containing ssh key
        :param password: ssh password
        :param paramiko: True to use paramiko for ssh (defaults to False)
        :param timeout: timeout in seconds for ssh connection (defaults to 10s)
        :param cluster_id: string added to runtime files to prevent collisions
        :param use_dill: whether to use Dill as pickler (defaults to False)"""
        super(epyc.ClusterLab, self).__init__(notebook)
        
        # record all the connection arguments for later
        self._arguments = dict(url_file = url_file,
                               profile = profile,
                               profile_dir = profile_dir,
                               ipython_dir = ipython_dir,
                               context = context,
                               debug = debug,
                               sshserver = sshserver,
                               sshkey = sshkey,
                               password = password,
                               paramiko = paramiko,
                               timeout = timeout,
                               cluster_id = cluster_id,
                               use_dill = use_dill,
                               **extra_args)
        self._client = None

        # connect to the cluster
        self.open()

        # use Dill if requested
        if use_dill:
            self.use_dill()


    # ---------- Protocol ----------

    def open( self ):
        """Connect to the cluster."""
        if self._client is None:
            self._client = Client(**self._arguments)
        
    def close( self ):
        """Close down the connection to the cluster."""
        if self._client is not None:
            self._client.close()
            self._client = None

    def recreate(self):
        '''Save the arguments needed to re-connect to the cluster we use.

        :returns: a (classname, args) pair'''
        (cn, args) = super(ClusterLab, self).recreate()
        nargs = args.copy()
        nargs.update(self._arguments)
        return  (classname, nargs)


    # ---------- Remote control of the compute engines ----------

    def numberOfEngines( self ):
        """Return the number of engines available to this lab.

        :returns: the number of engines"""
        return len(self.engines())

    def engines( self ):
        """Return a list of the available engines.

        :returns: a list of engines"""
        self.open()
        return self._client[:]

    def use_dill( self ):
        """Make the cluster use Dill as pickler for transferring results. This isn't
        generally needed, but is sometimes useful for particularly complex experiments
        such as those involving closures. (Or, to put it another way, if you find yourself
        tempted to use this method, consider re-structuring your experiment code.)"""
        self.open()
        with self.sync_imports(quiet = True):
            import dill
        self._client.direct_view().use_dill()

    def sync_imports( self, quiet = False ):
        """Return a context manager to control imports onto all the engines
        in the underlying cluster. This method is used within a ``with`` statement.

        Any imports should be done with no experiments running, otherwise the
        method will block until the cluster is quiet. Generally imports will be one
        of the first things done when connecting to a cluster. (But be careful
        not to accidentally try to re-import if re-connecting to a running
        cluster.)

        :param quiet: if True, suppresses messages (defaults to False)
        :returns: a context manager"""
        self.open()
        return self._client[:].sync_imports(quiet = quiet)


    # ---------- Running experiments ----------

    def _mixup( self, ps ):
        """Private method to mix up a list of values in-place using a Fisher-Yates
        shuffle (see https://en.wikipedia.org/wiki/Fisher-Yates_shuffle).

        :param ps: the array
        :returns: the array, shuffled in-place"""
        for i in range(len(ps) - 1, 0, -1):
            j = int(numpy.random.random() * i)
            temp = ps[i]
            ps[i] = ps[j]
            ps[j] = temp
        return ps
     
    def runExperiment( self, e ):
        """Run the experiment across the parameter space in parallel using
        all the engines in the cluster. This method returns immediately.

        The experiments are run asynchronously, with the points in the parameter
        space being explored randomly so that intermediate retrievals of results
        are more representative of the overall result. Put another way, for a lot
        of experiments the results available will converge towards a final
        answer, so we can plot them and see the answer emerge.

        :param e: the experiment"""

        # create the parameter space
        space = self.parameterSpace()

        # only proceed if there's work to do
        if len(space) > 0:
            nb = self.notebook()
            
            # randomise the order of the parameter space so that we evaluate across
            # the space as we go along to try to make intermediate (incomplete) result
            # sets more representative of the overall result set
            ps = self._mixup(space)

            try:
                # connect to the cluster
                self.open()

                # submit an experiment at each point in the parameter space to the cluster
                view = self._client.load_balanced_view()
                jobs = []
                for p in ps:
                    jobs.extend((view.apply_async((lambda p: e.set(p).run()), p)).msg_ids)

                    # there seems to be a race condition in submitting jobs,
                    # whereby jobs get dropped if they're submitted too quickly
                    time.sleep(0.01)
                
                # record the mesage ids of all the jobs as submitted but not yet completed
                psjs = zip(ps, jobs)
                for (p, j) in psjs:
                    nb.addPendingResult(p, j)
            finally:
                # commit our pending results in the notebook
                nb.commit()
                self.close()

    def updateResults( self ):
        """Update our results within any pending results that have completed since we
        last retrieved results from the cluster.

        :returns: the number of pending results completed at this call"""

        # we do all the tests for pending results against the notebook directly,
        # as the corresponding methods on self call this method themselves
        nb = self.notebook()

        # look for pending results if we're waiting for any
        n = 0
        if nb.numberOfPendingResults() > 0:
            # we have results to get
            self.open()
            for j in set(nb.pendingResults()):
                # query the status of a job
                status = self._client.result_status(j, status_only = False)
                    
                # add all completed jobs to the notebook
                if j in status['completed']:
                    r = status[j]
                        
                    # update the result in the notebook, cancelling
                    # the pending result as well
                    # values come back from Client.result_status() in
                    # varying degrees of list-nesting, which LabNotebook.addResult()
                    # handles itself
                    nb.addResult(r, j)

                    # commit changes to the notebook
                    nb.commit()

                    # purge the completed job from the cluster
                    self._client.purge_hub_results(j)
                         
                    # record that we retrieved the results for the given job
                    n = n + 1
        return n


    # ---------- Accessing results ----------

    def numberOfResults( self ):
        """Return the number of results we have available at the moment.

        :returns: the number of results"""
        self.updateResults()
        return self.notebook().numberOfResults()

    def numberOfPendingResults( self ):
        """Return the number of resultswe are waiting for.

        :returns: the number of pending results"""
        self.updateResults()
        return self.notebook().numberOfPendingResults()
    
    def _availableResultsFraction( self ):
        """Private method to return the fraction of results available, as a real number
        between 0 and 1. This does not update the results fetched from the cluster.

        :returns: the fraction of available results"""
        tr = self.notebook().numberOfResults() + self.notebook().numberOfPendingResults()
        if tr == 0:
            return 0
        else:
            return (self.notebook().numberOfResults() + 0.0) / tr
    
    def readyFraction( self ):
        """Test what fraction of results are available. This will change over
        time as the results come in.

        :returns: the fraction from 0 to 1"""
        self.updateResults()
        return self._availableResultsFraction()
    
    def ready( self ):
        """Test whether all the results are available. This will change over
        time as the results come in.

        :returns: True if all the results are available"""
        return (self.readyFraction() == 1)

    def wait( self, timeout = -1 ):
        """Wait for all pending results to be finished. If timeout is set,
        return after this many seconds regardless.

        :param timeout: timeout period in seconds (defaults to forever)
        :returns: True if all the results completed"""

        # we can't use pyparallel.Client.wait() for this, because that
        # method only works for cases where the Client object is the one that
        # submitted the jobs to the cluster hub -- and therefore has the
        # necessary data structures to perform synchronisation. This isn't the
        # case for us, as one of the main goals of epyc is to support disconnected
        # operation, which implies a different Client object retrieving results
        # than the one that submitted the jobs in the first place. This is
        # unfortunate, but understandable given the typical use cases for
        # Client objects in pyparallel.
        #
        # Instead. we have to code around a little busily. The ClusterLab.WaitingTime
        # global sets the latency for waiting, and we repeatedly wait for this amount
        # of time before updating the results. The latency value essentially controls
        # how busy this process is: given that most simulations are expected to
        # be long, a latency in the tens of seconds feels about right as a default
        if self.numberOfPendingResults() > 0:
            # we've got pending results, wait for them
            timeWaited = 0
            while (timeout < 0) or (timeWaited < timeout):
                if self.numberOfPendingResults() == 0:
                    # no pending jobs left, we're complete
                    return True
                else:
                    # not done yet, calculate the waiting period
                    if timeout == -1:
                        # wait for the default waiting period
                        dt = self.WaitingTime
                    else:
                        # wait for the default waiting period or until the end of the timeout.
                        # whichever comes first
                        if (timeout - timeWaited) < self.WaitingTime:
                            dt = timeout - timeWaited
                        else:
                            dt = self.WaitingTime
                            
                    # sleep for a while
                    time.sleep(dt)
                    timeWaited = timeWaited + dt

            # if we get here, the timeout expired, so do a final check
            # and then exit
            return (self.numberOfPendingResults() == 0)

        else:
            # no results, so we got them all
            return True


    # ---------- Managing pending results ----------

    def pendingResults( self ):
        """Return the list of job iods for any pending results.

        :returns: a list of job ids"""
        return self.notebook().pendingResults()
    
    def pendingResultsFor( self, params ):
        """Return a list of job ids for any results pending for experiments
        at the given point in the parameter space.

        :param params: the experimental parameters
        :returns: a list of job ids"""
        return self.notebook().pendingResultsFor(params)
    
    def _abortJobs( self, js ):
        """Private method to abort a set of jobs.

        :param js: the job ids to be aborted"""
        self.open()
        self._client.abort(jobs = js)
        self.close()
        
    def cancelPendingResultsFor( self, params ):
        """Cancel any results pending for experiments at the given point
        in the parameter space.

        :param params: the experimental parameters"""
        
        # grab the result job ids
        jobs = self.pendingResultsFor(params)
        
        if len(jobs) > 0:
            # abort in the cluster
            self._abortJobs(jobs)
            
            # cancel in the notebook                  
            self.notebook().cancelPendingResultsFor(params)
        
    def cancelAllPendingResults( self ):
        """Cancel all pending results."""

        # grab all the pending job ids
        jobs = self.pendingResults()
        
        if len(jobs) > 0:
            # abort in the cluster
            self._abortJobs(jobs)
            
            # cancel in the notebook                  
            self.notebook().cancelAllPendingResults()
       
