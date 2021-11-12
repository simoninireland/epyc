# First experiment taken from the first tutorial
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

import numpy
import pandas
import matplotlib
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
import matplotlib.pyplot as plt
from epyc import Experiment, Lab, JSONLabNotebook


class CurveExperiment(Experiment):
    '''An experiment that computes the surface of a 2d function using
    epyc, whcih is then plotted and rendered as a PNG file.'''

    def do(self, params):
        '''Compute the sin value from two parameters x and y, returning a dict
        containing a result key with the computed value.

        :param params: the parameters
        :returns: the result dict'''
        x = params['x']
        y = params['y']
        r = numpy.sin(numpy.sqrt(x**2 + y**2))
        return dict(result = r)

# Create a lab in which to perform the experiment.
#
# We use a persistent JSON-based notebook to store the results: as
# an alternative we could have usedd a transient in-memory notebook
# (the LabNotebook class) of a notebook that uses HDF5 and so can
# interoperate with other tools (HDF5LabNNotebook).
lab = Lab(notebook = JSONLabNotebook("sin.json",
                                     create = True,
                                     description = "A point cloud of $sin \sqrt{x^2 + y^2}$"))

# Set up the parameter space within which to perform experiments.
#
# We could if we wanted increase the resolution of the computation
# by simply providing more points at which to plot the function.
# By default numpy uses 50 points ina  linspace: we could instead
# request 100 (or more) points for epyc to compute at.
lab['x'] = numpy.linspace(-2 * numpy.pi, 2 * numpy.pi)
lab['y'] = numpy.linspace(-2 * numpy.pi, 2 * numpy.pi)

# Run the experiment
lab.runExperiment(CurveExperiment())

# Retrieve the results
df = lab.dataframe()

# Plot the function
fig = plt.figure(figsize = (8, 8))
ax = fig.add_subplot(projection = '3d')

ax.scatter(df['x'], df['y'], df['result'],
           c=df['result'], depthshade=False, cmap=cm.coolwarm)
ax.set_xlim(numpy.floor(df['x'].min()), numpy.ceil(df['x'].max()))
ax.set_ylim(numpy.floor(df['y'].min()), numpy.ceil(df['y'].max()))
ax.set_zlim(numpy.floor(df['result'].min()), numpy.ceil(df['result'].max()))

plt.title(lab.notebook().description())
ax.set_xlabel('$x$')
ax.set_ylabel('$y$')

# Save the figure as a PNG
plt.savefig('pointcloud.png')
