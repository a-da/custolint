update_pip:
	pip install -U pip wheel

wheel: clean
	python -m build . --wheel

deploy_to_pypy: wheel
	twine upload dist/*

clean:
	rm -rvf ./build ./dist .coverage ./src/custolint.egg-info/

install:
	pip install custolint

install_dev:
	pip install -e .[dev,deploy_to_pip]

validate:
	coverage run -m pytest
	MAIN_BRANCH='master' custolint coverage .
	MAIN_BRANCH='master' custolint pylint
	MAIN_BRANCH='master' custolint flake8
	MAIN_BRANCH='master' custolint mypy
