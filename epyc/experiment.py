# Base class for experiments
#
# Copyright (C) 2016 Simon Dobson
# 
# Licensed under the GNU General Public Licence v.2.0
#

from datetime import datetime, timedelta


class Experiment(object):
    '''Base class for experiments conducted in a lab.

    From the developer's perspective, an experiment has five methods
    that can be overridden: configure(), deconfigure(), setUp(), do(),
    and tearDown(). configure() sets up the experiment with its parameters.
    If parameters have been set previously, deconfigure() is called first.
    do() performs the experiment, and is bracketed by calls to setUp()
    and tearDown(). The idea is that configure() is called whenever the
    parameters to the experiment are changed, while the other methods
    can be called one or more times between resets.

    From an experimenter's (or a lab's) perspective, an experiment
    has public methods set() and run(). The former sets the parameters
    for the experiment; the latter runs the experiment. producing a set
    of results that include direct experimental results and metadata on
    how the experiment ran. A single run may produce a list of result
    dicts if desired, each filled-in with the correct metadata.

    Results can be accessed by the results() method. The experiment also
    exposes an indexing interface to direct experimental results.'''

    # Top-level structure for results
    METADATA = 'metadata'                 # metadata values, mainly timing
    PARAMETERS = 'parameters'             # point in the parameter space the experiment ran on
    RESULTS = 'results'                   # results generated at that point

    # Common metadata elements reported
    START_TIME = 'start_time'             # datetime experiment started
    END_TIME = 'end_time'                 # datetime experiment ended
    ELAPSED_TIME = 'elapsed_time'         # time experiment took overall in ms
    SETUP_TIME = 'setup_time'             # time spent on setup in ms
    EXPERIMENT_TIME = 'experiment_time'   # time spent on experiment itself in ms
    TEARDOWN_TIME = 'teardown_time'       # time spent on teardown in ms
    STATUS = 'status'                     # True if experiment completed successfully
    EXCEPTION = 'exception'               # exception thrown if experiment failed

    
    def __init__( self ):
        '''Create a new experiment.'''
        self._metadata = dict()
        self._parameters = None
        self._results = None

    def setUp( self, params ):
        '''Set up the experiment. Default does nothing.

        params: the parameters of the experiment'''
        pass

    def tearDown( self ):
        '''Tear down the experiment. Default does nothing.'''
        pass

    def configure( self, params ):
        '''Configure the experiment for the given parameters.
        Default does nothing.

        params: the parameters'''
        pass

    def deconfigure( self ):
        '''De-configure the experiment prior to setting new parameters.
        Default does nothing.'''
        pass

    def set( self, params ):
        '''Set the parameters for the experiment.

        params: the parameters
        returns: the experiment'''
        if self._parameters is not None:
            self.deconfigure()
        self._parameters = params
        self.configure(params)
        return self

    def do( self, params ):
        '''Do the body of the experiment. This should be overridden
        by sub-classes.

        params: a dict of parameters for the experiment
        returns: a dict of results'''
        raise NotYetImplementedError('do()')

    def report( self, params, meta, res ):
        '''Return a dict of results. The default returns a dict with
        results keyed by self.RESULTS, the data point in the parameter space
        keyed by self.PARAMETERS, and timing and other metadata keyed
        by self.METADATA. Overriding this method can be used to record extra
        values, but be sure to call the base method as well.
 
        params: the parameters we ran under
        meta: the metadata for this run
        res: the direct experimental results from do()
        returns: a dict of extended results'''
        rc = dict()
        rc[self.PARAMETERS] = params.copy()
        rc[self.METADATA] = meta.copy()
        rc[self.RESULTS] = res
        return rc

    def run( self ):
        '''Run the experiment, using the parameters set using set().
        A "run" consists of calling setUp(), do(), and tearDown(),
        followed by collecting and storing (and returning) the
        experiment's results.

        returns: dict of reported results'''

        # perform the experiment protocol
        params = self._parameters
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
            self._metadata[self.ELAPSED_TIME] = (doneTeardownTime - startTime).total_seconds() / 1000.0
            self._metadata[self.SETUP_TIME] = (doneSetupTime - startTime).total_seconds() / 1000.0
            self._metadata[self.EXPERIMENT_TIME] = (doneExperimentTime - doneSetupTime).total_seconds() / 1000.0
            self._metadata[self.TEARDOWN_TIME] = (doneTeardownTime - doneExperimentTime).total_seconds() / 1000.0

            # set the success flag
            self._metadata[self.STATUS] = True
        except Exception as e:
            print "Caught exception in experiment: {e}".format(e = e)
            
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

        # report the results
        self._results = res
        return self.report(self.parameters(),
                           self.metadata(),
                           res)
    
    def __getitem__( self, k ):
        '''Return the given element of the experimental results. This only
        gives access to direct experimental results, not to parameters
        or metadata.

        k: the result key
        returns: the value'''
        if self._results is None:
            raise Exception("No results set")
        else:
            return (self.experimentalResults())[k]
    
    def success( self ):
        '''Test whether the experiment has been run successfully. This will
        be False if the experiment hasn't been run, or if it's been run and
        failed (in which case the exception will be stored in the metadata).

        returns: True if the experiment has been run successfully'''
        if self.STATUS in self.metadata().keys():
            return (self.metadata())[self.STATUS]
        else:
            return False

    def results( self ):
        '''Return a complete results dict. Only really makes sense for
        recently-executed experimental runs.

        return: the results dict'''
        return self.report(self.parameters(),
                           self.metadata(),
                           self.experimentalResults())

    def experimentalResults( self ):
        '''Return the experimental results from our last run. This will
        be None if we haven't been run, or if we ran and failed.

        return: the experimental results or None'''
        return self._results
    
    def parameters( self ):
        '''Return the current experimental parameters, which will
        be None if none have been given by a call to set()

        returns: the parameters,'''
        return self._parameters

    def metadata( self ):
        '''Return the metadata we collected at out last execution, which
        will be None if we've not been executed and an empty dict if
        we're mid-run (i.e., if this method is called from do() for
        whatever reason).

        returns: the metadata'''
        return self._metadata
    
    
        
    
