# Create an HDF5 file to be used for URL access tests
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

from epyc import Experiment, HDF5LabNotebook

class SampleExperiment(Experiment):
    '''A very simple experiment that adds up its parameters.'''
    
    def do( self, param ):
        return dict(total=param['k'] + 10)

e = SampleExperiment()
rc1 = e.set(dict(k=10)).run()
rc2 = e.set(dict(k=20)).run()
rc3 = e.set(dict(k=30)).run()
rc4 = e.set(dict(k=40)).run()

with HDF5LabNotebook('test/test.h5', create=True).open() as nb:
    # first result set
    nb.addResultSet('first')
    nb.addResult(rc1)
    nb.addResult(rc2)

    # second
    nb.addResultSet('second')
    nb.addResult(rc3)
    nb.addPendingResult(rc4[Experiment.PARAMETERS], '2345')

