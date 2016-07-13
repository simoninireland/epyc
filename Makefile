# Makefile for epyc
#
# Copyright (C) 2016 Simon Dobson
# 
# Licensed under the GNU General Public Licence v.2.0
# 


# ----- Sources -----

# Source code
SOURCES_SETUP = setup.py
SOURCES_CODE = \
	epyc/__init__.py \
	epyc/experiment.py \
	epyc/lab.py \
	epyc/clusterlab.py \
	epyc/labnotebook.py \
	epyc/jsonlabnotebook.py \
	epyc/sqlitelabnotebook.py
SOURCES_TESTS = \
	test/__init__.py \
	test/__main__.py \
	test/experiments.py \
	test/labs.py \
	test/clusterlabs.py \
	test/notebooks.py \
	test/jsonnotebooks.py \
	test/sqlitenotebooks.py
TESTSUITE = test

# Python packages needed by the test suite
PY_COMPUTATIONAL = \
	ipython \
	pyzmq \
	openssl \
	ipyparallel \
	numpy \
	dill \
	paramiko

# Packages that shouldn't be saved as requirements (because they're
# OS-specific, in this case OS X, and screw up Linux compute servers)
PY_NON_REQUIREMENTS = \
	appnope


# ----- Tools -----

# Base commands
PYTHON = python
IPYTHON = ipython
IPCLUSTER = ipcluster
PIP = pip
VIRTUALENV = virtualenv
ACTIVATE = . bin/activate
TR = tr
RM = rm -fr
CP = cp
CHDIR = cd

# Constructed commands
RUN_TESTS = $(IPYTHON) -m $(TESTSUITE)
RUN_CLUSTER = $(IPCLUSTER) start --profile=default --n=2

# Virtual environment support
ENV_COMPUTATIONAL = epyc_virtualenv
REQ_COMPUTATIONAL = requirements.txt
NON_REQUIREMENTS = $(SED) $(patsubst %, -e '/^%*/d', $(PY_NON_REQUIREMENTS))


# ----- Top-level targets -----

# Default prints a help message
help:
	@make usage

# Run the test suite in a suitable (predictable) virtualenv
test: env-computational
	($(CHDIR) $(ENV_COMPUTATIONAL) && $(ACTIVATE) && $(CHDIR) .. && $(RUN_TESTS))

# Run a small local compute cluster (in the foreground) for testing
cluster: env-computational
	($(CHDIR) $(ENV_COMPUTATIONAL) && $(ACTIVATE) && $(CHDIR) .. && $(RUN_CLUSTER))

# Build a source distribution
dist: MANIFEST 
	$(PYTHON) setup.py sdist

# Clean up the distribution build 
clean:
	$(RM) MANIFEST dist

# Clean up everything, including the computational environment (which is expensive to rebuild)
reallyclean: clean
	$(RM) $(ENV_COMPUTATIONAL)


# ----- Helper targets -----

# Create the manifest for the package
MANIFEST: $(SOURCES_SETUP) $(SOURCES_CODE)
	echo $(SOURCES_SETUP) $(SOURCES_CODE) | $(TR) ' ' '\n' >MANIFEST

# Build a computational environment in which to run the test suite
env-computational: $(ENV_COMPUTATIONAL)

# Build a detailed requirements.txt file ready for commiting to the repo
newenv-computational:
	echo $(PY_COMPUTATIONAL) | $(TR) ' ' '\n' >$(REQ_COMPUTATIONAL)
	make env-computational
	$(NON_REQUIREMENTS) $(ENV_COMPUTATIONAL)/requirements.txt >$(REQ_COMPUTATIONAL)

# Only re-build computational environment if the directory is missing
$(ENV_COMPUTATIONAL):
	$(VIRTUALENV) $(ENV_COMPUTATIONAL)
	$(CP) $(REQ_COMPUTATIONAL) $(ENV_COMPUTATIONAL)/requirements.txt
	$(CHDIR) $(ENV_COMPUTATIONAL) && $(ACTIVATE) && $(PIP) install -r requirements.txt && $(PIP) freeze >requirements.txt


# ----- Usage -----

define HELP_MESSAGE
Available targets:
   make test         run the test suite in a suitable virtualenv
   make cluster      run a small compute cluster for use by the tests
   make dist         create a source distribution
   make clean        clean-up the build
   make reallyclean  clean up the virtualenv as well

endef
export HELP_MESSAGE

usage:
	@echo "$$HELP_MESSAGE"
