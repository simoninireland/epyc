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

from epyc import ResultSet, Experiment, LabNotebook
import os
import sys
import h5py
import numpy
from datetime import datetime
from pandas import DataFrame
import dateutil.parser


class HDF5LabNotebook(LabNotebook):
    '''A lab notebook that persists itself to an HDF5 file.
    `HDF5 <https://www.hdfgroup.org/>`_  is a very common format
    for sharing large scientific datasets, allowing ``epyc`` to interoperate
    with a larger toolchain. This notebook also only loads
    each :term:`result set` on demand, allowing ``epyc`` to handle
    far larger datasets than can be held in memory (although each
    individual result set is loaded in its entirety).

    Python types have a fairly straightforward mapping to HDF5 types,
    and ``epyc`` has a default type mapping for them. You can however take control
    and specify the mapping for each element in a results dict. Note that
    the limitations of HDF5's types mean that some values may have
    different types when read than when acquired. (See :ref:`hdf5-type-management`
    for details.)

    :param name: HDF5 file to persist the notebook to
    :param create: (optional) if True, erase any existing file (defaults to False)
    :param description: (optional) free text description of the notebook 
    '''

    # Tuning parameters
    DefaultDatasetSize = 10             #: Default initial size for a new HDF5 dataset.
    RetainResultSets = False            #: If True, retain in memory any result sets read; if False, only retain the current result set. 
    TypeMapping = { int: numpy.int64, 
                    float: numpy.float64,
                    complex: numpy.complex128,
                    bool: numpy.bool,
                    str: h5py.string_dtype(),
                    datetime: h5py.string_dtype(),
                    Exception: h5py.string_dtype(),
                  }                     #: Default type mapping from Python types to HDF5 types.

    # Dataset structure
    RESULTS_DATASET = 'results'         #: Name of results dataset within the HDF5 group for a result set.
    PENDINGRESULTS_DATASET = 'pending'  #: Name of pending results dataset within the HDF5 group for a result set.

    # Metadata for the datasets

    # Metadata for the notebook
    DESCRIPTION = 'description'         #: Attribute holding the notebook description.
    CURRENT = 'current'                 #: Attribute holding the tag of the current result set.


    def __init__(self, name, create=False, description=''):
        super(HDF5LabNotebook, self).__init__(name, description)

        self._file = None             # file handle for underlying HDF5 file
        self._group = None            # group associated with the current result set
        self._dtype = dict()          # result set to dtype

        # check for the file already existing
        if os.path.isfile(name):
            # file exists, do we load it or create into it?
            if create:
                # delete and re-create the file
                self._create(name, description)
                
            else:
                # load notebook from file
                self._open()
                self._load()
                self._close()
        else:
            # no file, create it
            self._create(name, description)


    # ---------- Persistence ----------

    def isPersistent( self ):
        """Return True to indicate the notebook is persisted to an HDF5 file.

        :returns: True"""
        return True

    def commit( self ):
        """Persist any changes in the result sets in the notebook to disc."""
        self._open()
        self._save()
        self._close()


    # ---------- Managing result sets ----------


    # ---------- Protocol for managing the HDF5 file----------
    
    def _create(self, name, description):
        '''Create the HDF5 file to back this notebook.
        
        :param name: the filename
        :param description: the free text description of this notebook'''
        self._file = h5py.File(name, 'w')
        self._file.attrs[self.DESCRIPTION] = description
        self._description = description
        self._file.attrs[self.CURRENT] = self.DEFAULT_RESULTSET
        self._current = self.resultSet(self.DEFAULT_RESULTSET)

    def _open(self):
        '''Open the HDF5 file that backs this notebook.'''
        if self._file is None:
            self._file = h5py.File(self.name(), 'a')

    def _close(self):
        '''Close the underlying HDF5 file.'''
        if self._file is not None:
            self._file.close()
            self._file = None

    def _write(self, tag):
        '''Write the given result set to the file.

        :tag: the result set tag'''
        rs = self.resultSet(tag)
        names = rs.names()
        g = self._file[tag]

        if self.RESULTS_DATASET in g:
            # ---- PART 1: write structure ---

            # get the HDF5 dataset associated with this result set
            ds = self._file[tag][self.RESULTS_DATASET]

            # write out the names of all the fields as attributes
            for d in [ Experiment.METADATA, Experiment.PARAMETERS, Experiment.RESULTS ]:
                ds.attrs.create(d, list(names[d]), (len(names[d]),), h5py.string_dtype())

            # ---- PART 2: write results ---

            # ensure that the dataset is large enough to hold the result set,
            # expanding it if necessary
            if len(ds) != len(rs):
                ds.resize((len(rs),))

            # convert each result in the result set to an entry in the dataset
            df = rs.dataframe()
            dfnames = self._dtype[rs].names
            for i in range(len(df.index)):
                res = df.loc[df.index[i]]
                entry = []
                for k in dfnames:
                    # patch known datestamps ISO-format strings in metadata
                    if k in [ Experiment.START_TIME, Experiment.END_TIME ] and isinstance(res[k], datetime):
                        dt = res[k].isoformat()
                        entry.append(dt)
                    else:
                        entry.append(res[k])

                # write out the row
                ds[i] = tuple(entry)

        if self.PENDINGRESULTS_DATASET in g:
            # ---- PART 3: write pending results ---

            # get the pending results dataset
            pds = self._file[tag][self.PENDINGRESULTS_DATASET]

            # size to the pending results
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

    def _read(self, tag):
        '''Read the given result set into memory.

        :param tag: the result set tag'''
        rs = self.resultSet(tag)
        names = rs.names()
        g = self._file[tag]

        if self.RESULTS_DATASET in g:   
            # ---- PART 1: read structure ---

            # get the HDF5 dataset associated with this result set
            ds = self._file[tag][self.RESULTS_DATASET]

            # read the names of all the fields
            for d in [ Experiment.METADATA, Experiment.PARAMETERS, Experiment.RESULTS ]:
                names[d] = list(ds.attrs[d])

            # create the coresponding dtype
            dtype = self._file[tag][self.RESULTS_DATASET].dtype
            self._dtype[rs] = dtype

            # ---- PART 2: read results ---

            # read each line of the dataset into the result set
            # sd: should use a private API for this
            df = DataFrame()
            dfnames = self._dtype[rs].names
            for i in range(len(ds)):
                entry = list(ds[i])
                res = dict()
                for j in range(len(dfnames)):
                    # patch known datestamps to datetime objects
                    if dfnames[j] in [ Experiment.START_TIME, Experiment.END_TIME ]:
                        dt = dateutil.parser.parse(entry[j])
                        entry[j] = dt
                    res[dfnames[j]] = entry[j]
                df = df.append(res, ignore_index=True)
            rs._results = df

        if self.PENDINGRESULTS_DATASET in g:   
            # ---- PART 3: read pending results ---

            # get the pending results dataset
            pds = self._file[tag][self.PENDINGRESULTS_DATASET]

            # extract the parameter names, dropping the job id
            names[Experiment.PARAMETERS] = list(pds.dtype.names)
            names[Experiment.PARAMETERS].remove(ResultSet.JOBID)

            # read in each pending result
            pdfnames = names[Experiment.PARAMETERS]
            for i in range(len(pds)):
                elements = list(pds[i])
                params = dict()
                for j in range(len(pdfnames)):
                    params[pdfnames[j]] = elements[j]
                jobid = elements[-1]

                # record the pending result
                self.addPendingResult(params, jobid)

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
            rs = self.current()

            # read the result set in
            self._read(tag)

        # read the current result set and select it
        c = self._file.attrs[self.CURRENT]
        super(HDF5LabNotebook, self).select(c)

        # read other attributes
        self._description = self._file.attrs[self.DESCRIPTION]


    # ---------- Type management ----------

    def setResultSetType(self, rs, dtype):
        '''Use the given dtype to represent the results of the given result set
        in HDF5. This allows precise control of the type mapping used: if none is
        provided then one will be inferred using :meth:`inferType` when the first
        results appear. The types can't be re-set once set or inferred.

        :param rs: the result set
        :param dtype: the dtype of results'''
        if rs in self._dtype.keys():
            raise Exception('Already have a dtype for result set {t}'.format(t=self.resultSetTag(rs)))
        self._dtype[rs] = dtype

    def inferType(self, rc):
        '''Infer the HDF5 dataset element type (or dtype) of the given results dict.

        This method will be called automatically if no explicit dtype has been provided 
        for the result set by a call to :meth:`setResultSetType`.

        :param rc: the results dict
        :returns: the dtype'''

        # construct the canonical list of element names
        names = []
        for d in [ Experiment.METADATA, Experiment.PARAMETERS, Experiment.RESULTS ]:
            ns = list(rc[d].keys())
            ns.sort()
            names.extend(ns)

        # infer the types associated with each element using the type mapping
        types = dict()
        for d in [ Experiment.METADATA, Experiment.PARAMETERS, Experiment.RESULTS ]:
            for k in rc[d].keys():
                try:
                    t = type(rc[d][k])
                    types[k] = self.TypeMapping[t]
                except Exception:
                    raise Exception('No HDF5 mapping for type {t}'.format(t=t))

        # form the dtype
        elements = []
        for k in names:
            elements.append((k, types[k]))
        dtype = numpy.dtype(elements)
        return dtype

    def inferPendingResultsType(self, params):
        '''Infer the HDF5 dataset element type (or dtype) of the pending results of
        given dict of experimental parameters. This is essentially the same operation as
        :meth:`inferType` but restricted to experimental parameters and including
        a string job identifier.

        :param params: the experimental parameters
        :returns: the pending results dtype'''

        # construct the canonical list of element names
        names = list(params.keys()).copy()
        names.sort()

        # infer the types associated with each element using the type mapping
        types = dict()
        for k in names:
            try:
                t = type(params[k])
                types[k] = self.TypeMapping[t]
            except Exception:
                raise Exception('No HDF5 mapping for type {t}'.format(t=t))

        # form the dtype
        elements = []
        for k in names:
            elements.append((k, types[k]))
        elements.append((ResultSet.JOBID, h5py.string_dtype()))
        pdtype = numpy.dtype(elements)
        return pdtype


    # ---------- Adding results ----------

    def addResult(self, rc):
        '''Use the first-appearing results to add the necessary file
        structure. Note that this doesn't write results to the file, it simply
        makes sure we've set up the structure.

        :param rc: the result dict'''
        self._open()
        rs = self.current()
        tag = self.resultSetTag(rs)

        # create group for this result set if its missing
        if tag not in self._file:
            g = self._file.create_group(tag)
        else:
            g = self._file[tag]

        # create results table if there isn't one
        if self.RESULTS_DATASET not in g:        
            # construct the HDF5 type of the results dict if one hasn't been provided already
            if rs not in self._dtype.keys():
                # infer the dtype for results
                dtype = self.inferType(rc)
                self._dtype[rs] = dtype
            else:
                dtype = self._dtype[rs]

            # create the results dataset
            g.create_dataset(self.RESULTS_DATASET, (self.DefaultDatasetSize,), maxshape=(None,), dtype=dtype)

        # add the result
        super(HDF5LabNotebook, self).addResult(rc)


    # ---------- Managing pending results ----------

    def addPendingResult(self, params, jobid):
        '''Use the first-appearing pending results to add the necessary file
        structure. Note that this doesn't write results to the file, it simply
        makes sure we've set up the structure.

        :param params: the experiment parameters
        :param jobid: the job identifier'''
        self._open()
        rs = self.current()
        tag = self.resultSetTag(rs)

        # create group for this result set if its missing
        if tag not in self._file:
            g = self._file.create_group(tag)
        else:
            g = self._file[tag]

        # create results table if there isn't one
        if self.PENDINGRESULTS_DATASET not in g:        
            # construct the HDF5 type of the pending results
            pdtype = self.inferPendingResultsType(params)

            # create the pending results dataset
            g.create_dataset(self.PENDINGRESULTS_DATASET, (self.DefaultDatasetSize,), maxshape=(None,), dtype=pdtype)

        # add the result
        super(HDF5LabNotebook, self).addPendingResult(params, jobid)



