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

notebook_re = re.compile('^([\w/\.-]+)$')
notebook_resultset_re = re.compile('^([\w/\.-]+)?:([\w/\.-]+)$')
notebook_opt_resultset_re = re.compile('^([\w/\.-]+)(:([\w/\.-]+))?$')
notebook_resultset_rename_re = re.compile('^([\w/\.-]+)?:([\w/\.-]+)(=([\w/\.-]+))?$')

@click.group()
def cli():
    '''A command line interface (CLI) to epyc lab notebooks.'''
    pass

@cli.command()
@click.argument('notebook')
@click.option('-l/-s', '--long/--short', default=True, help='long/short form output')
def show(notebook, long):
    '''Show the structure of a notebook.

    The long form displays a human-readable summary of the result sets
    and their descriptions. The short form simply lists the result
    sets, one per line, in a form suitable for feeding to other
    commands. The default is the long form. The current result set is
    starred.

    '''

    # open the notebook
    try:
        nb = epyc.HDF5LabNotebook(name=notebook, create=False)
    except Exception as e:
        print(f"Can't open {notebook}: {e}", file=sys.stderr)
        sys.exit(1)

    # display the notebook's structure, in long or short form
    if long:
        # long form, print metadata about notebook
        desc=nb.description()
        click.echo(f'{desc}' +
                   (click.style(' (locked)', fg='red') if nb.isLocked() else ''))
        click.echo()

        # iterate the result sets
        currentTag = nb.currentTag()
        click.echo('Result sets:')
        for tag in nb.resultSets():
            # show result set global summary
            rs = nb.resultSet(tag)
            n = len(rs)
            desc = rs.description()
            click.echo(click.style(f'  {tag}', fg='green') +
                       (click.style('(*)', fg='yellow') if tag == currentTag else '') +
                       f' [{n}]: {desc}' +
                       (click.style(' (locked)', fg='red') if nb.isLocked() else ''))

            # show any attributes
            for key in rs.keys():
                value = rs[key]
                click.echo(click.style(f'    {key}', fg='green') + f': {value}')
    else:
        # short form, just print result set tags
        print('\n'.join(nb.resultSets()))

@cli.command()
@click.argument('rss', nargs=-1)
@click.argument('dest', nargs=1)
@click.option('-v', '--verbose', count=True, help='Generate verbose output (repeat for extra verbosity)')
@click.option('-n', '--pretend', is_flag=True, help="Check validity but don't copy anything")
def copy(rss, dest, verbose, pretend):
    '''Copy one or more result sets to the destination notebook.

    Result sets are specified as a triple [NOTEBOOK]:TAG[=NEWTAG]
    where NOTEBOOK is the name of a notebook, TAG is a result set tag
    within NOTEBOOK, and NEWTAG is a tag for the result set when it's
    copied to the destination (to avoid name clashes). If NOTEBOOK is
    omitted then the same notebook as the previous result set is
    used. If NEWTAG is omitted then TAG is used for the destination
    result set as well

    '''

    # check we have result sets to copy
    if len(rss) == 0:
        print('No result sets to copy')
        exit(0)

    # iterate through all result set specifiers
    copies = []
    fn = None
    tag = None
    newtag = None
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
            fn = m[1]
            tag = m[2]
        if m[4] is None:
            # no rename, use the same tag
            newtag = tag
        else:
            # result set will be renamed when copied
            newtag = m[4]

        # save the decomposed specifier
        copies.extend([(fn, tag, newtag)])

    # open the destination
    with epyc.HDF5LabNotebook(name=dest).open() as nb:
        # check that destination is not locked
        if nb.isLocked():
            print(f'Destination notebook {dest} is locked')
            sys.exit(1)

        # traverse the copy specifiers
        ofn = None
        nb1 = None
        for (fn, tag, newtag) in copies:
            # change notebooks if needed
            if ofn != fn:
                if nb1 is not None:
                    # commit the previous notebook
                    nb1.commit()

                # load the notebook if it's not already loaded
                nb1 = epyc.HDF5LabNotebook(fn)
            ofn = fn

            # sanity check the result sets
            if tag not in nb1.resultSets():
                print(f"No result set '{tag}' in {fn}", file=sys.stderr)
                sys.exit(1)
            if newtag in nb.resultSets():
                print(f"Result set '{newtag}' already exists in {dest}", file=sys.stderr)
                sys.exit(1)

            if verbose > 0:
                click.echo('Copied ' +
                           click.style(f'{fn}:{tag}', fg='green') +
                           ' -> ' +
                           click.style(f'{dest}:{newtag}', fg='green'))
            if not pretend:
                # copy the result set
                rs1 = nb1.resultSet(tag)
                rs = nb.addResultSet(newtag)
                for rc in rs1.results():
                    rs.addSingleResult(rc)

