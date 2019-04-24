# ipcontroller docker container
FROM ipbaseimage

# Run-time arguments
ENV SESSION_KEY="1d3beb15-278f4773cbabb73ede26c97d"

# Provide a shared session key to the controller and start the cluster controller
CMD PROFILE_DIR=`ipython profile locate epyc` && \
    echo "c.Session.key = '$SESSION_KEY'" >>$PROFILE_DIR/ipcontroller_config.py && \
    ipcontroller start --profile=epyc
