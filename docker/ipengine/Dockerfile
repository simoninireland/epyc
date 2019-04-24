# ipcontroller docker container
FROM ipbaseimage

# Run-time arguments
ENV SESSION_KEY="1d3beb15-278f4773cbabb73ede26c97d"
ENV ENGINES=1

# Provide a shared session key and start as many engines as requested
CMD PROFILE_DIR=`ipython profile locate epyc` && \
    echo "c.Session.key = '$SESSION_KEY'" >>$PROFILE_DIR/ipengine_config.py && \
    ipengine --profile=epyc