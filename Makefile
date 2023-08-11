IGNORE_ERROR_EXIT ?= false

update_pip_and_wheel:
	pip install -U pip wheel

wheel: clean
	python -m build . --wheel

deploy_to_pypy: wheel validate
	echo 'deploy have to be done by CI/CD pipeline' && exit 1
	twine upload dist/*

clean:
	rm -rvf ./build/ ./dist/ .coverage ./src/custolint.egg-info/ README.html ./.mypy_cache/
	rm -rvf	./.pytest_cache/ ./tests/.pytest_cache/ ./htmlcov/
	$(MAKE) --directory=docs clean_docs
	rm -f docs.tar

install:
	pip install custolint

install_dev:
	pip install -U pip wheel
	pip install -e ".[dev,deploy_to_pip]"

.PHONY: tests
tests:
	pytest tests

coverage_tests:
	coverage run --rcfile=config.d/.coveragerc -m pytest

custolint_validate:
	$(MAKE) coverage_tests
	custolint coverage --data-file=.coverage
	@echo
	custolint pylint
	@echo
	custolint flake8
	@echo
	custolint mypy

isort:
	isort src test

validate: custolint_validate
	$(MAKE) tests
	$(MAKE) isort
	pylint src --disable=fixme
	flake8 src
	mypy src
	$(MAKE) docs

introduce_chaos:
	# introduce modifications
	echo '' >> src/custolint/flake8.py

	echo 'CHECK = True' >> src/custolint/mypy.py
	echo 'CHECK = "False"' >> src/custolint/mypy.py

	echo 'import os' >> src/custolint/pylint.py


.PHONY: docs
docs:
	# save snapshot
	git stash save insert_chaos2 # -1- create snapshot
	git stash apply stash@{0} || exit 0  #-2- return to snapshot version

	$(MAKE) introduce_chaos

	$(MAKE) --directory=docs html

	# -3- save modification to drop them
	git stash save tmp
	# -4- return to snapshot version from -1-
	git stash apply stash@{1} || exit 0

	git stash drop stash@{0}
	git stash drop stash@{0} || exit 0

manual_release: deplolsy_to_pypy
	git push -u origin main
