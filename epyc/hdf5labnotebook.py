# Simulation "lab notebook" for collecting results, HDF5 version
#
# Copyright (C) 2020 Simon Dobson
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

from epyc import ResultSet, Experiment, LabNotebook, ResultsDict
import os
import h5py                    # type: ignore
import numpy                   # type: ignore
from datetime import datetime
from pandas import DataFrame   # type: ignore
import dateutil.parser
from contextlib import contextmanager
from typing import ContextManager, Dict, List, Set, Type, Final, Any, cast

class HDF5LabNotebook(LabNotebook):
    '''A lab notebook that persists itself to an HDF5 file.
    `HDF5 <https://www.hdfgroup.org/>`_  is a very common format
    for sharing large scientific datasets, allowing ``epyc`` to interoperate
    with a larger toolchain.

    ``epyc`` is built on top of the ``h5py`` `Python binding to HDF5 <https://www.h5py.org/>`_,
    which handles most of the heavy lifting using a lot of machinery for typing
    and so on matched with ``numpy``. Note that
    the limitations of HDF5's types mean that some values may have
    different types when read than when acquired. (See :ref:`hdf5-type-management`
    for details.)

    :param name: HDF5 file to persist the notebook to
    :param create: (optional) if True, erase any existing file (defaults to False)
    :param description: (optional) free text description of the notebook 
    '''

    # Tuning parameters
    DefaultDatasetSize : int = 10                    #: Default initial size for a new HDF5 dataset.

    # Dataset structure
    RESULTS_DATASET : Final[str] = 'results'         #: Name of results dataset within the HDF5 group for a result set.
    PENDINGRESULTS_DATASET : Final[str] = 'pending'  #: Name of pending results dataset within the HDF5 group for a result set.

    # Metadata for the datasets

    # Metadata for the notebook
    DESCRIPTION : Final[str] = 'description'         #: Attribute holding the notebook description.
    CURRENT : Final[str] = 'current'                 #: Attribute holding the tag of the current result set.


    def __init__(self, name : str, create : bool =False, description : str = ''):
        # create an empty file structure
        self._file : h5py.File = None          # file handle for underlying HDF5 file
        self._group : h5py.Group = None        # group associated with the current result set

        # check for file needing creation
        created = create or not os.path.isfile(name)
        if created:
            self._create(name, description)                

        # perform the normal initialisation
        super(HDF5LabNotebook, self).__init__(name, description)

        # load notebook from file if it wasn't newly created
        if not created:
            self._open()
            self._load()
            self._close()


    # ---------- Persistence ----------

    def isPersistent(self) -> bool:
        """Return True to indicate the notebook is persisted to an HDF5 file.

        :returns: True"""
        return True

    def commit(self):
        """Persist any changes in the result sets in the notebook to disc."""
        self._open()
        self._save()
        self._close()


    # ---------- Managing result sets ----------

    def addResultSet(self, tag : str, title : str =None) -> str:
        '''Add the necessary structure to the underlying file when creating the
        new result set. This ensures that, even if no results are added,
        there will be structure in the persistent store to indicate that the result
        set was created.

        :param tag: the tag
        :param title: (optional) the title
        :returns: the tag'''
        super(HDF5LabNotebook, self).addResultSet(tag, title)

        # add the appropriate group to the HDF5 file
        self._open()
        if tag not in self._file:
            self._file.create_group(tag)

        return tag


    # ---------- Protocol for managing the HDF5 file----------
    
    def _create(self, name : str, description : str):
        '''Create the HDF5 file to back this notebook.
        
        :param name: the filename
        :param description: the free text description of this notebook'''
        self._file = h5py.File(name, 'w')
        self._file.attrs[self.DESCRIPTION] = description
        self._description = description
        self._file.attrs[self.CURRENT] = self.DEFAULT_RESULTSET
        #self._current = self.resultSet(self.DEFAULT_RESULTSET)

    def _open(self):
        '''Open the HDF5 file that backs this notebook.'''
        if self._file is None:
            self._file = h5py.File(self.name(), 'a')

    def _close(self):
        '''Close the underlying HDF5 file.'''
        if self._file is not None:
            self._file.close()
            self._file = None

    def _write(self, tag : str):
        '''Write the given result set to the file.

        :tag: the result set tag'''
        rs = self.resultSet(tag)
        names = rs.names()
        g = self._file[tag]

        # if the result set is dirty, delete any attributes
        if rs.isDirty():
            for k in g.attrs.keys():
                del g.attrs[k]

        # if the result set's type has changed, delete any existing datasets
        if rs.isTypeChanged():
            if self.RESULTS_DATASET in g:
                del g[self.RESULTS_DATASET]
            if self.PENDINGRESULTS_DATASET in g:
                del g[self.PENDINGRESULTS_DATASET]
            rs.typechanged(False)        

        # write out all attributes (as strings)
        for k in rs.keys():
            v = rs[k]
            g.attrs.create(k, v, (1,), h5py.string_dtype())

        if rs.numberOfResults() > 0:
            # ---- PART 1: write structure ---

            # create results table if there isn't one
            if self.RESULTS_DATASET not in g:
                # get the dtype of the result set
                dtype = rs.dtype()
                hdf5dtype = self._HDF5dtype(dtype)

                # create the results dataset
                g.create_dataset(self.RESULTS_DATASET, (self.DefaultDatasetSize,), maxshape=(None,), dtype=hdf5dtype)

            # get the HDF5 dataset associated with this result set
            ds = self._file[tag][self.RESULTS_DATASET]

            # write out the names of all the fields as attributes
            for d in [ Experiment.METADATA, Experiment.PARAMETERS, Experiment.RESULTS ]:
                ns = names[d]
                if ns is not None:
                    ds.attrs.create(d, ns, (len(ns),), h5py.string_dtype())

            # ---- PART 2: write results ---

            # ensure that the dataset is large enough to hold the result set,
            # expanding it if necessary
            if len(ds) != len(rs):
                ds.resize((len(rs),))

            # write out each result
            df = rs.dataframe()
            dfnames = rs.dtype().names
            for i in range(len(df.index)):
                # convert row in the results table to a line in the dataset
                res = df.loc[df.index[i]]
                entry = []
                for k in dfnames:
                    if k in [ Experiment.START_TIME, Experiment.END_TIME ] and isinstance(res[k], datetime):
                        # patch known datestamps ISO-format strings in metadata
                        dt = res[k].isoformat()
                        entry.append(dt)
                    else:
                        entry.append(res[k])

                # write out the row
                ds[i] = tuple(entry)

        # ---- PART 3: write pending results ---

        if self.numberOfPendingResults() == 0:
            if self.PENDINGRESULTS_DATASET in g:
                # table isn't needed any more, so delete it to keep things tidy
                del g[self.PENDINGRESULTS_DATASET]
        else:
            # create results dataset if there isn't one
            if self.PENDINGRESULTS_DATASET not in g:        
                # construct the HDF5 type of the pending results
                pdtype = rs.pendingdtype() 
                hdf5pdtype = self._HDF5dtype(pdtype)

                # create the pending results dataset
                g.create_dataset(self.PENDINGRESULTS_DATASET, (self.DefaultDatasetSize,), maxshape=(None,), dtype=hdf5pdtype)

            # get the pending results dataset
            pds = g[self.PENDINGRESULTS_DATASET]

            # match size to the pending results
            if len(pds) != rs.numberOfPendingResults():
                pds.resize((rs.numberOfPendingResults(),))

            # write out each pending result
            pdf = rs._pending
            if pdf is not None:
                pdfnames = names[Experiment.PARAMETERS]
                for i in range(len(pdf.index)):
                    res = pdf.loc[i]
                    entry = []
                    for k in pdfnames:
                        entry.append(res[k])
                    entry.append(res[ResultSet.JOBID])

                    # write out the row
                    pds[i] = tuple(entry)

        # mark the result set as now clean
        rs.dirty(False)

    def _read(self, tag : str):
        '''Read the given result set into memory.

        :param tag: the result set tag'''
        rs = self.resultSet(tag)
        names = dict()
        g = self._file[tag]

        # read the names of all the fields and all the attributes
        for k in g.attrs.keys():
            rs[k] = g.attrs[k]

  
        if self.RESULTS_DATASET in g:   
            # ---- PART 1: read structure ---

            # get the HDF5 dataset associated with this result set
            ds = self._file[tag][self.RESULTS_DATASET]

            # read the names of all the fields and all the attributes
            for k in [ Experiment.METADATA, Experiment.PARAMETERS, Experiment.RESULTS ]:
                names[k] = list(ds.attrs[k])

            # ---- PART 2: read results ---

            # read each line of the dataset into the result set
            # sd: this uses the results dict API and so is quite wasteful
            for i in range(len(ds)):
                entry = list(ds[i])
                rc = Experiment.resultsdict()
                j = 0
                for d in [ Experiment.METADATA, Experiment.PARAMETERS, Experiment.RESULTS ]:
                    for k in names[d]:
                        if k in [ Experiment.START_TIME, Experiment.END_TIME ]:
                            # patch known datestamps to datetime objects
                            dt = dateutil.parser.parse(entry[j])
                            entry[j] = dt
                        rc[d][k] = entry[j]
                        j += 1
                self.addResult(rc, tag)

        if self.PENDINGRESULTS_DATASET in g:   
            # ---- PART 3: read pending results ---

            # get the pending results dataset
            pds = self._file[tag][self.PENDINGRESULTS_DATASET]

            # extract the parameter names, dropping the job id
            names[Experiment.PARAMETERS] = list(pds.dtype.names)
            names[Experiment.PARAMETERS].remove(ResultSet.JOBID)

            # read in each pending result
            # sd: this uses the results dict API and so is quite wasteful
            pdfnames = names[Experiment.PARAMETERS]
            for i in range(len(pds)):
                elements = list(pds[i])
                params = dict()
                for j in range(len(pdfnames)):
                    params[pdfnames[j]] = elements[j]
                jobid = elements[-1]                      # job id must be the last column!

                # record the pending result
                self.addPendingResult(params, jobid, tag)

        # mark the result set as clean
        rs.dirty(False)
        rs.typechanged(False)

    def _save(self):
        '''Save all dirty result sets. These are written out completely.'''
        for tag in self.resultSets():
            rs = self.resultSet(tag)
            if rs.isDirty():
                # result set has changed since it was created, loaded, or last saved
                self._write(tag)

        # write out the housekeeping information for the notebook
        meta = self._file.attrs
        meta[self.CURRENT] = self.resultSetTag(self.current())

    def _load(self):
        '''Load the notebook and all result sets.'''

        # read the tags of all result sets and create empty sets for them
        tags = list(self._file.keys())
        for tag in tags:
            # create an empty result set to hold this dataset
            self.addResultSet(tag)

            # read the result set in
            self._read(tag)

        # read the current result set and select it
        c = self._file.attrs[self.CURRENT]
        super(HDF5LabNotebook, self).select(c)

        # read other attributes
        self._description = self._file.attrs[self.DESCRIPTION]

    def _HDF5dtype(self, dtype : numpy.dtype) -> numpy.dtype:
        '''Patch a `numpy` dtype into its HDF5 equivalent.

        :param dtype: the numpy dtype
        :returns: the HDF5 dtype'''
        elements = []
        for k in dtype.names:
            t = dtype.fields[k][0]
            if t.kind in ['S', 'U']:
                # h5py can't handle Python strings but has its own dtype for them
                t = h5py.string_dtype()
                #print('Patched string {k}'.format(k=k))
            elements.append((k, t))
        return numpy.dtype(elements)


    # ---------- Context manager protocol ----------

    @contextmanager
    def open(self):
        '''Open and close the underlying file using a ``with`` block.'''
        try:
            # open the underlying file
            # sd: strictly unnecessary as the operations all open as required
            self._open()
            yield self
        finally:
            # commit any changes and close the file
            self.commit()


