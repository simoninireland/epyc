#!/usr/bin/env bash
set -o errexit -o pipefail -o noclobber -o nounset

# Script to fire-up an engines as part of an ipyparallel compute cluster
#
# Copyright (C) 2016--2019 Simon Dobson
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

hostname=`hostname`
profile="default"
verbose=""
venv=""
if [[ -e /proc/cpuinfo ]]; then
    # we're on Linux, so we can query for the number of cores as a default
    engines=$(grep -c processor /proc/cpuinfo)
else
    engines=1
fi

# make sure we've got a working getopt
! getopt --test >/dev/null
if [[ ${PIPESTATUS[0]} -ne 4 ]]; then
    echo '$0: no getopt'
    exit 1
fi

# usage
OPTS="Vv:p:n:"
LONGOPTS="verbose,venv:,profile:,engines:"
usage () {
    cat <<EOU
Usage: $0 [options] command

Commands:
   start                                 start the engines
   stop                                  stop the engines

Options:
   -V, --verbose                         verbose output
   -v <venv>, --venv <venv>              run in Python virtual environment <venv>
   -p <profile>, --profile <profile>     use IPython <profile>
   -n <n>, --engines <n>                 start <n> engines
EOU
    exit 0
}

# parse command-line options
! PARSED=$(getopt --options=$OPTS --longoptions=$LONGOPTS --name "$0" -- "$@")
if [[ ${PIPESTATUS[0]} -ne 0 ]]; then
    echo "$0: getopt couldn't parse options"
    exit 1
fi
eval set -- "$PARSED"
while true; do
    case "$1" in
        -V|--verbose)
            verbose="true"
            shift
            ;;
        -v|--venv)
            venv="$2"
            shift 2
            ;;
        -p|--profile)
            profile="$2"
            shift 2
            ;;
        -n|--engines)
            engines="$2"
            shift 2
            ;;
        --)
            shift
            break
            ;;
     esac
done

# get command
if [[ $# -ne 1 ]]; then
    usage
fi
command=$1

# enter virtual environment if one has been provided
if [[ ! "$venv" = "" ]]; then
    if [[ "$verbose" = "true" ]]; then
        echo "Entering virtual environment $venv"
    fi
    . $venv/bin/activate
fi

# acquire profile directory and create pid filename
profile_dir=$(ipython locate profile $profile)
engines_pidfile="$profile_dir/epyc-engines-$hostname.pid"

# execute command
if [[ "$command" == "start" ]]; then
    for i in `seq 1 $engines`; do
        ipengine --profile=$profile 2>&1 >>/dev/null &
        echo -n "$! " >>$engines_pidfile
    done
    if [[ "$verbose" = "true" ]]; then
        echo "Started $engines engines on $hostname"
    fi

elif [[ "$command" == "stop" ]]; then
    kill -9 $(cat $engines_pidfile)
    if [[ "$verbose" = "true" ]]; then
        echo "Stopped engines on $hostname"
    fi
    rm $engines_pidfile

else
    usage
fi



