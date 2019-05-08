# Simulation "lab notebook" for collecting results, JSON version
#
# Copyright (C) 2016 Simon Dobson
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

import os
import json
import numpy
from datetime import datetime
import dateutil.parser
import types


class MetadataEncoder(json.JSONEncoder):
    """Add support for encoding Python datetime objects within
    JSON objects, using the standard ISO string representation.
    (Plus a few other minor tweaks to get things to work more smoothly.)"""

    def default( self, o ):
        """If o is a datetime object, convert it to an ISO string. If it is an
        exception, convert it to a string. If it is a numpy int, coerce it to
        a Python int.

        :param o: the field to serialise
        :returns: a string encoding of the field"""
        if isinstance(o, datetime):
            # date/time, return an ISO formatted string
            return o.isoformat()
        else:
            if isinstance(o, Exception):
                # exception, stringify it
                return str(o)
            else:
                if isinstance(o, numpy.integer):
                    # numpy ints inherit differently between Python 2 and 3
                    # see https://bugs.python.org/issue24313
                    return int(o)
                else:
                    # everything else, pass through
                    return super(MetadataEncoder, self).default(o)


class JSONLabNotebook(epyc.LabNotebook):
    """A lab notebook that persists intself to a JSON file. This is
    the most basic kind of persistent notebook, readable by
    virtually any tooling.

    Using JSON presents some disadvantages, as not all types can be
    represented. Specifically, exceptions from the metadata of failed
    experiments (with the :attr:`Experiment.EXCEPTION`)
    will be saved as strings (for the exception).
    We also need to convert `datetime` objects to ISO-format strings
    when saving.
    """

    def __init__( self, name, create = False, description = None ):
        """Create a new JSON notebook, using the notebook's name
        as the JSON file. If this file exists, it will be opened
        and loaded unless create is True, in which case it will
        be erased.

        :param name: JSON file to persist the notebook to
        :param create: if True, erase existing file (defaults to False)
        :param description: free text description of the notebook"""
        super(epyc.JSONLabNotebook, self).__init__(name, description)

        # check for the file already existing
        if os.path.isfile(self.name()):
            # file exists, do we load it or create into it?
            if create:
                # empty the file
                with open(self.name(), 'w') as f:
                    f.write('')

                # preserve any description we were passed
                self._description = description
            else:
                # load notebook from file
                self._load(self.name())

    def isPersistent( self ):
        """Return True to indicate the notebook is persisted to a JSON file.

        :returns: True"""
        return True

    def commit( self ):
        """Persist to disc."""
        self._save(self.name())
        
    def _load( self, fn ):
        """Retrieve the notebook from the given file.

        :param fn: the file name"""

        # if file is empty, create an empty notebook
        if os.path.getsize(fn) == 0:
            self._description = None
            self._results = dict()
            self._pending = dict()
        else:
            # load the JSON object
            with open(fn, "r") as f:
                s = f.read()

                # parse back into appropriate variables
                j = json.loads(s)
                self._description = j['description']
                self._pending = dict(j['pending'])
                self._results = j['results']

                # perform any post-load patching
                self.patch()

    def _patchDatetimeMetadata( self, res, mk ):
        """Private method to patch an ISO datetime string to a datetime object
        for metadata key mk.

        :param res: results dict
        :param mk: metadata key"""
        t = res[epyc.Experiment.METADATA][mk]
        res[epyc.Experiment.METADATA][mk] = dateutil.parser.parse(t)
        
    def patch( self ):
        """Patch the results dict. The default processes the :attr:`Experiment.START_TIME`
        and :attr:`Experiment.END_TIME` metadata fields back into Python `datetime` objects
        from ISO strings. This isn't strictly necessary, but it makes notebook
        data structure more Pythonic."""

        for k in self._results.keys():
            ars = self._results[k]
            for res in ars:
                if isinstance(res, dict) and res[epyc.Experiment.METADATA][epyc.Experiment.STATUS]:
                    # a successful, non-pending result, patch its timing metadata
                    self._patchDatetimeMetadata(res, epyc.Experiment.START_TIME)
                    self._patchDatetimeMetadata(res, epyc.Experiment.END_TIME)

    def _save( self, fn ):
        """Persist the notebook to the given file.

        :param fn: the file name"""

        # create JSON object
        j = json.dumps({ 'description': self.description(),
                         'pending': self._pending,
                         'results': self._results },
                       indent = 4,
                       cls = MetadataEncoder)

        # write to file
        with open(fn, 'w') as f:
            f.write(j)
            

    
