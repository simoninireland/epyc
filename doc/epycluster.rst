.. _epycluster:


Managing clusters
-----------------

``epycluster.sh`` is a script that wraps-up the mechanisms for starting and stopping ``ipyparallel`` compute
clusters on a range of different common topologies. Using ``epycluster`` it's not necessary to understand
the underlying machinery needed to manage distributed computing.

Usage: ``epycluster`` [options] command

In common with many modern tools, ``epycluster`` provides a range of sub-commands:

========  ========
Commands
========  ========
init      initialise a cluster profile
start     start the cluster
stop      stop the cluster
========  ========

There are also a small number of options, not all used with all commands:

====================================  ========
Options
====================================  ========
-V, --verbose                         verbose output
-v <venv>, --venv <venv>              run in Python virtual environment <venv>
-p <profile>, --profile <profile>     use <profile> as the cluster's profile
-d <class>, --dbclass <class>         use Python <class> for controller jobs database
-m <machines>, --machines <machines>  start engines on named <machines>
-n <n>, --engines <n>                 start <n> engines on each machine
-h, --help                            show this message
====================================  ========

See :ref:`second-tutorial` for an introduction to using ``epycluster``.
