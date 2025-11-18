SHELL=/bin/bash

.PHONY : conda
conda :
	conda env create -f environment.yaml --yes

.PHONY : install
install :
	inv install --no-optional-deps

.PHONY : install-all
install-all :
	inv install --docs-deps

.PHONY : update
update :
	inv update

.PHONY : lint
lint :
	inv check-lint

.PHONY : format
format :
	inv check-format

.PHONY : docformat
docformat :
	inv docformat

.PHONY : doctest-src
doctest-src :
	inv doctest-src

.PHONY : unit-test
unit-test :
	inv unit-test

.PHONY : unit-test-cov
unit-test-cov :
	inv unit-test --cov

.PHONY : integration-test
integration-test :
	inv integration-test

.PHONY : integration-test-cov
integration-test-cov :
	inv integration-test --cov

.PHONY : publish-pypi
publish-pypi :
	inv publish-pypi

.PHONY : publish-doc-dev
publish-doc-dev :
	inv publish-doc-dev

.PHONY : publish-doc-latest
publish-doc-latest :
	inv publish-doc-latest

.PHONY : setup-venv
setup-venv :
	$(MAKE) update-uv
	uv venv --python 3.13 --clear
	$(MAKE) install-invoke
	.venv/bin/inv create-venv
	.venv/bin/inv install --docs-deps

.PHONY : install-invoke
install-invoke :
	uv pip install "invoke>=2.2.0"

.PHONY : update-uv
update-uv :
	uv self update
