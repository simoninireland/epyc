# Base class for experiments
#
# Copyright (C) 2016--2021 Simon Dobson
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

from datetime import datetime
import traceback
import sys
if sys.version_info >= (3, 8):
    from typing import Set, Dict, Union, List, Any, Final
else:
    # backwards compatibility with Python 35, Python36, and Python37 
    from typing import Set, Dict, Union, List, Any
    from typing_extensions import Final

# The type of results dicts
ResultsDict = Dict[str, Dict[str, Any]]     #: Type of results dicts.

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

    # Top-level structure for results dicts
    METADATA : Final[str] = 'metadata'                 #: Results dict key for metadata values, mainly timing.
    PARAMETERS : Final[str] = 'parameters'             #: Results dict key for describing the point in the parameter space the experiment ran on.
    RESULTS : Final[str] = 'results'                   #: Results dict key for the experimental results generated at the experiment's parameter point.

    # Standard metadata elements reported
    EXPERIMENT : Final[str] = 'epyc.experiment.classname'              #: Metadata element for storing the class name of the experiment.
    START_TIME : Final[str] = 'epyc.experiment.start_time'             #: Metadata element for the datetime experiment started.
    END_TIME : Final[str] = 'epyc.experiment.end_time'                 #: Metadata element for the datetime experiment ended.
    ELAPSED_TIME : Final[str] = 'epyc.experiment.elapsed_time'         #: Metadata element for the time experiment took overall in seconds.
    SETUP_TIME : Final[str] = 'epyc.experiment.setup_time'             #: Metadata element for the time spent on setup in seconds.
    EXPERIMENT_TIME : Final[str] = 'epyc.experiment.experiment_time'   #: Metadata element for the time spent on experiment itself in seconds.
    TEARDOWN_TIME : Final[str] = 'epyc.experiment.teardown_time'       #: Metadata element for the time spent on teardown in seconds.
    STATUS : Final[str] = 'epyc.experiment.status'                     #: Metadata element that will be True if experiment completed successfully, False otherwise.
    EXCEPTION : Final[str] = 'epyc.experiment.exception'               #: Metadata element containing the exception thrown if experiment failed.
    TRACEBACK : Final[str] = 'epyc.experiment.traceback'               #: Metadata element containing the traceback from the exception (as a string).

    # The above, collected together
    StandardMetadata : Set[str]                        #: The standard metadata elements to always capture.  
    StandardMetadataTypes : Dict[str, type]            #: Type mapping for standard metadata.

    def __init__(self):
        self._metadata : Dict[str, Any] = dict()
        self._parameters : Dict[str, Any] = dict()
        self._results : Union[Dict[str, Any], List[Dict[str, Any]]] = dict()

    @classmethod
    def _init_statics(cls):
        '''Initialise the static members that need complex constructors.'''
        cls.StandardMetadata = set([ cls.EXPERIMENT,
                                     cls.START_TIME,
                                     cls.END_TIME,
                                     cls.ELAPSED_TIME,
                                     cls.EXPERIMENT_TIME,
                                     cls.SETUP_TIME,
                                     cls.TEARDOWN_TIME,
                                     cls.STATUS,
                                     cls.EXCEPTION,
                                     cls.TRACEBACK
                                   ]) 
        cls.StandardMetadataTypes = { cls.EXPERIMENT: str,
                                      cls.START_TIME: datetime,
                                      cls.END_TIME: datetime,
                                      cls.ELAPSED_TIME: float,
                                      cls.SETUP_TIME: float,
                                      cls.EXPERIMENT_TIME: float,
                                      cls.TEARDOWN_TIME: float,
                                      cls.STATUS: bool,
                                      cls.EXCEPTION: str,
                                      cls.TRACEBACK: str,
                                    }

    # ---------- Results dicts ----------

    @staticmethod
    def resultsdict() -> ResultsDict:
        '''Create an empty results dict, structured correctly.

        :returns: an empty results dict'''
        rc : ResultsDict = dict()
        rc[Experiment.PARAMETERS] = dict()
        rc[Experiment.METADATA] = dict()
        rc[Experiment.RESULTS] = dict()
        return rc


    # ---------- Configuration ----------

    def set(self, params: Dict[str, Any]) -> 'Experiment':
        """Set the parameters for the experiment, returning the
        now-configured experiment.

        :param params: the parameters
        :returns: the experiment"""
        if self._parameters is not None:
            self.deconfigure()
        self.configure(params)
        return self

    def configure(self, params : Dict[str, Any]):
        """Configure the experiment for the given parameters.
        The default stores the parameters for later use. Be sure
        to call this base method when overriding.

        :param params: the parameters"""
        self._parameters = params

    def deconfigure(self):
        """De-configure the experiment prior to setting new parameters.
        The default removes the parameters. Be sure
        to call this base method when overriding."""
        self._parameters = dict()


    # ---------- Running the experiment ----------

    def setUp(self, params : Dict[str, Any]):
        """Set up the experiment. Default does nothing.

        :param params: the parameters of the experiment"""
        pass

    def tearDown(self):
        """Tear down the experiment. Default does nothing."""
        pass

    def do(self, params : Dict[str, Any]) -> Union[Dict[str, Any], List[ResultsDict]]:
        """Do the body of the experiment. This should be overridden
        by sub-classes. Default does nothing.

        An experiment can return two types of results:

        - a dict mapping names to values for experimental results
        - a list of :term:`results dict`s, which represent fully-formed experiments

        params: a dict of parameters for the experiment
        returns: the experimental results """
        return dict()

    def report(self, params : Dict[str, Any], meta : Dict[str, Any], res : Union[Dict[str, Any], List[ResultsDict]]) -> ResultsDict:
        """Return a properly-structured dict of results. The default returns a dict with
        results keyed by :attr:`Experiment.RESULTS`, the data point in the parameter space
        keyed by :attr:`Experiment.PARAMETERS`, and timing and other metadata keyed
        by :attr:`Experiment.METADATA`. Overriding this method can be used to record extra
        metadata values, but be sure to call the base method as well.

        If the experimental results are a list of results dicts, then we report a
        results dict whose results are a list of results dicts.
        This is used by :class:`RepeatedExperiment` amd other experiments that want to report
        multiple sets of results.

        :param params: the parameters we ran under
        :param meta: the metadata for this run
        :param res: the direct experimental results from do()
        :returns: a :term:`results dict`"""
        rc = Experiment.resultsdict()
        rc[self.PARAMETERS] = params.copy()
        rc[self.METADATA] = meta.copy()
        rc[self.RESULTS] = res
        return rc

    def run(self) -> ResultsDict:
        """Run the experiment, using the parameters set using :meth:`set`.
        A "run" consists of calling :meth:`setUp`, :meth:`do`, and :meth:`tearDown`,
        followed by collecting and storing (and returning) the
        experiment's results. If running the experiment raises an
        exception, that will be returned in the metadata along with
        its traceback to help with experiment debugging.

        :returns: a :term:`results dict`"""
        
        # record the experiment's class name
        self._metadata = dict()
        cn = '{modulename}.{classname}'.format(modulename = self.__class__.__module__,
                                               classname = self.__class__.__name__)
        self._metadata[self.EXPERIMENT] = cn

        # perform the experiment protocol
        params = self.parameters()
        self._results = dict()
        res = dict()
        doneSetupTime = doneExperimentTime = doneTeardownTime = None
        elapsedTime = 0
        startTime = datetime.now()
        self._metadata[self.START_TIME] = startTime
        try:
            # do the phases in order, recording the wallclock times at each phase
            self.setUp(params)
            doneSetupTime = datetime.now()
            dt = (doneSetupTime - startTime).total_seconds()
            elapsedTime = dt
            self._metadata[self.SETUP_TIME] = dt
            res = self.do(params)
            doneExperimentTime = datetime.now()
            dt = (doneExperimentTime - doneSetupTime).total_seconds()
            elapsedTime += dt
            self._metadata[self.EXPERIMENT_TIME] = dt
            self.tearDown()
            doneTeardownTime = datetime.now() 
            dt = (doneTeardownTime - doneExperimentTime).total_seconds()
            elapsedTime += dt
            self._metadata[self.TEARDOWN_TIME] = dt
            self._metadata[self.END_TIME] = doneTeardownTime
            self._metadata[self.ELAPSED_TIME] = elapsedTime
            
            # set the success flag
            self._metadata[self.STATUS] = True
        except Exception as e:
            print("Caught exception in experiment: {e}".format(e=e), file=sys.stderr)

            # grab the traceback before we do anything else
            #_, _, tb = sys.exc_info()
            tb = traceback.format_exc()
            
            # decide on the cleanup actions that need doing
            if (doneSetupTime is not None) and (doneExperimentTime is None):
                # we did the setup and then failed in the experiment, so
                # we need to do the teardown
                try:
                    self.tearDown()
                except Exception as f:
                    # log, but otherwise ignore, any exceptions
                    # that happen in the teardown
                    print("Caught exception in teardown (ignored): {f}".format(f=f), file=sys.stderr)
            self._metadata[self.ELAPSED_TIME] = elapsedTime
            self._metadata[self.END_TIME] = datetime.now()

            # set the failure flag and record the exception
            self._metadata[self.STATUS] = False
            self._metadata[self.EXCEPTION] = e
            self._metadata[self.TRACEBACK] = tb
                
        # report the results
        self._results = res
        return self.report(params,
                           self._metadata,
                           res)


    # ---------- Accessing results ----------

    def __getitem__(self, k : str) -> Any:
        """Return the given element of the experimental results. This only
        gives access to the experimental results, *not* to the parameters
        or metadata.

        :param k: the result key
        :returns: the value
        :raises: KeyError if there is no such result"""
        return (self.experimentalResults())[k]
    
    def success(self) -> bool:
        """Test whether the experiment has been run successfully. This will
        be False if the experiment hasn't been run, or if it's been run and
        failed.

        :returns: ``True`` if the experiment has been run successfully"""
        if self.STATUS in self.metadata().keys():
            return (self.metadata())[self.STATUS]
        else:
            return False

    def failed(self) -> bool:
        '''Test whether an experiment failed. This will be True if the experiment has
        been run and has failed, which means that there will be an exception and traceback
        information stored in the metadata. It will be False if the experiment hasn't
        been run.

        :returns: ``True`` if the experiment has failed'''
        if self.STATUS not in self.metadata().keys():
            return False
        else:
            return not (self.metadata())[self.STATUS]

    def results(self) -> Union[ResultsDict, List[ResultsDict]]:
        """Return a complete results dict. Only really makes sense for
        recently-executed experimental runs.

        :returns: the results dict, or a list of them"""
        return self.report(self.parameters(),
                           self.metadata(),
                           self.experimentalResults())

    def experimentalResults(self) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Return the experimental results from our last run. This will
        be None if we haven't been run, or if we ran and failed.

        :returns: the experimental results dict, which may be empty, and may be a list of dicts"""
        return self._results
    
    def parameters(self) -> Dict[str, Any]:
        """Return the current experimental parameters, which will
        be None if none have been given by a call to set()

        :returns: the parameters, which may be empty"""
        return self._parameters

    def metadata(self) -> Dict[str, Any]:
        """Return the metadata we collected at out last execution, which
        will be None if we've not been executed and an empty dict if
        we're mid-run (i.e., if this method is called from do() for
        whatever reason).

        :returns: the metadata, which may be empty"""
        return self._metadata
    
    
        
    
