# Makefile for epyc
#
# Copyright (C) 2016--2018 Simon Dobson
# 
# Licensed under the GNU General Public Licence v.2.0
# 

# The name of our package on PyPi
PACKAGENAME = epyc

# The version we're building
VERSION = 0.16.1

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
	doc/install.rst \
	doc/lifecycle.rst \
	doc/concepts.rst \
	doc/cookbook.rst \
	doc/cookbook/epyc-venv.rst \
	doc/cookbook/ipython-multicore.rst \
	doc/cookbook/ipython-distributed.rst \
	doc/cookbook/ipython-distributed-shared-fs.rst \
	doc/cookbook/disconnected-usage.rst \
	doc/tutorial.rst \
    doc/tutorial/simple-experiment.rst \
    doc/tutorial/defining.rst \
    doc/tutorial/testing.rst \
    doc/tutorial/lab.rst \
    doc/tutorial/parameters.rst \
    doc/tutorial/running.rst \
    doc/tutorial/results.rst \
	doc/reference.rst \
	doc/experiment.rst \
	doc/lab.rst \
	doc/experimentcombinator.rst \
	doc/repeatedexperiment.rst \
	doc/summaryexperiment.rst \
	doc/jsonlabnotebook.rst \
	doc/clusterlab.rst \
	doc/gotchas.rst \
    doc/gotchas/jupyter-class-names.rst \
	doc/glossary.rst

SOURCES_UTILS = \
    utils/make-pointcloud.py

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
    six \
    future \
	ipython \
	pyzmq \
	ipyparallel \
	dill \
	pandas
# For the documentation and development venv
PY_DEV_REQUIREMENTS = \
	numpy \
	jupyter \
	matplotlib \
	seaborn \
	nose \
	tox \
	coverage \
	sphinx \
	twine

# Packages that shouldn't be saved as requirements (because they're
# OS-specific, in this case OS X, and screw up Linux compute servers,
# or because of Python 2.7 vs 3.7 incompatibilities)
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
TOX = tox
COVERAGE = coverage
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
RUN_TESTS = $(TOX)
RUN_COVERAGE = $(COVERAGE) erase && $(COVERAGE) run -a setup.py test && $(COVERAGE) report -m --include '$(PACKAGENAME)*'
RUN_SETUP = $(PYTHON) setup.py
RUN_SPHINX_HTML = PYTHONPATH=$(ROOT) make html
RUN_TWINE = $(TWINE) upload dist/$(PACKAGENAME)-$(VERSION).tar.gz dist/$(PACKAGENAME)-$(VERSION).tar.gz.asc
NON_REQUIREMENTS = $(SED) $(patsubst %, -e '/^%*/d', $(PY_NON_REQUIREMENTS))
RUN_CLUSTER = PYTHONPATH=.:test $(IPCLUSTER) start --profile=default --n=2
RUN_NOTEBOOK = PYTHONPATH=$(ROOT) $(JUPYTER) notebook


# ----- Top-level targets -----

# Default prints a help message
help:
	@make usage

# Run the test suite in a suitable (predictable) virtualenv
test: env
	$(ACTIVATE) && $(RUN_TESTS)

# Run coverage checks over the test suite
coverage: env
	$(ACTIVATE) && $(RUN_COVERAGE)

# Run a small local compute cluster (in the foreground) for testing
cluster: env
	$(ACTIVATE) && $(RUN_CLUSTER)

# Build the API documentation using Sphinx
.PHONY: doc
doc: $(SOURCES_DOCUMENTATION) $(SOURCES_DOC_CONF)
	$(ACTIVATE) && $(CHDIR) doc && $(RUN_SPHINX_HTML)

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
   make test         run the test suite for all Python versions we support
   make coverage     run coverage checks of the test suite
   make doc          build the API documentation using Sphinx
   make cluster      run a small compute cluster for use by the tests
   make docserver    run a Jupyter notebook to edit the tutorial
   make env          create a known-good development virtual environment
   make newenv       update the development venv's requirements
   make sdist        create a source distribution
   make clean        clean-up the build
   make reallyclean  clean up the virtualenv as well

endef
export HELP_MESSAGE

usage:
	@echo "$$HELP_MESSAGE"
