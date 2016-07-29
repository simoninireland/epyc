# Base class for experiments
#
# Copyright (C) 2016 Simon Dobson
# 
# Licensed under the GNU General Public Licence v.2.0
#

import time


class Experiment:
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
    how the experiment ran.

    Results can be accessed by the results() method. The experiment also
    exposes an indexing interface to direct experimental results.'''

    # Top-level structure for results
    METADATA = 'metadata'                 # metadata values, mainly timing
    PARAMETERS = 'parameters'             # point in the parameter space the experiment ran on
    RESULTS = 'results'                   # results generated at that point

    # Common metadata elements reported
    START_TIME = 'start_time'             # experiment started
    END_TIME = 'end_time'                 # experiment ended
    ELAPSED_TIME = 'elapsed_time'         # time experiment took overall
    SETUP_TIME = 'setup_time'             # time spent on setup
    EXPERIMENT_TIME = 'experiment_time'   # time spent on experiment itself
    TEARDOWN_TIME = 'teardown_time'       # time spent on teardown
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

    def report( self, res ):
        '''Return a dict of results. The default returns a dict with
        results keyed by self.RESULTS, the data point in the parameter space
        keyed by self.PARAMETERS, and timing and other metadata keyed
        by self.METADATA. Overriding this method can be used to record extra
        values, but be sure to call the base method as well.
 
        res: the direct experimental results from do()
        returns: a dict of extended results'''
        rc = dict()
        rc[self.METADATA] = self._metadata
        rc[self.PARAMETERS] = self._parameters
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
        self._results = None
        res = None
        doneSetupTime = doneExperimentTime = doneTeardownTime = 0
        try:
            # do the phases in order, recording the wallclock times at each phase
            startTime = time.clock()
            self.setUp(params)
            doneSetupTime = time.clock()
            res = self.do(params)
            doneExperimentTime = time.clock() 
            self.tearDown()
            doneTeardownTime = time.clock() 

            # record the various timings
            self._metadata[self.START_TIME] = startTime
            self._metadata[self.END_TIME] = doneTeardownTime
            self._metadata[self.ELAPSED_TIME] = doneTeardownTime - startTime
            self._metadata[self.SETUP_TIME] = doneSetupTime - startTime
            self._metadata[self.EXPERIMENT_TIME] = doneExperimentTime - doneSetupTime
            self._metadata[self.TEARDOWN_TIME] = doneTeardownTime - doneExperimentTime

            # set the success flag
            self._metadata[self.STATUS] = True
        except Exception as e:
            print "Caught exception in experiment: {e}".format(e = e)
            
            # decide on the cleanup actions that need doing
            if (doneSetupTime > 0) and (doneExperimentTime == 0):
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
        if res is None:
            res = dict()
        self._results  = self.report(res)
        return self._results 

    def results( self ):
        '''Return the results of the experiment.

        returns: a dict of results'''
        return self._results

    def __getitem__( self, k ):
        '''Return the given element of the experimental results. This only
        gives access to direct experimental results, not to parameters
        or metadata.

        k: the result key
        returns: the value'''
        if self._results is None:
            raise Exception("No results set")
        else:
            return self._results[self.RESULTS][k]
    
    def success( self ):
        '''Test whether the experiment has been run successfully.

        returns: True if the experiment has been run successfully'''
        if self.STATUS in self._metadata:
            return self._metadata[self.STATUS]
        else:
            return False
    

    
        
    
