PKGNAME=km3db

default: build

all: install

install: 
	pip install .

install-dev:
	pip install -e ".[dev]"
	pip install -e ".[extras]"

venv:
	python3 -m venv venv

clean:
	python3 setup.py clean --all
	rm -rf venv

test: 
	python -m pytest --junitxml=./reports/junit.xml -o junit_suite_name=$(PKGNAME) tests

test-cov:
	python -m pytest --cov ./$(PKGNAME) --cov-report term-missing --cov-report xml:reports/coverage.xml --cov-report html:reports/coverage tests

test-loop: 
	python -m pytest tests
	ptw --ext=.py,.pyx --ignore=doc tests

benchmark:
	scripts/run_benchmarks.py benchmarks

black:
	black $(PKGNAME)
	black doc/conf.py
	black tests
	black examples
	black setup.py

.PHONY: all clean install install-dev venv test test-cov test-loop benchmark black
