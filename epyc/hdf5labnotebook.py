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

from epyc import ResultSet, Experiment, LabNotebook, NotebookVersionException, PackageContactInfo
import os
import h5py                    # type: ignore
import numpy                   # type: ignore
from datetime import datetime
from pandas import DataFrame   # type: ignore
from dateutil.parser import parse
from requests import get
from requests.exceptions import MissingSchema
from tempfile import NamedTemporaryFile
import sys
if sys.version_info >= (3, 8):
    from typing import Final, Any
else:
    # backwards compatibility with Python 35, Python36, and Python37 
    from typing import Any
    from typing_extensions import Final

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

    The name of the notebook can be a file or a URL. Only files can be created
    or updated: if a URL is provided then the notebook will be read and
    immediately marked as locked. This implies that ``create=True`` won't
    work in conjunction with URLs.

    .. important ::

        Note that because of the design of the ``requests`` library used for
        handling URLs, using a ``file:``-schema URL will result in an exception
        being raised. Use filenames for accessing files.

    :param name: HDF5 file or URL backing the notebook
    :param create: (optional) if True, erase any existing file (defaults to False)
    :param description: (optional) free text description of the notebook 
    '''

    # Latest file format, defining how a notebook is laid out within the HDF5 file
    Version : Final[str] = '1'                       #: File structure version number used by this notebook.

    # Tuning parameters
    DefaultDatasetSize : int = 10                    #: Default initial size for a new HDF5 dataset.

    # Dataset structure
    RESULTS_DATASET : Final[str] = 'results'         #: Name of results dataset within the HDF5 group for a result set.
    PENDINGRESULTS_DATASET : Final[str] = 'pending'  #: Name of pending results dataset within the HDF5 group for a result set.

    # Metadata for the notebook and/or result sets
    CREATOR : Final[str] = 'creator'                 #: Attribute holding library information and URL.
    VERSION : Final[str] = 'version'                 #: Attribute holding the version of file structure used.
    DESCRIPTION : Final[str] = 'description'         #: Attribute holding the notebook and result set descriptions.
    CURRENT : Final[str] = 'current-resultset'       #: Attribute holding the tag of the current result set.
    LOCKED : Final[str] = 'locked'                   #: Attribute flagging as result set or notebook as being locked to further changes.

    def __init__(self, name : str, create : bool =False, description : str =None):
        # create an empty file structure
        self._file : h5py.File = None          # HDF5 file for underlying data
        self._group : h5py.Group = None        # group associated with the current result set

        # if we're looking at a URL, some behaviour is different
        try:
            # attempt to open the name as a URL
            response = get(name)

            # if we get here, the name is a URL
            self._isRemote = True
        except MissingSchema:
            # name is a file
            self._isRemote = False

        # check for file needing creation
        created = (not self._isRemote) and (create or not os.path.isfile(name))
        if created:
            self._create(name)                

        # perform the normal initialisation
        super(HDF5LabNotebook, self).__init__(name, description)

        if not created:
            # load notebook from file if it wasn't newly created
            self._open()
            self._load()
            self._close()

            # use the description we were given, if there is one
            if description is not None:
                self.setDescription(description)


    # ---------- Persistence ----------

    def isPersistent(self) -> bool:
        """Return True to indicate the notebook is persisted to an HDF5 file.

        :returns: True"""
        return True

    def commit(self):
        """Persist any changes in the result sets in the notebook to disc."""
        if not self.isLocked():
            self._open()
            self._save()
            self._close()

    def _commit(self):
        '''If we're finishing, commit regardless of the lock status.'''
        self._open()
        self._save()
        self._close()


    # ---------- Managing result sets ----------

    def addResultSet(self, tag : str, description : str =None) -> ResultSet:
        '''Add the necessary structure to the underlying file when creating the
        new result set. This ensures that, even if no results are added,
        there will be structure in the persistent store to indicate that the result
        set was created.

        :param tag: the tag
        :param description: (optional) the description
        :returns: the result set'''
        rs = super(HDF5LabNotebook, self).addResultSet(tag, description)

        # add the appropriate group to the HDF5 file
        self._open()
        if tag not in self._file:
            self._file.create_group(tag)

        # mark the result set as being dirty to force a save
        rs.dirty()

        return rs


    # ---------- Protocol for managing the HDF5 file----------
    
    def _create(self, name : str):
        '''Create the HDF5 file to back this notebook.
        
        :param name: the filename
        :param description: the free text description of this notebook'''
        self._file = h5py.File(name, 'w')
        self._file.attrs[self.VERSION] = self.Version
        #self._current = self.resultSet(self.DEFAULT_RESULTSET)

    def _open(self):
        '''Open the HDF5 file that backs this notebook.'''
        if self._file is None:
            if self._isRemote:
                # open as a URL
                response = get(self.name())

                # slurp the contents into a local temp file
                tf = NamedTemporaryFile(delete=False)
                for chunk in response.iter_content(chunk_size=1024):
                    tf.write(chunk)
                tf.close()

                # open the file read-only
                self._file = h5py.File(tf.name, 'r')   # can only be read
            else:
                # open as a file 
                self._file = h5py.File(self.name(), 'a')

    def _close(self):
        '''Close the underlying HDF5 file.'''
        if self._file is not None:
            self._file.close()
            self._file = None

        # if we loaded from a URL, lock the notebook
        if self._isRemote:
            self.finish(commit=False)   # don't try to commit it when finishing

    def _write(self, tag : str):
        '''Write the given result set to the file.

        :tag: the result set tag'''
        rs = self.resultSet(tag)
        names = rs.names()
        g = self._file[tag]

        # delete any attributes
        for k in g.attrs.keys():
            del g.attrs[k]

        # if the result set's type has changed, delete any existing datasets
        if rs.isTypeChanged():
            if self.RESULTS_DATASET in g:
                del g[self.RESULTS_DATASET]
            if self.PENDINGRESULTS_DATASET in g:
                del g[self.PENDINGRESULTS_DATASET]

        # write out the description
        g.attrs.create(self.DESCRIPTION, rs.description(), dtype=h5py.string_dtype())

        # write out all attributes (as strings)
        for k in rs.keys():
            v = rs[k]
            g.attrs.create(k, self._asString(v), dtype=h5py.string_dtype())

        # write out the locked flag
        g.attrs.create(self.LOCKED, rs.isLocked(), dtype=numpy.bool)

        if rs.numberOfResults() > 0:
            # ---- PART 1: write structure ---

            # create results table if there isn't one
            if self.RESULTS_DATASET not in g:
                # get the dtype of the result set
                dtype = rs.dtype()
                hdf5dtype = self._HDF5dtype(dtype)

                # create the results dataset
                g.create_dataset(self.RESULTS_DATASET, (self.DefaultDatasetSize,), maxshape=(None,), dtype=hdf5dtype)

                # write out the names of all the fields as attributes
                for d in [ Experiment.METADATA, Experiment.PARAMETERS, Experiment.RESULTS ]:
                    ns = names[d]
                    if ns is not None:
                        g[self.RESULTS_DATASET].attrs.create(d, ns, dtype=h5py.string_dtype())

            # get the HDF5 dataset associated with this result set
            ds = g[self.RESULTS_DATASET]

            # ---- PART 2: write results ---

            # ensure that the dataset is large enough to hold the result set,
            # expanding it if necessary
            if len(ds) != len(rs):
                ds.resize((len(rs),))

            # write out each result
            df = rs.dataframe()
            dtype = rs.dtype()
            hdf5dtype = ds.dtype
            dfnames = dtype.names
            for i in range(len(df.index)):
                # get the row to write
                res = df.iloc[i]

                # convert row in the results table to a line in the dataset
                entry = []
                for k in dfnames:
                    if k in [ Experiment.START_TIME, Experiment.END_TIME ] and isinstance(res[k], datetime):
                        # patch known datestamps ISO-format strings in metadata
                        dt = res[k].isoformat()
                        entry.append(dt)
                    else:
                        et = h5py.check_vlen_dtype(hdf5dtype[k])
                        if et is None:
                            # "normal" type, pass through
                            entry.append(res[k])
                        elif et == str:
                            # string, convert
                            entry.append(self._asString(res[k]))
                        else:
                            # array of something
                            entry.append(numpy.array(res[k]))
    
                # write out the row
                ds[i] = tuple(entry)

        # ---- PART 3: write pending results ---

        if rs.numberOfPendingResults() == 0:
            if self.PENDINGRESULTS_DATASET in g:
                # table isn't needed any more, so delete it to keep things tidy
                del g[self.PENDINGRESULTS_DATASET]
        else:
            pdtype = rs.pendingdtype() 
            hdf5pdtype = self._HDF5dtype(pdtype)

            # create results dataset if there isn't one
            if self.PENDINGRESULTS_DATASET not in g:        
                # construct the HDF5 type of the pending results
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
                    res = pdf.iloc[i]
                    entry = []
                    for k in pdfnames:
                        if hdf5pdtype[k] == h5py.string_dtype():
                            entry.append(self._asString(res[k]))
                        else:
                            entry.append(res[k])
                    entry.append(res[ResultSet.JOBID])

                    # write out the row
                    pds[i] = tuple(entry)

        # mark the result set as now clean
        rs.dirty(False)
        rs.typechanged(False)

    def _read(self, tag : str):
        '''Read the given result set into memory.

        :param tag: the result set tag'''
        rs = self.resultSet(tag)
        names = dict()
        g = self._file[tag]

        # read the attributes, all treated as strings
        formats = None
        locked = False
        for k in g.attrs.keys():
            if k == self.DESCRIPTION:
                # description held separately from attributes
                rs.setDescription(str(g.attrs[self.DESCRIPTION]))
            elif k == self.LOCKED:
                # locked flag
                locked = g.attrs[self.LOCKED]
            else:
                rs[k] = self._asString(g.attrs[k])

        if self.RESULTS_DATASET in g:   
            # ---- PART 1: read structure ---

            # get the HDF5 dataset associated with this result set
            ds = self._file[tag][self.RESULTS_DATASET]

            # read the names of all the fields and all the attributes
            for k in [ Experiment.METADATA, Experiment.PARAMETERS, Experiment.RESULTS ]:
                if k in ds.attrs:
                    names[k] = list(ds.attrs[k])
                else:
                    names[k] = []   # no result fields (suggests any results so far have failed)

            # ---- PART 2: read results ---

            # read each line of the dataset into the result set
            # sd: this uses the results dict API and so is quite wasteful
            hdf5dtype = ds.dtype
            for i in range(len(ds)):
                entry = list(ds[i])
                rc = Experiment.resultsdict()
                j = 0
                for d in [ Experiment.METADATA, Experiment.PARAMETERS, Experiment.RESULTS ]:
                    for k in names[d]:
                        et = h5py.check_vlen_dtype(hdf5dtype[k])
                        if et == str:
                            # string, convert
                            entry[j] = self._asString(entry[j])
                        elif et is not None:
                            # array of something
                            entry[j] = numpy.array(entry[j])
                        if k in [ Experiment.START_TIME, Experiment.END_TIME ]:
                            try:
                                # patch known datestamps to datetime objects
                                dt = parse(entry[j])
                                entry[j] = dt
                            except:
                                # leave unchanged if we can't patch
                                pass
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
            pdfnames = list(pds.dtype.names)
            jobidcol = pdfnames.index(ResultSet.JOBID)
            for i in range(len(pds)):
                jobid = ''
                elements = list(pds[i])
                params = dict()
                for j in range(len(pdfnames)):
                    if j == jobidcol:
                        jobid = elements[j]
                    else:
                        params[pdfnames[j]] = elements[j]

                # some backends force strings, not bytes, for job ids
                if isinstance(jobid, bytes):
                    jobid = jobid.decode()

                # record the pending result
                self.addPendingResult(params, jobid, tag)

        # lock the result set if flagged 
        if locked:
            rs.finish()

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
        meta[self.CREATOR] = PackageContactInfo
        meta[self.VERSION] = self.Version
        meta[self.DESCRIPTION] = self.description()
        meta[self.CURRENT] = self.resultSetTag(self.current())
        meta[self.LOCKED] = self.isLocked()

    def _load(self):
        '''Load the notebook and all result sets.'''
        meta = self._file.attrs

        # version check
        v = meta[self.VERSION]
        if v != self.Version:
            # at present can't handle different file structure versions
            raise NotebookVersionException(self.Version, v)

        # read the tags of all result sets and create empty sets for them
        tags = list(self._file.keys())
        for tag in tags:
            # create an empty result set to hold this dataset
            self.addResultSet(tag)

            # read the result set in
            self._read(tag)

        # read the current result set and select it
        c = meta[self.CURRENT]
        super(HDF5LabNotebook, self).select(c)

        # read other attributes
        self._description = meta[self.DESCRIPTION]

        # lock if necessary
        if meta[self.LOCKED]:
            self.finish(commit=False)


    # ---------- Type conversion ----------

    def _HDF5simpledtype(self, dtype : numpy.dtype) -> numpy.dtype:
        '''Patch a simple ``numpy`` dtype to the formats available in HDF5.

        :param dtype: the ``numpy`` dtype
        :returns: the HDF5 dtype'''
        if dtype.kind in ['S', 'U']:
            # h5py can't handle Python strings but has its own dtype for them
            return h5py.string_dtype()
        #elif dtype.kind in ['O']:
        #    # object (probably numpy array), wrap as vlen
        #    return h5py.vlen_dtype(dtype)
        elif dtype.shape != ():
            # list, make into a vlen type
            return h5py.vlen_dtype(self._HDF5dtype(dtype.base))
        else:
            # leave unpatched
            return dtype

    def _HDF5dtype(self, dtype : numpy.dtype) -> numpy.dtype:
        '''Patch a ``numpy`` dtype into its HDF5 equivalent. This method
        handles structured types with named fields.

        :param dtype: the ``numpy`` dtype
        :returns: the HDF5 dtype'''
        if dtype.names is not None:
            # a structured dtype, unpack and patch all the fields
            elements = []
            for k in dtype.names:
                t = self._HDF5dtype(dtype.fields[k][0])
                elements.append((k, t))
            return numpy.dtype(elements)
        else:
            # a simple dtype, patch it
            return self._HDF5simpledtype(dtype)

    def _asString(self, o : Any) -> str:
        '''Coerce the given value to a string. This is needed to handle
        occasional (and Python-version-dependent) weirdness in the 
        representation of strings as raw sequences when going to and from
        HDF5. 

        :param o: the object
        :returns: the string'''
        if isinstance(o, bytes):
            return o.decode()
        elif isinstance(o, str):
            return o
        else:
            return str(o)
