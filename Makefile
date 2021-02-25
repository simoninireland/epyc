# Makefile for epyc
#
# Copyright (C) 2016--2021 Simon Dobson
#
# This file is part of epyc, experiment management in Python.
#
# epyc is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# epyc is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with epyc. If not, see <http://www.gnu.org/licenses/gpl.html>.

# The name of our package on PyPi
PACKAGENAME = epyc

# The version we're building
VERSION = 1.3.2


# ----- Sources -----

# Source code
SOURCES_CODE = \
	epyc/py.typed \
	epyc/__init__.py \
	epyc/experiment.py \
	epyc/experimentcombinator.py \
	epyc/repeatedexperiment.py \
	epyc/summaryexperiment.py \
	epyc/lab.py \
	epyc/clusterlab.py \
	epyc/labnotebook.py \
	epyc/jsonlabnotebook.py \
	epyc/hdf5labnotebook.py \
        epyc/scripts/epyc.py
SOURCES_TESTS = \
	test/__init__.py \
	test/test_experiments.py \
	test/test_repeatedexperiments.py \
	test/test_summaryexperiments.py \
	test/test_labs.py \
	test/test_parallellabs.py \
	test/test_clusterlabs.py \
	test/test_resultsets.py \
	test/test_notebooks.py \
	test/test_jsonnotebooks.py \
	test/test_hdf5notebooks.py
TESTSUITE = test

SOURCES_TUTORIAL = doc/epyc.ipynb
SOURCES_DOC_CONF = doc/conf.py
SOURCES_DOC_BUILD_DIR = doc/_build
SOURCES_DOC_BUILD_HTML_DIR = $(SOURCES_DOC_BUILD_DIR)/html
SOURCES_DOC_ZIP = $(PACKAGENAME)-doc-$(VERSION).zip
SOURCES_DOCUMENTATION = \
	doc/index.rst \
	doc/install.rst \
	doc/lifecycle.rst \
	doc/glossary.rst \
	doc/tutorial.rst \
        doc/tutorial/concepts.rst \
        doc/tutorial/first.rst \
        doc/tutorial/simple-experiment.rst \
        doc/tutorial/defining.rst \
        doc/tutorial/testing.rst \
        doc/tutorial/lab.rst \
        doc/tutorial/parameters.rst \
        doc/tutorial/running.rst \
        doc/tutorial/results.rst \
        doc/tutorial/pointcloud.png\
        doc/tutorial/second.rst \
        doc/tutorial/parallel-concepts.rst \
        doc/tutorial/unicore-parallel.rst \
        doc/tutorial/multicore-parallel.rst \
        doc/tutorial/sharedfs-parallel.rst \
	doc/tutorial/cluster.rst \
	doc/tutorial/cluster-problems.rst \
	doc/tutorial/third.rst \
	doc/tutorial/large.rst \
	doc/tutorial/persistent.rst \
	doc/tutorial/pending.rst \
	doc/tutorial/locking.rst \
	doc/tutorial/fourth.rst \
	doc/tutorial/jupyter.rst \
	doc/tutorial/disconnected.rst \
	doc/tutorial/avoid-repeated.rst \
	doc/tutorial/here-and-there.rst \
	doc/cookbook.rst \
	doc/cookbook/epyc-venv.rst \
	doc/cookbook/disconnected-usage.rst \
	doc/cookbook/metadata.rst \
	doc/reference.rst \
	doc/experiment.rst \
	doc/resultset.rst \
	doc/lab.rst \
	doc/experimentcombinator.rst \
	doc/repeatedexperiment.rst \
	doc/summaryexperiment.rst \
	doc/jsonlabnotebook.rst \
	doc/hdf5labnotebook.rst \
	doc/clusterlab.rst \
	doc/exceptions.rst

# Extras for building diagrams etc
SOURCES_UTILS = \
        utils/make-pointcloud.py \
        utils/make-hdf5-url-test.py

# Extras for the build and packaging system
SOURCES_EXTRA = \
	README.rst \
	LICENSE \
	HISTORY
SOURCES_GENERATED = \
	MANIFEST \
	setup.py
SOURCES_SETUP_IN = setup.py.in

# Distribution files
DIST_SDIST = dist/$(PACKAGENAME)-$(VERSION).tar.gz
DIST_WHEEL = dist/$(PACKAGENAME)-$(VERSION)-py3-none-any.whl

# ipyparallel testing cluster
CLUSTER_PROFILE = $(PACKAGENAME)test
CLUSTER_PROFILE_DIR = `$(IPYTHON) locate profile $(CLUSTER_PROFILE)`
CLUSTER_TOKEN_FILE = $(CLUSTER_PROFILE_DIR)/pid/ipcluster.pid

# ----- Tools -----

# Base commands
PYTHON = python3
IPYTHON = ipython
IPCLUSTER = ipcluster
JUPYTER = jupyter
TOX = tox
COVERAGE = coverage
PIP = pip
TWINE = twine
GPG = gpg
GIT = git
VIRTUALENV = $(PYTHON) -m venv
ACTIVATE = . $(VENV)/bin/activate
TR = tr
CAT = cat
SED = sed
RM = rm -fr
CP = cp
CHDIR = cd
ZIP = zip -r

# Files that are locally changed vs the remote repo
# (See https://unix.stackexchange.com/questions/155046/determine-if-git-working-directory-is-clean-from-a-script)
GIT_DIRTY = $(shell $(GIT) status --untracked-files=no --porcelain)

# Root directory
ROOT = $(shell pwd)

# Requirements for running the library and for the development venv needed to build it
VENV = .venv
REQUIREMENTS = requirements.txt
DEV_REQUIREMENTS = dev-requirements.txt

