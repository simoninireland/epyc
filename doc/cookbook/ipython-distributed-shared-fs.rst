.. _ipython-distributed-shared-fs:

.. currentmodule:: epyc

Setting up a compute cluster (with a shared filing system)
----------------------------------------------------------

Dedicated compute clusters often have a filing system shared between all the machines.


.. code-block:: python

    # BEGIN ipcontroller-config-x

    # ssh configuration to allow access to controller from outside
    c.IPControllerApp.ssh_server = "sif.cs.st-andrews.ac.uk"

    # engine configuration of where to register
    c.IPControllerApp.reuse_files = True
    c.IPControllerApp.location = "sif.cs.st-andrews.ac.uk"
    c.HubFactory.ip = u'*'

    # persistent store for jobs
    c.HubFactory.db_class ="IPython.parallel.controller.sqlitedb.SQLiteDB"

    # END ipcontroller-config-x



.. code-block:: shell

    #!/bin/sh

    targets=sif-[1-12]
    profile=cluster
    profile_dir=~/.ipython/profile_$profile
    command=$1

    cd ~/cncp
    . venv/bin/activate

    if [ "$command" == "init" ]; then
        rm -fr $profile_dir
        ipython profile create $profile --parallel
        cat ipcontroller-config-x.py >>$profile_dir/ipcontroller_config.py
        echo "Created new profile $profile"

    elif [ "$command" == "start" ]; then
        ipcontroller --profile=$profile &
        nohup pdsh -w $targets nohup cncp/engine.sh start &

    elif [ "$command" == "stop" ]; then
        pdsh -w $targets cncp/engine.sh stop
        killall ipcontroller

    else
        echo "usage: cluster.sh [init|start|stop]"
    fi




.. code-block:: shell

    #!/bin/sh

    profile=cluster
    hostname=`hostname`
    command=$1

    cd ~/cncp
    . venv/bin/activate

    if [ "$command" == "start" ]; then
        engines=`grep -c processor /proc/cpuinfo`
        for i in `seq 1 $engines`; do
	        nohup ipengine --profile=$profile &
        done
        echo "Started $engines engines on $hostname"

    elif [ "$command" == "stop" ]; then
        killall ipengine
        echo "Stopped engines on $hostname"

    else
        echo "usage: engine.sh [start|stop]"
    fi

