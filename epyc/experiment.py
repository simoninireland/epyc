# Base class for experiments
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

from __future__ import print_function
from datetime import datetime, timedelta
import sys
import traceback

class Experiment(object):
    """Base class for an :term:`experiment` conducted in a :term:`lab`.

    An :class:`Experiment` defines a computational experiment that can be run
    independently or (more usually) controlled from an instamnce of the
    :class:`Lab` class. Experiments should be long-lasting, able to conduct
    repeated runs at several different parameter points.

    From an experimenter's (or a lab's) perspective, an experiment
    has public methods :meth:`set` and :meth:`run`. The former sets the parameters
    for the experiment; the latter runs the experiment. producing a set
    of results that include direct experimental results and metadata on
    how the experiment ran. A single run may produce a list of result
    dicts if desired, each filled-in with the correct metadata.

    Experimental results, parameters, and metadata can be access directly
    from the :class:`Experiment` object. The class also exposes
    an indexing interface to access experimental results by name.
    """

    # Top-level structure for results
    METADATA = 'metadata'                 #: Results dict key for metadata values, mainly timing
    PARAMETERS = 'parameters'             #: Results dict key for describing the point in the parameter space the experiment ran on
    RESULTS = 'results'                   #: Results dict key for the experimental results generated at the experiment's parameter point

    # Common metadata elements reported
    START_TIME = 'start_time'             #: Metadata element for the datetime experiment started
    END_TIME = 'end_time'                 #: Metadata element for the datetime experiment ended
    ELAPSED_TIME = 'elapsed_time'         #: Metadata element for the time experiment took overall in seconds
    SETUP_TIME = 'setup_time'             #: Metadata element for the time spent on setup in seconds
    EXPERIMENT_TIME = 'experiment_time'   #: Metadata element for the time spent on experiment itself in seconds
    TEARDOWN_TIME = 'teardown_time'       #: Metadata element for the time spent on teardown in seconds
    STATUS = 'status'                     #: Metadata element that will be True if experiment completed successfully, False otherwise
    EXCEPTION = 'exception'               #: Metadata element containing the exception thrown if experiment failed
    TRACEBACK = 'traceback'               #: Metadata element containing the traceback from the exception (as a string)

    
    def __init__( self ):
        """Create a new experiment."""
        self._metadata = dict()
        self._parameters = None
        self._results = None


    # ---------- Configuration ----------

    def set(self, params):
        """Set the parameters for the experiment, returning the
        now-configured experiment. Be sure to call this base method when overriding.

        :param params: the parameters
        :returns: the experiment"""
        if self._parameters is not None:
            self.deconfigure()
        self.configure(params)
        return self

    def configure( self, params ):
        """Configure the experiment for the given parameters.
        The default stores the parameters for later use. Be sure
        to call this base method when overriding.

        :param params: the parameters"""
        self._parameters = params

    def deconfigure( self ):
        """De-configure the experiment prior to setting new parameters.
        Default removes the parameters. Default does nothing."""
        self._parameters = None


    # ---------- Running the experiment ----------

    def setUp( self, params ):
        """Set up the experiment. Default does nothing.

        :param params: the parameters of the experiment"""
        pass

    def tearDown( self ):
        """Tear down the experiment. Default does nothing."""
        pass

    def do( self, params ):
        """Do the body of the experiment. This should be overridden
        by sub-classes.

        params: a dict of parameters for the experiment
        returns: a dict of experimental results"""
        raise NotImplementedError('do()')

    def report( self, params, meta, res ):
        """Return a properly-structured dict of results. The default returns a dict with
        results keyed by :attr:`Experiment.RESULTS`, the data point in the parameter space
        keyed by :attr:`Experiment.PARAMETERS`, and timing and other metadata keyed
        by :attr:`Experiment.METADATA`. Overriding this method can be used to record extra
        metadata values, but be sure to call the base method as well.

        :param params: the parameters we ran under
        :param meta: the metadata for this run
        :param res: the direct experimental results from do()
        :returns: a :term:`results dict`"""
        rc = dict()
        rc[self.PARAMETERS] = params.copy()
        rc[self.METADATA] = meta.copy()
        rc[self.RESULTS] = res
        return rc

    def run( self ):
        """Run the experiment, using the parameters set using :meth:`set`.
        A "run" consists of calling :meth:`setUp`, :meth:`do`, and :meth:`tearDown`,
        followed by collecting and storing (and returning) the
        experiment's results. If running the experiment raises an
        exception, that will be returned in the metadata along with
        its traceback to help with experiment debugging.

        :returns: a :term:`results dict`"""
        
        # perform the experiment protocol
        params = self.parameters()
        self._metadata = dict()
        self._results = None
        res = None
        doneSetupTime = doneExperimentTime = doneTeardownTime = None
        try:
            # do the phases in order, recording the wallclock times at each phase
            startTime = datetime.now()
            self.setUp(params)
            doneSetupTime = datetime.now()
            res = self.do(params)
            doneExperimentTime = datetime.now() 
            self.tearDown()
            doneTeardownTime = datetime.now() 
            
            # record the various timings
            self._metadata[self.START_TIME] = startTime
            self._metadata[self.END_TIME] = doneTeardownTime
            self._metadata[self.ELAPSED_TIME] = (doneTeardownTime - startTime).total_seconds()
            self._metadata[self.SETUP_TIME] = (doneSetupTime - startTime).total_seconds()
            self._metadata[self.EXPERIMENT_TIME] = (doneExperimentTime - doneSetupTime).total_seconds()
            self._metadata[self.TEARDOWN_TIME] = (doneTeardownTime - doneExperimentTime).total_seconds()
            
            # set the success flag
            self._metadata[self.STATUS] = True
        except Exception as e:
            print("Caught exception in experiment: {e}".format(e = e))

            # grab the traceback before we do anything else
            #_, _, tb = sys.exc_info()
            tb = traceback.format_exc()
            
            # decide on the cleanup actions that need doing
            if (doneSetupTime is not None) and (doneExperimentTime is None):
                # we did the setup and then failed in the experiment, so
                # we need to do the teardown
                try:
                    self.tearDown()
                except:
                    pass
                
            # set the failure flag and record the exception
            # (there will be no timing information recorded)
            self._metadata[self.STATUS] = False
            self._metadata[self.EXCEPTION] = e
            self._metadata[self.TRACEBACK] = tb
                
        # report the results
        self._results = res
        return self.report(params,
                           self._metadata,
                           res)


    # ---------- Accessing results ----------

    def __getitem__( self, k ):
        """Return the given element of the experimental results. This only
        gives access to the experimental results, *not* to the parameters
        or metadata.

        :param k: the result key
        :returns: the value
        :raises: KeyError if there is no such result"""
        if self._results is None:
            raise KeyError(k)
        else:
            return (self.experimentalResults())[k]
    
    def success( self ):
        """Test whether the experiment has been run successfully. This will
        be False if the experiment hasn't been run, or if it's been run and
        failed.

        :returns: ``True`` if the experiment has been run successfully"""
        if self.STATUS in self.metadata().keys():
            return (self.metadata())[self.STATUS]
        else:
            return False

    def failed(self):
        '''Test whether an experiment failed. This will be True if the experiment has
        been run and has failed, which means that there will be an exception and traceback
        information stored in the metadata.

        :returns: ``True`` if the experiment has failed'''
        if self.STATUS not in self.metadata().keys():
            return False
        else:
            return not (self.metadata())[self.STATUS]

    def results( self ):
        """Return a complete results dict. Only really makes sense for
        recently-executed experimental runs.

        :returns: the results dict"""
        return self.report(self.parameters(),
                           self.metadata(),
                           self.experimentalResults())

    def experimentalResults( self ):
        """Return the experimental results from our last run. This will
        be None if we haven't been run, or if we ran and failed.

        :returns: the experimental results or ``None``"""
        return self._results
    
    def parameters( self ):
        """Return the current experimental parameters, which will
        be None if none have been given by a call to set()

        :returns: the parameters,"""
        return self._parameters

    def metadata( self ):
        """Return the metadata we collected at out last execution, which
        will be None if we've not been executed and an empty dict if
        we're mid-run (i.e., if this method is called from do() for
        whatever reason).

        :returns: the metadata"""
        return self._metadata
    
    
        
    
