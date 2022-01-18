# Base class for experiment combinators that co=ordinate other experiments
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

from epyc import Experiment
from typing import Dict, Any


class ExperimentCombinator(Experiment):
    """An experiment that wraps-up another, underlying experiment. This is an abstract
    class that just provides the common wrapping logic.

    Experiment combinators aren't expected to have parameters of their own: they
    simply use the parameters of their underlying experiment. They may however
    give rise to metadata of their own, and modify the results returned by running
    their underlying experiment."""

    def __init__(self, ex : Experiment):
        """Create a combinator based on the given experiment.

        ex: the underlying experiment"""
        super().__init__()
        self._experiment = ex

    def experiment(self) -> Experiment:
        """Return the underlying experiment.

        :returns: the underlying experiment"""
        return self._experiment

    def set(self, params : Dict[str, Any]) -> Experiment:
        """Set the parameters for the experiment, returning the
        now-configured experiment.

        :param params: the parameters
        :returns: the experiment combinator itself"""
        self.experiment().set(params)
        return self

    def parameters(self) -> Dict[str, Any]:
        """Return the current experimental parameters, taken from the
        underlying experiment.

        :returns: the parameters,"""
        return self.experiment().parameters()
