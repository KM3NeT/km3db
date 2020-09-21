PKGNAME=km3db

default: build

all: install

install: 
	pip install .

install-dev:
	pip install -e ".[dev]"

venv:
	python3 -m venv venv

clean:
	python3 setup.py clean --all
	rm -rf venv

test: 
	py.test --junitxml=./reports/junit.xml -o junit_suite_name=$(PKGNAME) tests

test-cov:
	py.test --cov ./$(PKGNAME) --cov-report term-missing --cov-report xml:reports/coverage.xml --cov-report html:reports/coverage tests

test-loop: 
	py.test tests
	ptw --ext=.py,.pyx --ignore=doc tests

black:
	black $(PKGNAME)
	black doc/conf.py
	black tests
	black examples
	black setup.py

.PHONY: all clean install install-dev venv test test-cov test-loop yapf
