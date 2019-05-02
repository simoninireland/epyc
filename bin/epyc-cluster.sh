#!/usr/bin/env bash

# Script to fire-up a compute cluster
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
machines=""
dbclass="IPython.parallel.controller.sqlitedb.SQLiteDB"
profile="default"
verbose=""
venv=""
engines=""

# make sure we've got a working getopt
! getopt --test >/dev/null
if [[ ${PIPESTATUS[0]} -ne 4 ]]; then
    echo '$0: no getopt'
    exit 1
fi

# usage
OPTS="Vv:p:d:n:m:"
LONGOPTS="verbose,venv:,profile:,dbclass:,engines:,machines:"
usage () {
    cat <<EOU
Usage: $0 [options] command

Commands:
   init                                  initialise a cluster profile
   start                                 start the cluster
   stop                                  stop the cluster

Options:
   -V, --verbose                         verbose output
   -v <venv>, --venv <venv>              run in Python virtual environment <venv>
   -p <profile>, --profile <profile>     use IPython <profile>
   -d <class>, --dbclass <class>         use Python <class> for controller jobs database
   -m <machines>, --machines <machines>  start engines on named <machines>
   -n <n>, --engines <n>                 start <n> engines on each machine
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
        -d|--dbclass)
            dbclass="$2"
            shift 2
            ;;
        -n|--engines)
            engines="$2"
            shift 2
            ;;
        -m|--machines)
            machines="$2"
            shift 2
            ;;
        --)
            shift
            break
            ;;
     esac
done
engineopts="--profile $profile"
if [[ "$verbose" = "true" ]]; then
    engineopts="$engineopts --verbose"
fi
if [[ ! "$venv" = "" ]]; then
    engineopts="$engineopts --venv $venv"
fi
if [[ ! "$engines" = "" ]]; then
    engineopts="$engineopts -n $engines"
fi
if [[ "$verbose" = "true" ]]; then
    echo "Started $engines engines on $hostname"
fi

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
ipcontroller_config="$profile_dir/ipcontroller_config.py"
tasksdb="$profile_dir/tasks.db"
controller_pidfile="$profile_dir/epyc-controller.pid"

# execute command
if [[ "$command" == "init" ]]; then
    rm -fr $profile_dir
    ipython profile create $profile --parallel
    cat >>$ipcontroller_config <<EOF
# BEGIN epyc-cluster

# persistent store for jobs
c.HubFactory.db_class ="$dbclass"

# END epyc-cluster
EOF
    if [[ $verbose ]]; then
        echo "Created new profile $profile"
    fi

elif [[ "$command" == "start" ]]; then
    rm -fr nohup.out $tasksdb
    if [[ -e $controller_pidfile ]]; then
        echo "$0: controller already running ($controller_pidfile)"
        exit 1
    fi
    ipcontroller --profile=$profile 2>&1 >>/dev/null &
    echo $! >$controller_pidfile
    sleep 2
    if [[ "$verbose" = "true" ]]; then
        echo "Started controller on $hostname"
    fi

    if [[ "$machines" = "" ]]; then
        epyc-engine.sh $engineopts start
    else
        for m in "$machines"; do
            ssh $m epyc-engine.sh $engineopts start
        done
    fi

elif [[ "$command" == "stop" ]]; then
    if [[ "$machines" = "" ]]; then
        epyc-engine.sh $engineopts stop
    else
        for m in "$machines"; do
            ssh $m epyc-engine.sh $engineopts stop
        done
    fi

    if [[ "$verbose" = "true" ]]; then
        kill -9 $(cat $controller_pid)
        echo "Stopped controller on $hostname"
    fi
    rm $controller_pidfile

else
    usage
fi



