update_pip:
	pip install -U pip wheel

wheel: clean
	python -m build . --wheel

deploy_to_pypy: validate wheel
	twine upload dist/*

clean:
	rm -rvf ./build ./dist .coverage ./src/custolint.egg-info/

install:
	pip install custolint

install_dev:
	pip install -e .[dev,deploy_to_pip]

validate:
	rm -f .coverage
	coverage run --branch -m pytest
	MAIN_BRANCH='master' custolint coverage .coverage
	echo
	MAIN_BRANCH='master' custolint pylint
	echo
	MAIN_BRANCH='master' custolint flake8
	echo
	MAIN_BRANCH='master' custolint mypy
