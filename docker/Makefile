# Makefile for epyc docker containers
#
# Copyright (C) 2018 Simon Dobson
#
# Licensed under the GNU General Public Licence v.2.0
#

# ----- Sources -----

# Image names
IMAGES = \
    ipbaseimage \
    ipcluster

# Dockerfiles for the images
DOCKERFILES = $(patsubst %, %/Dockerfile, $(IMAGES))


# ----- Tools -----

# Base commands
DOCKER = docker

# Constructed commands
BUILD_IMAGE = $(DOCKER) build


# ----- Top-level targets -----

# Default prints a help message
help:
	@make usage

# Build all images
build: $(DOCKERFILES)


# ----- Helper rules -----

.PHONY: ipbaseimage
ipbaseimage: ipbaseimage/Dockerfile
	$(BUILD_IMAGE) -f $@/Dockerfile -t $@ ..

