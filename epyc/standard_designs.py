# Standard experimental designs
#
# Copyright (C) 2016--2022 Simon Dobson
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

from typing import Dict, List, Tuple, Any
import numpy
from epyc import Design, DesignException, Experiment, ExperimentalConfiguration


class FactorialDesign(Design):
    '''A simple factorial design.

    In a factorial design, an experiment is perform for every
    combination of a lab's parameters. Essentially this forms the
    cross-product of all parameter values, returned as a list of
    dicts. If the lab was set up with the following parameters:

    .. code-block:: python

       lab['a'] = [1, 2]
       lab['b'] = [3, 4]

    then this design would generate a space consisting of four points:

    - {a=1, b=3}
    - {a=1, b=4}
    - {a=2, b=3}
    - {a=2, b=4}

    at which it would run the given experiment. The experiments are
    returned in random order.

    '''

    def experiments(self, e: Experiment, ps: Dict[str, Any]) -> ExperimentalConfiguration:
        '''Form the cross-product of all parameters.

        :param ps: a dict of parameter values
        :returns: an experimental configuration'''
        ds = []
        for p in ps.keys():
            rs = ps[p]
            dsprime = []
            for r in rs:
                if len(ds) > 0:
                    for (_, dp) in ds:
                        eprime = dp.copy()
                        eprime[p] = r
                        dsprime.append((e, eprime))
                else:
                    eprime = {}
                    eprime[p] = r
                    dsprime.append((e, eprime))
            if len(dsprime) > 0:
                ds = dsprime

        # randomise the order of the experiments
        numpy.random.shuffle(ds)

        return ds


class PointwiseDesign(Design):
    '''A design whose space is the sequence of values taken from the range
    of each parameter. If the lab was set up with the following parameters:

    .. code-block:: python

       lab['a'] = [1, 2]
       lab['b'] = [3, 4]

    then this design would generate a space consisting of two points:

    - {a=1, b=3}
    - {a=2, b=4}

    This design requires that all parameters have the same length of range:
    if a parameter is a singleton (only a single value), this will be extended
    across all the space. So if the parameters were:

    .. code-block:: python

       lab['a'] = 1
       lab['b'] = [3, 4]

    the design would generate:

    - {a=1, b=3}
    - {a=1, b=4}
    '''

    def experiments(self, e: Experiment, ps: Dict[str, Any]) -> ExperimentalConfiguration:
        '''Form experimental points from corresponding values in
        the parameter ranges, extending any singletons.

        :param ps: a dict of parameter values
        :returns: an experimental configuration'''

        # check parameter ranges are all equal or 1
        ls = list(map(len, list(ps.values())))
        sls = set(ls)
        nls = len(sls)
        l = 0
        if nls == 1:
            # only one parameter range length
            l = ls[0]
        elif nls > 1:
            # more than one length, are there too many altogether?
            if nls > 2:
                # too many different ranges
                raise DesignException('Parameter range lengths don\'t match')
            elif 1 not in sls:
                # not extending
                raise DesignException('Parameter range lengths don\'t match an not extending')
            else:
                # some ranges are being extended, extract the other length
                for j in sls:
                    if j != 1:
                        l = j

        # extract the parameters being extended
        ones = [p for (p, v) in ps.items() if len(v) == 1]

        ds = []
        for i in range(l):
            eprime = {}
            for p in ps.keys():
                if p in ones:
                    eprime[p] = ps[p][0]
                else:
                    eprime[p] = ps[p][i]
            ds.append((e, eprime))
        return ds
