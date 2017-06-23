# Simulation "lab" experiment management, sequential version
#
# Copyright (C) 2016 Simon Dobson
# 
# Licensed under the GNU General Public Licence v.2.0
#

import epyc

import collections


class Lab(object):
    '''A laboratory for computational experiments.

    A :class:`Lab` conducts an experiment at different points in a
    multi-dimensional parameter space.  The default performs all the
    experiments locally; sub-classes exist to perform remote parallel
    experiments.

    A :class:`Lab` stores its result in a notebook, an instance of :class:`LabNotebook`.
    By default the base :class:`Lab` class uses an in-memory notebook, essentially
    just a dict; sub-clasess use persistent notebooks to manage larger
    sets of experiments.
    '''

    def __init__( self, notebook = None ):
        '''Create an empty lab.
 
        :param notebook: the notebook used to store results (defaults to an empty :class:`LabNotebook`)'''
        if notebook is None:
            self._notebook = epyc.LabNotebook()
        else:
            self._notebook = notebook
        self._parameters = dict()

    def open( self ):
        '''Open a lab for business. Sub-classes might insist the they are
        opened and closed explicitly when experiments are being performed.
        The default does nothing.'''
        pass

    def close( self ):
        '''Shut down a lab. Sub-classes might insist the they are
        opened and closed explicitly when experiments are being performed.
        The default does nothing.'''
        pass

    def updateResults( self ):
        '''Update the lab's results. This method is called by all other methods
        that return results in some sense, and may be overridden to let the results
        "catch up" with external processing. The default does nothing.'''
        pass
    
    def addParameter( self, k, r ):
        '''Add a parameter to the experiment's parameter space. k is the
        parameter name, and r is its range.

        :param k: parameter name
        :param r: parameter range'''

        # if range is a single value, make it a list
        if isinstance(r, basestring) or not isinstance(r, collections.Iterable):
            r = [ r ]
        self._parameters[k] = r

    def parameters( self ):
        '''Return a list of parameter names.

        :returns: a list of parameter names'''
        return self._parameters.keys()

    def __len__( self ):
        '''The length of an experiment is the total number of data points
        that will be explored. 

        :returns: the length of the experiment'''
        n = 1
        for p in self.parameters():
            n = n * len(self._parameters[p])
        return n
        
    def __getitem__( self, k ):
        '''Access a parameter range using array notation.

        :param k: parameter name
        :returns: the parameter range'''
        return self._parameters[k]

    def __setitem__( self, k, r ):
        '''Add a parameter using array notation.

        :param k: the parameter name
        :param r: the parameter range'''
        return self.addParameter(k, r)

    def _crossProduct( self, ls ):
        '''Internal method to generate the cross product of all parameter
        values, creating the parameter space for the experiment.

        :param ls: an array of parameter names
        :returns: list of dicts'''
        p = ls[0]
        ds = []
        if len(ls) == 1:
            # last parameter, convert range to a dict
            for i in self._parameters[p]:
                dp = dict()
                dp[p] = i
                ds.append(dp)
        else:
            # for other parameters, create a dict combining each value in
            # the range to a copy of the dict of other parameters
            ps = self._crossProduct(ls[1:])
            for i in self._parameters[p]:
                for d in ps:
                    dp = d.copy()
                    dp[p] = i
                    ds.append(dp)

        # return the complete parameter space
        return ds
           
    def parameterSpace( self ):
        '''Return the parameter space of the experiment as a list of dicts,
        with each dict mapping each parameter name to a value.

        :returns: the parameter space as a list of dicts'''
        ps = self.parameters()
        if len(ps) == 0:
            return []
        else:
            return self._crossProduct(ps)
    
    def runExperiment( self, e ):
        '''Run an experiment over all the points in the parameter space.
        The results will be stored in the notebook.

        :param e: the experiment'''

        # create the parameter space
        ps = self.parameterSpace()

        # run the experiment at each point
        nb = self.notebook()
        for p in ps:
            # print "Running {p}".format(p = p)
            res = e.set(p).run()
            nb.addResult(res)

        # commit the results
        nb.commit()

    def notebook( self ):
        '''Return the notebook being used by this lab.

        :returns: the notebook'''
        return self._notebook
    
    def results( self ):
        '''Retrieve the list of :term:`results dict` hashes (each of which contains the
        point at which the experiment was evaluated to get this
        result).

        :returns: a list of results dicts'''
        self.updateResults()
        return self.notebook().results()

    def dataframe( self ):
        '''Return the results as a pandas DataFrame.

        :returns: the resulting dataset as a DataFrame'''
        self.updateResults()
        return self.notebook().dataframe()
    
    def ready( self ):
        '''Test whether all the results are ready, that is none are
        pending.

        :returns: True if the results are in'''
        self.updateResults()
        return (len(self.notebook().pendingResults()) == 0)


