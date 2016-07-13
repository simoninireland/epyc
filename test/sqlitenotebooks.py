# Tests of Sqlite notebooks
#
# Copyright (C) 2016 Simon Dobson
# 
# Licensed under the GNU General Public Licence v.2.0
#

from epyc import *

import unittest
import os
from tempfile import NamedTemporaryFile


class SqlliteLabNotebookTests(unittest.TestCase):

    def testCreateDatabaseInMemory( self ):
        '''Test creation of notebook using SQLite database in memory'''
        db = SqliteLabNotebook('test')
        self.assertFalse(db.isPersistent())
        self.assertEqual(db.name(), 'test')

    def testCreateDatabase( self ):
        '''Test creation of notebook using SQLite database in a file'''
        tf = NamedTemporaryFile()
        tf.close()
        fn = tf.name
        
        db = SqliteLabNotebook('test', fn)
        self.assertTrue(db.isPersistent())
        self.assertEqual(db.name(), 'test')
        self.assertTrue(os.path.isfile(fn))
        os.remove(fn)
