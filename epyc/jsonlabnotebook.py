# Simulation "lab notebook" for collecting results, JSON version
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

import os
import json
import re
import logging
import numpy
from datetime import datetime
import dateutil.parser
from epyc import Logger, LabNotebook, Experiment, PackageContactInfo
from typing import Any, Dict


logger = logging.getLogger(Logger)


class MetadataEncoder(json.JSONEncoder):
    """Add support for encoding Python datetime objects within
    JSON objects, using the standard ISO string representation.
    (Plus a few other minor tweaks to get things to work more smoothly.)"""

    def default(self, o: Any) -> Any:
        """If o is a datetime object, convert it to an ISO string. If it is an
        exception, convert it to a string. If it is a numpy int, coerce it to
        a Python int.

        :param o: the field to serialise
        :returns: a string encoding of the field"""
        if isinstance(o, datetime):
            # date/time, return an ISO formatted string
            return o.isoformat()
        elif isinstance(o, Exception):
            # exception, stringify it
            return str(o)
        elif isinstance(o, numpy.integer):
            # numpy ints inherit differently between Python 2 and 3
            # see https://bugs.python.org/issue24313
            return int(o)
        elif isinstance(o, numpy.bool_):
            # numpy's bool_ type, cast it
            return bool(o)
        else:
            # everything else, pass through
            return super(MetadataEncoder, self).default(o)


