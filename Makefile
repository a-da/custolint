IGNORE_ERROR_EXIT ?= false

update_pip:
	pip install -U pip wheel

wheel: clean
	python -m build . --wheel

deploy_to_pypy: wheel validate
	twine upload dist/*

clean:
	rm -rvf ./build/ ./dist/ .coverage ./src/custolint.egg-info/ README.html ./.mypy_cache/
	rm -rvf	./.pytest_cache/ ./tests/.pytest_cache/ ./htmlcov/
	$(MAKE) --directory=docs clean_docs
	rm -f docs.tar

install:
	pip install custolint

install_dev:
	pip install -e .[dev,deploy_to_pip]

custolint_validate:
	coverage run --rcfile=config.d/.coveragerc -m pytest
	custolint coverage .coverage
	echo
	custolint pylint
	echo
	custolint flake8
	echo
	custolint mypy

validate: custolint_validate
	pytest tests
	pylint src --disable=fixme
	flake8
	mypy src
	$(MAKE) docs && export LANG=en_US.UTF-8 LC_ALL=$LANG && tar -cvf docs.tar docs

.PHONY: docs
docs:
	$(MAKE) --directory=docs html

manual_release: deploy_to_pypy
	git push -u origin main
