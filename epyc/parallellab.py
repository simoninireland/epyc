# Simulation "lab" experiment management, local parallel version
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

import logging
from joblib import Parallel, delayed
from multiprocessing import cpu_count
from epyc import Logger, Lab, LabNotebook, Experiment


logger = logging.getLogger(Logger)


class ParallelLab(Lab):
    '''A :class:`Lab` that uses local parallelism.

    Unlike a basic :class:`Lab`, this class runs multiple experiments
    in parallel to accelerate throughput. Unlike a :class:`ClusterLab` it
    runs all jobs synchronously and locally, and so can't make use of a larger
    compute cluster infrastructure and can't run tasks in the background
    to be collected later. This does however mean that ``epyc`` can make
    full use of a multicore machine quite trivially.

    The optional ``cores`` parameter selects the number of cores to use:

    - a value of 1 uses 1 core (sequential mode);
    - a value of +n uses n cores;
    - a value of 0 uses all available cores; and
    - a value of -n uses (available - n) cores.

    So a value of ``cores=-1`` will run on 1 fewer cores than the total number
    of physical cores available on the machine.

    .. important ::

        This behaviour is slightly different to that of ``joblib``
        as described `here <https://joblib.readthedocs.io/en/latest/generated/joblib.Parallel.html>`_.

    Note that you can specify more cores to use
    than there are physical cores on the machine: this will have no positive effects.
    Note also that using all the cores on a machine may result in you being
    locked out of the user interface as your experiments consume all available
    computational resources, and may also be regarded as an unfriendly act by
    any other users with whom you share the machine.

    :param notebook: (optional) the notebook used to store results
    :param cores: (optional) number of cores to use (defaults to all available)
    '''

    def __init__(self, notebook: LabNotebook = None, cores: int = 0):
        super().__init__(notebook)

        # compute the nunber of cores to use and store for later
        if cores == 0:
            # use all available
            cores = cpu_count()
        elif cores < 0:
            # use fewer than available, down to a minimum of 1
            cores = max(cpu_count() + cores, 1)   # cpu_count() + cores as cores is negative
        else:
            # use the number of cores requested, up to the maximum available
            cores = min(cores, cpu_count())
        self._cores = cores
        logger.info(f'ParallelLab created with {cores} cores')

    def numberOfCores(self) -> int:
        '''Return the number of cores we will use to run experiments.

        :returns: maximum number of concurrent experiments'''
        return self._cores


    # ---------- Running experiments ----------

    def runExperiment(self, e: Experiment):
        """Run the experiment across the parameter space in parallel using
        the allowed cores. The experiments are all run synchronously.

        :param e: the experiment"""

        # create the experimental parameter space
        eps = self.experiments(e)
        nps = len(eps)

        # only proceed if there's work to do
        if nps > 0:
            nb = self.notebook()

            # run the experiments
            try:
                with Parallel(n_jobs=self.numberOfCores()) as processes:
                    # run over the chunk
                    rcs = processes(delayed(lambda ep: ep[0].set(ep[1]).run())(ep) for ep in eps)

                    # add the results as they come back
                    for rc in rcs:
                        nb.addResult(rc)
            finally:
                # commit our pending results in the notebook
                nb.commit()
                self.close()
