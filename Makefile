MAIN_BRANCH := main

update_pip:
	pip install -U pip wheel

wheel: clean
	python -m build . --wheel

deploy_to_pypy: wheel # validate
	twine upload dist/*

clean:
	rm -rvf ./build ./dist .coverage ./src/custolint.egg-info/

install:
	pip install custolint

install_dev:
	pip install -e .[dev,deploy_to_pip]

custolint_validate:
	rm -f .coverage
	coverage run --branch -m pytest
	MAIN_BRANCH=$(MAIN_BRANCH) custolint coverage .coverage
	echo
	MAIN_BRANCH=$(MAIN_BRANCH) custolint pylint
	echo
	MAIN_BRANCH=$(MAIN_BRANCH) custolint flake8
	echo
	MAIN_BRANCH=$(MAIN_BRANCH) custolint mypy


validate: custolint_validate
	pytest tests
	pylint src --disable=fixme
	flake8
	mypy src