@cli.command()
@click.argument('rss', nargs=-1)
@click.option('-v', '--verbose', count=True, help='Generate verbose output (repeat for extra verbosity)')
@click.option('-n', '--pretend', is_flag=True, help="Check validity but don't copy anything")
def remove(rss, verbose, pretend):
    '''Remove one or more result sets from notebook(s).

    Result sets are specified as a pair [NOTEBOOK]:TAG where
    NOTEBOOK is the name of a notebook and TAG is a result set tag
    within NOTEBOOK. If NOTEBOOK is omitted then the same notebook as
    the previous result set is used.

    '''

    # iterate through all result set specifiers
    copies = []
    fn = None
    tag = None
    for spec in rss:
        # extract the parts from the specifier
        m = notebook_resultset_re.match(spec)
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
            fn = m[1]
            tag = m[2]
        copies.extend([(fn, tag)])

    # traverse the removal specifiers
    ofn = None
    nb1 = None
    for (fn, tag) in copies:
        # change notebooks if needed
        if ofn != fn:
            if nb1 is not None:
                # commit the previous notebook
                nb1.commit()

            # load the notebook if it's not already loaded
            nb1 = epyc.HDF5LabNotebook(fn)
        ofn = fn

        # sanity check the result sets
        if tag not in nb1.resultSets():
            print(f"No result set '{tag}' in {fn}", file=sys.stderr)
            sys.exit(1)

        if verbose > 0:
            click.echo('Removed ' +
                       click.style(f'{fn}:{tag}', fg='green'))
        if not pretend:
            nb1.deleteResultSet(tag)

@cli.command()
@click.argument('spec')
@click.option('-v', '--verbose', count=True, help='Generate verbose output (repeat for extra verbosity)')
@click.option('-n', '--pretend', is_flag=True, help="Check validity but don't change anything")
def select(spec, verbose, pretend):
    '''Select a result set as current.

    The result set is specified as a pair NOTEBOOK[:TAG] where
    NOTEBOOK is the name of a notebook and TAG is a result set tag
    within NOTEBOOK. If no TAG is specified then the command returns
    the tag of the current result set.

    '''

    # extract the notebook and tag
    m = notebook_opt_resultset_re.match(spec)
    if m is None:
        print(f"Invalid result set specifier '{spec}'", file=sys.stderr)
        exit(1)
    else:
        fn = m[1]
        tag = m[3]

    with epyc.HDF5LabNotebook(fn).open() as nb:
        if tag == None:
            # no tag, just display the current result set's tag
            tag = nb.currentTag()
            print(tag)
        else:
            # sanity check
            if tag in nb.resultSets():
                # tag exists, make it current
                if not pretend:
                    nb.select(tag)
                    if verbose > 0:
                        click.echo('Made ' +
                                   click.style(f'{fn}:{tag}', fg='green') +
                                   " current")
            else:
                print(f'No result set {tag}')
                exit(1)


if __name__ == '__main__':
    cli()
