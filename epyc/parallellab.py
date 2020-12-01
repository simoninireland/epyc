# Simulation "lab" experiment management, local parallel version
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

from epyc import Lab, LabNotebook, Experiment
import numpy                                     # type: ignore
from joblib import Parallel, delayed
from multiprocessing import cpu_count


class ParallelLab(Lab):
    '''A :class:`Lab` that uses local parallelism.

    Unlike a basic :class:`Lab`, this class runs multiple experiments
    in parallel to accelerate throughput. Unlike a :class:`ClusterLab` it
    runs all jobs synchronously and locally, and so can't make use of a larger
    compute cluster infrastructure and can't run tasks in the background
    to be collected later. This does however mean that ``epyc`` can make
    full use of a multicore machine quite trivially.

    The optional ``cores`` parameter selects the number of cores to use
    according to the conventions of ``joblib``:

    - a value of 1 uses 1 core (sequential mode);
    - a value of +n uses n cores;
    - a value of -1 uses all available cores; and
    - a value of -2 or below uses (available + 1 + cores) cores.

    So a value of ``cores=-2`` will run on 1 fewer cores than the total number
    of physical cores available on the machine.
    
    Note that you can specify more cores to use
    than there are physical cores on the machine: this will have no positive effects.
    Note also that using all the cores on a machine may result in you being
    locked out of the user interface as your experiments consume all available
    computational resources, and may also be regarded as an unfriendly act by
    any other users with whom you share the machine.

    :param notebook: (optional) the notebook used to store results
    :param cores: (optional) number of cores to use (defaults to all available)
    '''

    def __init__(self, notebook : LabNotebook =None, cores : int =-1):
        super(ParallelLab, self).__init__(notebook)

        # compute the nunber of cores to use and store for later
        if cores == -1:
            # use all available
            cores = cpu_count()
        elif cores < -1:
            # use fewer than available, down to a minimum of 1
            cores = max(cpu_count() + 1 + cores, 1)
        self._cores = cores

    def numberOfCores(self) -> int:
        '''Return the number of cores we will use to run experiments.

        :returns: maximum number of concurrent experiments'''
        return self._cores


    # ---------- Running experiments ----------

    def runExperiment(self, e : Experiment):
        """Run the experiment across the parameter space in parallel using
        the allowed cores. The experiments are all run synchronously.

        :param e: the experiment"""

        # create the parameter space
        space = self.parameterSpace()
        nps = len(space)

        # only proceed if there's work to do
        if len(space) > 0:
            nb = self.notebook()

            # randomise the order of the parameter space so that we reduce the
            # risk of computational imbalance, as there's a barrier synchronisation
            # between chunks of experiments]
            ps = space.copy()
            numpy.random.shuffle(ps)

            # run the experiments
            try:
                chunk = self.numberOfCores()
                with Parallel(n_jobs=chunk) as processes:
                    # compute number of parallel chunks we'll run
                    nchunks = int(nps / chunk)
                    if nps % chunk > 0:
                        nchunks += 1

                    # run the experiments in chunks
                    i = 0
                    for _ in range(nchunks):
                        # determine and extract the next chunk of parameter space
                        di = min(chunk, len(ps) - i)
                        eps = list(zip([e] * di, ps[i:i + di]))

                        # run over the chunk
                        rcs = processes(delayed(lambda ep: ep[0].set(ep[1]).run())(ep) for ep in eps)

                        # add the results as they come back
                        for rc in rcs:
                            nb.addResult(rc)

                        i += di
            finally:
                # commit our pending results in the notebook
                nb.commit()
                self.close()

    