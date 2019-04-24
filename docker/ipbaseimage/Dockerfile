# Base image for IPython ipyparallel docker containers
FROM python:2.7.15-stretch

# Build parameters
ARG USER="epyc"

# Create a non-root user and home directory to run in -- but stay as root
# while we complete the setup
RUN useradd -ms /bin/bash $USER
WORKDIR /home/$USER

# Populate the build environment
RUN apt-get update && \
    apt-get install -y \
    libopenblas-base libopenblas-dev \
    libatlas-base-dev
COPY requirements.txt .
RUN pip install --no-cache-dir -r ./requirements.txt

# Downgrade to the non-root user and create an IPython parallel profile
USER $USER
RUN ipython profile create --parallel epyc
