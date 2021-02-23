# Container script for manipulating notebooks from the command line 
#
# Copyright (C) 2021 Simon Dobson
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
import sys
import re
import click
import epyc

notebook_resultset_rename_re = re.compile('^([\w/\.-]*):([\w/\.-]+)(=([\w/\.-]+))?$')

@click.group()
def cli():
    '''A command line interface (CLI) to epyc lab notebooks.'''
    pass

@cli.command()
@click.argument('notebook')
@click.option('-l/-s', '--long/--short', default=True, help='long/short form output')
def show(notebook, long):
    '''Show the structure of a notebook.

    The long form displays a human-readable summary of the result sets and their
    descriptions. The short form simply lists the result sets, one per line,
    in a form suitable for feeding to other commands. The default is the long form.'''
    
    # open the notebook
    try:
        nb = epyc.HDF5LabNotebook(name=notebook, create=False)
    except Exception as e:
        print(f"Can't open {notebook}: {e}", file=sys.stderr)
        sys.exit(1)
       
    # display the notebook's structure, in long or short form
    if long:
        # long form, print metadata about notebook
        click.echo('{desc}{locked}'.format(desc=nb.description(),
                                           locked=click.style(' (locked)', fg='red') if nb.isLocked() else ''))
        print()
    
        # iterate the result sets
        click.echo('Result sets:')
        tags = nb.resultSets()
        for tag in tags:
            rs = nb.resultSet(tag)
            desc = rs.description()
            click.echo(click.style(f'   {tag}', fg='red') + f': {desc}')
    else:
        # short form, just print result set tags
        print('\n'.join(nb.resultSets()))

@cli.command()
@click.argument('rss', nargs=-1)
@click.argument('dest', nargs=1)
@click.option('-v', '--verbose', count=True, help='Generate verbose output (repeat for extra verbosity)')
def copy(rss, dest, verbosity):
    '''Copy one or more result sets to the destination notebook.

    Result sets are specified as a triple [NOTEBOOK]:TAG[=NEWTAG] where NOTEBOOK
    is the name of a notebook, TAG is a result set tag within NOITEBOOK, and
    NEWTAG is a tag for the result set when it's copied to the destination (to
    avoid name clashes). If NOTEBOOK is omitted then the same notebook as the previous
    result set is used. if NEWTAG is omittedd then TAG is used for the destination
    result set as well'''

    # check we have result sets to copy
    if len(rss) == 0:
        print('No result sets to copy')
        exit(0)
    
    with epyc.HDF5LabNotebook(name=dest).open() as nb:
        # check that destination is not locked
        if nb.isLocked():
            print(f'Destination notebook {dest} is locked')
            sys.exit(1)

        # iterate through all result set specifiers
        fn = None
        tag = None
        newtag = None
        nb1 = None
        for spec in rss:
            # extract the parts from the specifier
            m = notebook_resultset_rename_re.match(spec)
            if m is None:
                print(f"Invalid result set specifier '{spec}'", file=sys.stderr)
                exit(1)
            if m[1] == '':
                # no notebook, can we use the previous one?
                if fn is None:
                    # no notebook default
                    print(f"No notebook for result set specifier '{spec}'", file=sys.stderr)
                    exit(1)
            else:
                # notebook replaces the current one
                nb1 = None
                fn = m[1]
                tag = m[2]
            if m[4] is None:
                # no rename, use the same tag
                newtag = tag
            else:
                # result set will be renamed when copied
                newtag = m[4]

            # load the notebook if it's not already loaded 
            if nb1 is None:
                nb1 = epyc.HDF5LabNotebook(fn)

            # sanity check the result sets
            if tag not in nb1.resultSetTags():
                print(f"No result set '{tag}' in {fn}", file=sys.stderr)
                sys.exit(1)
            if newtag in nb.resultSetTags():
                print(f"Result set '{tag}' already exists in {dest}", file=sys.stderr)
                sys.exit(1)
            
            # copy the result set
            if verbosity == 1:
                click.echo(click.style('#', fg='green'), end='')
            rs1 = nb1.resultSet(tag)
            rs = nb.addResultSet(newtag)
            for rc in rs1.results():
                if verbosity == 1:
                    print('.', end='')
                rs.addResult(rc)    
            if verbosity == 1:
                print('')

            
if __name__ == '__main__':
    cli()
    
