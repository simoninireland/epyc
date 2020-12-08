# Simulation "lab" experiment management, parallel cluster version
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

from epyc import Lab, LabNotebook, Experiment
import numpy                                  # type: ignore
import time
import sys
from ipyparallel import Client, DirectView    # type: ignore
from contextlib import AbstractContextManager

class ClusterLab(Lab):
    """A :class:`Lab` running on an ``pyparallel`` compute cluster.

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
    WaitingTime : int = 30           #: Waiting time for checking for job completion. Lower values increase network traffic.
    Reconnections : int = 5          #: Number of attempts when re-connecting to a cluster.
    Retries : int = 3                #: Number of re-tries for failed jobs.
    
    def __init__( self, notebook : LabNotebook = None, url_file = None, profile = None, profile_dir = None, ipython_dir = None, context = None, debug = False, sshserver = None, sshkey = None, password = None, paramiko = None, timeout = 10, cluster_id = None, **extra_args ):
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
        :param cluster_id: string added to runtime files to prevent collisions"""
        super(ClusterLab, self).__init__(notebook)
        
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
                               **extra_args)
        self._client : Client = None

        # connect to the cluster
        self.open()

        # use the more sophisticated pickler
        rc = self._client[:].use_cloudpickle()


    # ---------- Protocol ----------

    def connect(self):
        '''Low-level connection to the cluster. Most code should
        use :meth:`open` to open the connection: this method
        performs a single connection attempt, raising an exception if it
        fails.'''
        if self._client is None:
            self._client = Client(**self._arguments)

            # if we get here, activate the connection
            self.activate()

    def activate(self):
        '''Make the connection active to ipyparallel/Jupyter. Usually
        only needed when there are several labs active in one program,
        where this method selects the lab used by, fo example, parallel magics.'''
        if self._client is None:
            raise Exception('No open connection to activate')
        else:
            self._client.direct_view().activate()

    def open(self):
        """Connect to the cluster. This will involve several possible re-tries."""
        try:
            # first try
            if self._client is None:
                # no open connection, try to connect
                self.connect()
            else:
                # we have an open connection, activate it
                self.activate()
        except Exception as exc:
            # if we get here, we're definitely disconnected, so try
            # to re-connect the requisite number of times
            for i in range(self.Reconnections):
                print('Connection to cluster failed, reconnecting ({i}/{n})'.format(i=i + 1, n=self.Reconnections), file=sys.stderr)
                try:
                    # try to connect
                    self.connect()

                    # if we get here, we succeeded
                    return
                except Exception as e:
                    # go round the loop again, saving the exception in
                    # case we're the last try
                    exc = e
            
            # OK, we've failed enough, stop punching the brick wall...
            raise exc

    def close( self ):
        """Close down the connection to the cluster."""
        if self._client is not None:
            self._client.close()
            self._client = None

    def recreate(self):
        '''Save the arguments needed to re-connect to the cluster we use.

        :returns: a (classname, args) pair'''
        (_, args) = super(ClusterLab, self).recreate()
        n = '{modulename}.{classname}'.format(modulename = self.__class__.__module__,
                                              classname = self.__class__.__name__)
        nargs = args.copy()
        nargs.update(self._arguments)
        return (n, nargs)


    # ---------- Remote control of the compute engines ----------

    def numberOfEngines(self) -> int:
        """Return the number of engines available to this lab.

        :returns: the number of engines"""
        return len(self.engines())

    def engines(self) -> DirectView:
        """Return a list of the available engines.

        :returns: a list of engines"""
        self.open()
        return self._client[:]

    def sync_imports(self, quiet : bool =False) -> AbstractContextManager:
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
        return self._client[:].sync_imports(quiet=quiet)


    # ---------- Running experiments ----------

    def runExperiment(self, e : Experiment):
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
            ps = space.copy()
            numpy.random.shuffle(ps)

            try:
                # connect to the cluster
                self.open()

                # configure a load balanced view of the cluster
                view = self._client.load_balanced_view()
                view.set_flags(retries=self.Retries)

                # submit an experiment at each point in the parameter space to the cluster
                jobs = []
                for p in ps:
                    rc = view.apply_async(lambda ep: ep[0].set(ep[1]).run(), (e, p))
                    ids = rc.msg_ids
                    #print('Started {ids}'.format(ids=ids))
                    jobs.extend(ids)

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

    def updateResults(self, purge : bool =False) -> int:
        """Update our results within any pending results that have completed since we
        last retrieved results from the cluster. Optionally purges any jobs that
        have crashed, which can be due to engine failure within the
        cluster. This prevents individual crashes blocking the retrieval of other jobs.

        :param purge: (optional) cancel any jobs that have crashed (defaults to False)
        :returns: the number of pending results completed at this call"""
        nb = self.notebook()

        # look for pending results if we're waiting for any
        n = 0
        if not nb.ready():
            # we have results to get
            try:
                crashed = []
                self.open()
                for j in set(nb.allPendingResults()):
                    try:
                        # query the status of a job
                        #print('Test status of {j}'.format(j=j))
                        status = self._client.result_status(j, status_only=False)
                    
                        # add all completed jobs to the notebook
                        if j in status['completed']:
                            r = status[j]
                            #print('{j} completed'.format(j=j))

                            # resolve the result in the appropriate result set
                            nb.resolvePendingResult(r, j)

                            # record that we retrieved the results for the given job
                            n = n + 1
                    
                            # purge the completed job from the cluster
                            self._client.purge_hub_results(j)        
                    except Exception as e:
                        # report the exception and carry on, recording the job as crashed
                        print(e, file=sys.stderr)
                        crashed.append(j)

                # purge any crashed jobs if requested
                if purge and len(crashed) > 0:
                    for j in crashed:
                        nb.cancelPendingResult(j)
                        self._client.purge_hub_results(j)    
            finally:
                # commit changes to the notebook and close the connection
                nb.commit()
                self.close()

        return n


    # ---------- Accessing results ----------
    
    def wait(self, timeout : int =-1) -> bool:
        """Wait for all pending results in all result sets to be finished. If timeout is set,
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
        nb = self.notebook()
        if nb.numberOfAllPendingResults() > 0:
            # we've got pending results, wait for them
            timeWaited = 0
            while (timeout < 0) or (timeWaited < timeout):
                self.updateResults()
                if nb.numberOfAllPendingResults() == 0:
                    # no pending results left, we're complete
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
            return (nb.numberOfAllPendingResults() == 0)

        else:
            # no results, so we got them all
            return True

       
