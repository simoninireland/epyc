# Makefile for epyc
#
# Copyright (C) 2016 Simon Dobson
# 
# Licensed under the GNU General Public Licence v.2.0
# 


# ----- Sources -----

# Source code
SOURCES_SETUP_IN = setup.py.in
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
SOURCES_DOC = doc/epyc.ipynb
SOURCES_EXTRA = \
	README.rst \
	LICENSE
SOURCES_GENERATED = \
	MANIFEST \
	setup.py

# Python packages needed
# For the system to install and run
PY_COMPUTATIONAL = \
	ipython \
	pyzmq \
	ipyparallel \
	dill \
	pandas
# For the documentation
PY_INTERACTIVE = \
	numpy \
	jupyter \
	matplotlib \
	seaborn

# Packages that shouldn't be saved as requirements (because they're
# OS-specific, in this case OS X, and screw up Linux compute servers)
PY_NON_REQUIREMENTS = \
	appnope


# ----- Tools -----

# Base commands
PYTHON = python
IPYTHON = ipython
JUPYTER = jupyter
IPCLUSTER = ipcluster
PIP = pip
VIRTUALENV = virtualenv
ACTIVATE = . bin/activate
TR = tr
CAT = cat
SED = sed
RM = rm -fr
CP = cp
CHDIR = cd

# Constructed commands
RUN_TESTS = $(IPYTHON) -m $(TESTSUITE)
RUN_CLUSTER = $(IPCLUSTER) start --profile=default --n=2
RUN_NOTEBOOK = $(JUPYTER) notebook
RUN_SETUP = $(PYTHON) setup.py

# Virtual environment support
ENV_COMPUTATIONAL = venv
REQ_COMPUTATIONAL = requirements.txt
NON_REQUIREMENTS = $(SED) $(patsubst %, -e '/^%*/d', $(PY_NON_REQUIREMENTS))
REQ_SETUP = $(PY_COMPUTATIONAL:%="%",)


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

# Run a server for writing the documentation
.PHONY: doc
doc:
	($(CHDIR) $(ENV_COMPUTATIONAL) && $(ACTIVATE) && $(CHDIR) ../doc && PYTHONPATH=.. $(RUN_NOTEBOOK))

cluster: env-computational

# Build a source distribution
dist: $(SOURCES_GENERATED)
	$(RUN_SETUP) sdist

# Upload a source distribution to PyPi (has to be done in one command)
upload: $(SOURCES_GENERATED)
	$(RUN_SETUP) sdist upload

# Clean up the distribution build 
clean:
	$(RM) $(SOURCES_GENERATED) epyc.egg-info dist

# Clean up everything, including the computational environment (which is expensive to rebuild)
reallyclean: clean
	$(RM) $(ENV_COMPUTATIONAL)


# ----- Helper targets -----

# Build a computational environment in which to run the test suite
env-computational: $(ENV_COMPUTATIONAL)

# Build a new, updated, requirements.txt file ready for commiting to the repo
# Only commit if we're sure we pass the test suite!
newenv-computational:
	echo $(PY_COMPUTATIONAL)  $(PY_INTERACTIVE) | $(TR) ' ' '\n' >$(REQ_COMPUTATIONAL)
	make env-computational
	$(NON_REQUIREMENTS) $(ENV_COMPUTATIONAL)/requirements.txt >$(REQ_COMPUTATIONAL)

# Only re-build computational environment if the directory is missing
$(ENV_COMPUTATIONAL):
	$(VIRTUALENV) $(ENV_COMPUTATIONAL)
	$(CP) $(REQ_COMPUTATIONAL) $(ENV_COMPUTATIONAL)/requirements.txt
	$(CHDIR) $(ENV_COMPUTATIONAL) && $(ACTIVATE) && $(PIP) install -r requirements.txt && $(PIP) freeze >requirements.txt


# ----- Generated files -----

# Manifest for the package
MANIFEST:
	echo  $(SOURCES_EXTRA) $(SOURCES_GENERATED) $(SOURCES_CODE) | $(TR) ' ' '\n' >$@

# The setup.py script
setup.py: $(SOURCES_SETUP_IN)
	$(CAT) $(SOURCES_SETUP_IN) | sed -e 's/REQ_SETUP/$(REQ_SETUP)/g' >$@


# ----- Usage -----

define HELP_MESSAGE
Available targets:
   make test         run the test suite in a suitable virtualenv
   make cluster      run a small compute cluster for use by the tests
   make dist         create a source distribution
   make upload       upload distribution to PyPi
   make clean        clean-up the build
   make reallyclean  clean up the virtualenv as well

endef
export HELP_MESSAGE

usage:
	@echo "$$HELP_MESSAGE"