# Requirements for setup.py
# We filter out any requirements for backporting before Python38
PY_REQUIREMENTS = $(shell $(SED) -e '/^typing_extensions/d' -e 's/^\(.*\)/"\1",/g' $(REQUIREMENTS) | $(TR) '\n' ' ')

# Constructed commands
RUN_TESTS = $(TOX)
RUN_COVERAGE = $(COVERAGE) erase && $(COVERAGE) run -a setup.py test && $(COVERAGE) report -m --include '$(PACKAGENAME)*'
RUN_NOTEBOOK = $(JUPYTER) notebook
RUN_SETUP = $(PYTHON) setup.py
RUN_SPHINX_HTML = PYTHONPATH=$(ROOT) make html
RUN_TWINE = $(TWINE) upload dist/$(PACKAGENAME)-$(VERSION).tar.gz dist/$(PACKAGENAME)-$(VERSION).tar.gz.asc
RUN_CREATE_PROFILE = $(IPYTHON) profile create --parallel $(CLUSTER_PROFILE)
RUN_CLUSTER = PYTHONPATH=.:test PATH=bin:$$PATH $(IPCLUSTER) start --profile $(CLUSTER_PROFILE) --n 2


# ----- Top-level targets -----

# Default prints a help message
help:
	@make usage

# Run the test suite in a suitable (predictable) virtualenv
test: env Makefile setup.py
	$(ACTIVATE) && $(RUN_TESTS)

# Run coverage checks over the test suite
coverage: env Makefile setup.py
	$(ACTIVATE) && $(RUN_COVERAGE)

# Run a small local compute cluster (in the foreground) for testing
cluster: env
	$(ACTIVATE) && $(RUN_CREATE_PROFILE) 
	$(RM) $(CLUSTER_TOKEN_FILE)
	$(ACTIVATE) && $(RUN_CLUSTER)

# Just run the ClusterLab tests
testclusterlab: env
	PYTHONPATH=. $(PYTHON) test/test_clusterlabs.py

# Build the API documentation using Sphinx
.PHONY: doc
doc: $(SOURCES_DOCUMENTATION) $(SOURCES_DOC_CONF)
	$(ACTIVATE) && $(CHDIR) doc && $(RUN_SPHINX_HTML)

# Build a development venv from the known-good requirements in the repo
.PHONY: env
env: $(VENV)

$(VENV):
	$(VIRTUALENV) $(VENV)
	$(CAT) $(REQUIREMENTS) $(DEV_REQUIREMENTS) >$(VENV)/requirements.txt
	$(ACTIVATE) && $(CHDIR) $(VENV) && $(PIP) install -r requirements.txt

# Build a source distribution
sdist: $(DIST_SDIST)

# Build a wheel distribution
wheel: $(DIST_WHEEL)

# Upload a source distribution to PyPi
upload: commit sdist wheel
	$(GPG) --detach-sign -a dist/$(PACKAGENAME)-$(VERSION).tar.gz
	$(ACTIVATE) && $(RUN_TWINE)

# Update the remote repos on release
commit: check-local-repo-clean
	$(GIT) push origin master
	$(GIT) tag -a v$(VERSION) -m "Version $(VERSION)"
	$(GIT) push origin v$(VERSION)

.SILENT: check-local-repo-clean
check-local-repo-clean:
	if [ "$(GIT_DIRTY)" ]; then echo "Uncommitted files: $(GIT_DIRTY)"; exit 1; fi

# Build the diagrams for the documentation and test files for URL testing
diagrams-data: diagrams testdata

diagrams:
	$(ACTIVATE) && PYTHONPATH=$(ROOT) $(PYTHON) utils/make-pointcloud.py

testdata:
	$(ACTIVATE) && PYTHONPATH=$(ROOT) $(PYTHON) utils/make-hdf5-url-test.py

# Clean up the distribution build 
clean:
	$(RM) $(SOURCES_GENERATED) epyc.egg-info dist $(SOURCES_DOC_BUILD_DIR) $(SOURCES_DOC_ZIP) dist build

# Clean up everything, including the computational environment (which is expensive to rebuild)
reallyclean: clean
	$(RM) $(VENV)


# ----- Generated files -----

# Manifest for the package
MANIFEST: Makefile
	echo  $(SOURCES_EXTRA) $(SOURCES_GENERATED) $(SOURCES_CODE) | $(TR) ' ' '\n' >$@

# The setup.py script
setup.py: $(SOURCES_SETUP_IN) Makefile
	$(CAT) $(SOURCES_SETUP_IN) | $(SED) -e 's|VERSION|$(VERSION)|g' -e 's|REQUIREMENTS|$(PY_REQUIREMENTS)|g' >$@

# The source distribution tarball
$(DIST_SDIST): $(SOURCES_GENERATED) $(SOURCES_CODE) Makefile
	$(ACTIVATE) && $(RUN_SETUP) sdist

# The binary (wheel) distribution
$(DIST_WHEEL): $(SOURCES_GENERATED) $(SOURCES_CODE) Makefile
	$(ACTIVATE) && $(RUN_SETUP) bdist_wheel


# ----- Usage -----

define HELP_MESSAGE
Available targets:
   make test         run the test suite for all Python versions we support
   make coverage     run coverage checks of the test suite
   make doc          build the API documentation using Sphinx
   make cluster      run a small compute cluster for use by the tests
   make env          create a known-good development virtual environment
   make sdist        create a source distribution
   make wheel	     create binary (wheel) distribution
   make upload       upload distribution to PyPi
   make commit       tag current version and push to master repo 
   make clean        clean-up the build
   make reallyclean  clean up the virtualenv as well

endef
export HELP_MESSAGE

usage:
	@echo "$$HELP_MESSAGE"
