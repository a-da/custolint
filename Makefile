IGNORE_ERROR_EXIT ?= false

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
	coverage run --source="src/custolint" --branch -m pytest
	custolint coverage .coverage || $(IGNORE_ERROR_EXIT)
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
