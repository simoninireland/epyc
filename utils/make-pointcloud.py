# Perform the simple pointcloud experiment and generate a plot
#
# Copyright (C) 2016--2019 Simon Dobson
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

import epyc
import numpy
import pandas
import matplotlib
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
import matplotlib.pyplot as plt
import seaborn


class CurveExperiment(epyc.Experiment):

    def do(self, params):
        x = params['x']
        y = params['y']
        r = numpy.sin(numpy.sqrt(x ** 2 + y ** 2))
        return dict(result=r)

lab = epyc.Lab(notebook=epyc.JSONLabNotebook("sin.json",
                                             create=True,
                                             description="A point cloud of $sin \sqrt{x^2 + y^2}$"))
lab['x'] = numpy.linspace(-2 * numpy.pi, 2 * numpy.pi)
lab['y'] = numpy.linspace(-2 * numpy.pi, 2 * numpy.pi)
lab.runExperiment(CurveExperiment())

df = lab.notebook().dataframe()
fig = plt.figure(figsize = (8, 8))
ax = fig.gca(projection = '3d')

ax.scatter(df['x'], df['y'], df['result'], c = df['result'], depthshade = False, cmap = cm.coolwarm)
ax.set_xlim(numpy.floor(df['x'].min()), numpy.ceil(df['x'].max()))
ax.set_ylim(numpy.floor(df['y'].min()), numpy.ceil(df['y'].max()))
ax.set_zlim(numpy.floor(df['result'].min()), numpy.ceil(df['result'].max()))

plt.title(lab.notebook().description())
ax.set_xlabel('$x$')
ax.set_ylabel('$y$')

plt.savefig('doc/tutorial/pointcloud.png')
