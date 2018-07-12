# Makefile for epyc
#
# Copyright (C) 2016--2018 Simon Dobson
# 
# Licensed under the GNU General Public Licence v.2.0
# 

# The name of our package on PyPi
PACKAGENAME = epyc

# The version we're building
VERSION = 0.15.1

# ----- Sources -----

# Source code
SOURCES_SETUP_IN = setup.py.in
SOURCES_SDIST = dist/$(PACKAGENAME)-$(VERSION).tar.gz
SOURCES_CODE = \
	epyc/__init__.py \
	epyc/experiment.py \
	epyc/experimentcombinator.py \
	epyc/repeatedexperiment.py \
	epyc/summaryexperiment.py \
	epyc/lab.py \
	epyc/clusterlab.py \
	epyc/labnotebook.py \
	epyc/jsonlabnotebook.py
SOURCES_TESTS = \
	test/__init__.py \
	test/__main__.py \
	test/test_experiments.py \
	test/test_repeatedexperiments.py \
	test/test_summaryexperiments.py \
	test/test_labs.py \
	test/test_clusterlabs.py \
	test/test_notebooks.py \
	test/test_jsonnotebooks.py
TESTSUITE = test

SOURCES_TUTORIAL = doc/epyc.ipynb
SOURCES_DOC_CONF = doc/conf.py
SOURCES_DOC_BUILD_DIR = doc/_build
SOURCES_DOC_BUILD_HTML_DIR = $(SOURCES_DOC_BUILD_DIR)/html
SOURCES_DOC_ZIP = epyc-doc-$(VERSION).zip
SOURCES_DOCUMENTATION = \
	doc/index.rst \
	doc/experiment.rst \
	doc/lab.rst \
	doc/experimentcombinator.rst \
	doc/repeatedexperiment.rst \
	doc/summaryexperiment.rst \
	doc/jsonlabnotebook.rst \
	doc/clusterlab.rst \
	doc/glossary.rst \
	doc/index.rst

SOURCES_EXTRA = \
	README.rst \
	LICENSE \
	HISTORY
SOURCES_GENERATED = \
	MANIFEST \
	setup.py \
	$(SOURCES_DOC_CONF)

# Python packages needed
# For the system to install and run
PY_REQUIREMENTS = \
    future \
	ipython \
	pyzmq \
	ipyparallel \
	dill \
	pandas
# For the documentation and development venv
PY_DEV_REQUIREMENTS = \
    six \
	numpy \
	jupyter \
	matplotlib \
	seaborn \
	sphinx \
	twine

# Packages that shouldn't be saved as requirements (because they're
# OS-specific, in this case OS X, and screw up Linux compute servers,
# or because of Pytnon 2.7 vs 3.7 incompatibilities)
PY_NON_REQUIREMENTS = \
	appnope \
	functools32 \
	subprocess32 \
	futures
VENV = venv
REQUIREMENTS = requirements.txt
DEV_REQUIREMENTS = dev-requirements.txt

# Name for the IPython parallel cluster we use for testing
PROFILE = $(PACKAGENAME)


# ----- Tools -----

# Base commands
PYTHON = python
IPYTHON = ipython
JUPYTER = jupyter
IPCLUSTER = ipcluster
PIP = pip
TWINE = twine
GPG = gpg
VIRTUALENV = virtualenv
ACTIVATE = . $(VENV)/bin/activate
TR = tr
CAT = cat
SED = sed
RM = rm -fr
CP = cp
CHDIR = cd
ZIP = zip -r

# Root directory
ROOT = $(shell pwd)

# Constructed commands
RUN_TESTS = $(PYTHON) -m unittest discover -s test
RUN_SETUP = $(PYTHON) setup.py
RUN_SPHINX_HTML = PYTHONPATH=$(ROOT) make html
RUN_TWINE = $(TWINE) upload dist/$(PACKAGENAME)-$(VERSION).tar.gz dist/$(PACKAGENAME)-$(VERSION).tar.gz.asc
NON_REQUIREMENTS = $(SED) $(patsubst %, -e '/^%*/d', $(PY_NON_REQUIREMENTS))
RUN_CLUSTER = PYTHONPATH=.:test $(IPCLUSTER) start --profile=default --n=2
RUN_NOTEBOOK = PYTHONPATH=$(ROOT) $(JUPYTER) notebook

# Python3 compatibility testing
VENV3 = venv3
PYTHON3 = python3
VIRTUALENV3 = $(PYTHON3) -m venv
ACTIVATE3 = . $(VENV3)/bin/activate
PIP3 = pip3
RUN_TESTS3 = $(PYTHON3) -m unittest discover -s test


# ----- Top-level targets -----