class JSONLabNotebook(LabNotebook):
    '''A lab notebook that persists intself to a JSON file. This is
    the most basic kind of persistent notebook, readable by
    virtually any tooling.

    Using JSON presents some disadvantages, as not all types can be
    represented. Specifically, exceptions from the metadata of failed
    experiments (with :attr:`Experiment.EXCEPTION`) will be saved as strings.
    We also need to convert `datetime` objects to ISO-format strings
    when saving.

    :param name: JSON file to persist the notebook to
    :param create: if True, erase existing file (defaults to False)
    :param description: free text description of the notebook
    '''

    # Structure of the file
    VERSION = 'version'                              #: Tag for version number (missing for v1).

    def __init__(self, name: str, create: bool = False, description: str = None):
        super().__init__(name, description)

        # check for the file already existing
        if os.path.isfile(name):
            # file exists, do we load it or create into it?
            if create:
                self._create(name)
            else:
                self._load(name)

                # use the description we were given, if there is one
                if description is not None:
                    self.setDescription(description)

    def isPersistent(self) -> bool:
        """Return True to indicate the notebook is persisted to a JSON file.

        :returns: True"""
        return True

    def commit(self):
        """Persist to disc."""
        self._save(self.name())

    def _create(self, fn: str):
        '''Create an empty JSON file for this notebook.

        :param fn: the file name'''
        with open(fn, 'w') as f:
            f.write('')

    def _load(self, fn: str):
        """Retrieve the notebook from the given file.

        :param fn: the file name"""
        if os.path.getsize(fn) > 0:
            with open(fn, "r") as f:
                # load the JSON object
                s = f.read()
                j = json.loads(s)

                # check version
                if self.VERSION in j:
                    # we have a version string, check it's ours
                    v = j[self.VERSION]
                    if v == '2':
                        self._newload(j)
                    else:
                        raise Exception('Unhandled JSON file format {v}'.format(v=v))
                else:
                    # no version string, do the old-style load
                    logger.warning('Version 1 JSON format, notebook may have import errors')
                    self._oldload(j)

    def _oldload(self, j: Dict[str, Any]):
        '''Load an old-format file.

        In this format, all results were held in dicts keyed by a key synthesised from the
        parameter names and values. Pending results were held as a mapping from job ids
        to these synthetic keys.

        :param j: the old-style JSON object'''

        # description
        self.setDescription(j['description'])

        # results
        # held as mapping from key to list of results dicts for same parameters
        for k in j['results]']:
            rcs = j['results'][k]
            for rc in rcs:
                meta = rc[Experiment.METADATA]
                for k in meta:
                    if k in [ Experiment.START_TIME, Experiment.END_TIME ]:
                        meta[k] = dateutil.parser.parse(meta[k])    # patch ISO-format strings to datetime objects
                self.addResult(rc)

        # pending results
        # held as mapping from job id to key, which need to be unpacked to retrieve the actual parameters
        # key held as string containing a sequence of of "<name>:[[<value>]];" for each parameter
        # sd: which idiot decided '[[...]]' was good bracketing???...
        pattern = re.compile('([a-zA-Z0-9\-\.]+)=\[\[([^\]]+)\]\]')
        pendings = dict(j['pending'])
        for jobid in pendings:
            key = pendings[jobid]

            # convert key to params
            params = dict()
            ps = key.split(';')
            for p in ps[0:-1]:      # terminating ; needs to be ignored
                m = pattern.match(p)
                n = m.group(1)
                v = m.group(2)
                if n in [ Experiment.START_TIME, Experiment.END_TIME ]:
                    v = dateutil.parser.parse(v)    # patch ISO-format strings to datetime objects
                params[n] = v
            self.addPendingResult(params, jobid)

    def _newload(self, j: Dict[str, Any]):
        '''Load a new-format file.

        In this format we save everything as dicts, nested or otherwise.

        :param j: the JSON object'''

        # notebook-level metadata
        self.setDescription(j['description'])
        currentTag = j['current']

        # result sets
        for tag in j['resultsets']:
            rs = self.addResultSet(tag)
            res = j['resultsets'][tag]

            # attributes
            locked = False
            for k in res.keys():
                if k == 'results':
                    # results, deal with them next
                    pass
                elif k == 'description':
                    # description handled separately
                    rs.setDescription(res[k])
                elif k == 'locked':
                    # locked flag
                    locked = res[k]
                else:
                    rs[k] = res[k]

            # results
            rcs = res['results']
            for rc in rcs:
                meta = rc[Experiment.METADATA]
                for k in meta:
                    if k in [Experiment.START_TIME, Experiment.END_TIME]:
                        try:
                            # patch ISO-format strings to datetime objects
                            meta[k] = dateutil.parser.parse(meta[k])
                        except:
                            # leave unchanged
                            pass
                self.addResult(rc, tag=tag)

            # pending results
            pendings = res['pending-results']
            for jobid in pendings:
                params = dict(pendings[jobid])
                self.addPendingResult(params, jobid, tag=tag)

            # lock the result set if flagged
            if locked:
                rs.finish()

        # select the correct result set
        self.select(currentTag)

        # lock the notebook if needed
        if j['locked']:
            self.finish()

    def _save(self, fn: str):
        """Persist the notebook to the given file. Note that, while we can load
        both old and new formats, we only save in the new format.

        :param fn: the file name"""

        # result sets
        rsrcs = {}
        for tag in self.resultSets():
            rs = self.resultSet(tag)

            # results (as nested results dicts)
            rsres = {}
            rsres['results'] = list(rs.results())

            # pending results
            pending = {}
            for jobid in rs.pendingResults():
                params = rs.pendingResultParameters(jobid)
                pending[jobid] = params
            rsres['pending-results'] = pending

            # attributes
            for k in rs.keys():
                rsres[k] = rs[k]

            # description
            rsres['description'] = rs.description()

            # lock
            rsres['locked'] = rs.isLocked()

            # store the whole result set
            rsrcs[tag] = rsres

        # create the JSON object
        j = json.dumps({'creator': PackageContactInfo,
                        'version': '2',
                        'description': self.description(),
                        'current': self.currentTag(),
                        'locked': self.isLocked(),
                        'resultsets': rsrcs },
                       indent=4,
                       cls=MetadataEncoder)

        # write to file
        with open(fn, 'w') as f:
            f.write(j)
