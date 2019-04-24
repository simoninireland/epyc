# Standalone ipcluster docker container
FROM ipbaseimage

# Spin-up a cluster (controller and engines) with an engine per processor
CMD engines=`grep -c processor /proc/cpuinfo` && \
    ipcluster start --profile=epyc --n=$engines
