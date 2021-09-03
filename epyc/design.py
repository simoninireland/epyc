# Base class for experimental designs
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

from typing import Dict, List, Tuple, Any
from epyc import Experiment


# Type alias for sets of experiments
ExperimentalConfiguration = List[Tuple[Experiment, Dict[str, Any]]]    #: Type of a configuration of experiments.


class DesignException(Exception):
    '''An exception raised whenever a set of parameter ranges can't
    be used as the basis for a design.

    '''

    def __init__(self, msg: str):
        super().__init__(f'Design excpetion: {msg}')


class Design:
    '''Base class for experimental designs.

    A "design" is a protocol for conducting a set of experiments so as
    to maximise the amount of useful data collected. It is a common
    topic in real-world experiments, and can be applied to
    computational experiments as well.

    A design in ``epyc`` converts a set of :term:`experimental
    parameters` into ann :term:`experimental configuration`, a list
    consisting of pairs of an experiment to run and the parameters at
    which to run it.

    A design must be able to cope with being passed None as an
    experiment, and should return None for all the experiments in the
    configuration: this allows for pre-checks to be performed.

    A design is associated with each :class:`Lab`. By default the standard
    :class:`FactorialDesign` is used, and no further action is needed. Other
    designs can be selected at lab creation time.

    '''

    def experiments(self, e: Experiment, ps: Dict[str, Any]) -> ExperimentalConfiguration:
        '''Convert a mapping from parameter name to list of values into
        a list of mappings from parameter names to single values paired with
        experiment to run at that point, according to the requirements of the
        design. This method must be overridden by sub-classes.

        :param ps: a dict of parameter values
        :returns: an experimental configuration'''
        raise NotImplementedError('parameterSpace() must be overridden by sub-classes')