# Default prints a help message
help:
	@make usage

# Run the test suite in a suitable (predictable) virtualenv
test: env
	$(ACTIVATE) && $(RUN_TESTS)

# Run a small local compute cluster (in the foreground) for testing
cluster: env
	$(ACTIVATE) && $(RUN_CLUSTER)

# Build the API documentation using Sphinx
.PHONY: doc
doc: $(SOURCES_DOCUMENTATION) $(SOURCES_DOC_CONF)
	(ACTIVATE) && $(CHDIR) doc && $(RUN_SPHINX_HTML)

.PHONY: docserver
docserver:
	$(ACTIVATE) && $(CHDIR) doc && $(RUN_NOTEBOOK))

# Build a development venv from the known-good requirements in the repo
.PHONY: env
env: $(VENV)

$(VENV):
	$(VIRTUALENV) $(VENV)
	$(CP) $(DEV_REQUIREMENTS) $(VENV)/requirements.txt
	$(ACTIVATE) && $(CHDIR) $(VENV) && $(PIP) install -r requirements.txt

# Build a development venv from the latest versions of the required packages,
# creating a new requirements.txt ready for committing to the repo. Make sure
# things actually work in this venv before committing!
.PHONY: newenv
newenv:
	$(RM) $(VENV)
	$(VIRTUALENV) $(VENV)
	echo $(PY_REQUIREMENTS) | $(TR) ' ' '\n' >$(VENV)/$(REQUIREMENTS)
	$(ACTIVATE) && $(CHDIR) $(VENV) && $(PIP) install -r requirements.txt && $(PIP) freeze >requirements.txt
	$(NON_REQUIREMENTS) $(VENV)/requirements.txt >$(REQUIREMENTS)
	echo $(PY_DEV_REQUIREMENTS) | $(TR) ' ' '\n' >$(VENV)/$(REQUIREMENTS)
	$(ACTIVATE) && $(CHDIR) $(VENV) && $(PIP) install -r requirements.txt && $(PIP) freeze >requirements.txt
	$(NON_REQUIREMENTS) $(VENV)/requirements.txt >$(DEV_REQUIREMENTS)

# Build a source distribution
sdist: $(SOURCES_SDIST)

# Upload a source distribution to PyPi
upload: $(SOURCES_SDIST)
	$(GPG) --detach-sign -a dist/$(PACKAGENAME)-$(VERSION).tar.gz
	$(ACTIVATE) && $(RUN_TWINE)

# Clean up the distribution build 
clean:
	$(RM) $(SOURCES_GENERATED) epyc.egg-info dist $(SOURCES_DOC_BUILD_DIR) $(SOURCES_DOC_ZIP)

# Clean up everything, including the computational environment (which is expensive to rebuild)
reallyclean: clean
	$(RM) $(VENV)


# ----- Python3 compatibility -----

# Build a Python3 compatibility venv
.PHONY: env3
env3: $(VENV3)

$(VENV3):
	$(VIRTUALENV3) $(VENV3)
	$(CP) $(DEV_REQUIREMENTS) $(VENV3)/requirements.txt
	$(ACTIVATE3) && $(CHDIR) $(VENV3) && $(PIP3) install -r requirements.txt

# Run the test suite in a Python3 environment
compat: env3
	$(ACTIVATE3) && $(RUN_TESTS3)


# ----- Generated files -----

# Manifest for the package
MANIFEST: Makefile
	echo  $(SOURCES_EXTRA) $(SOURCES_GENERATED) $(SOURCES_CODE) | $(TR) ' ' '\n' >$@

# The setup.py script
setup.py: $(SOURCES_SETUP_IN) Makefile
	$(CAT) $(SOURCES_SETUP_IN) | $(SED) -e 's/VERSION/$(VERSION)/g' -e 's/REQUIREMENTS/$(PY_REQUIREMENTS:%="%",)/g' >$@

# The source distribution tarball
$(SOURCES_SDIST): $(SOURCES_GENERATED) $(SOURCES_CODE) Makefile
	$(ACTIVATE) && $(RUN_SETUP) sdist


# ----- Usage -----

define HELP_MESSAGE
Available targets:
   make test         run the test suite in a suitable virtualenv
   make doc          build the API documentation using Sphinx
   make cluster      run a small compute cluster for use by the tests
   make docserver    run a Jupyter notebook to edit the tutorial
   make env          create a known-good development virtual environment
   make newenv       update the development venv's requirements
   make sdist        create a source distribution
   make clean        clean-up the build
   make reallyclean  clean up the virtualenv as well

Python3 compatibility:
   make compat       run test suite in Python3 virtualenv

endef
export HELP_MESSAGE

usage:
	@echo "$$HELP_MESSAGE"
