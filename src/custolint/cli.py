import sys

from . import mypy
from . import pylint
from . import flake8
from . import coverage


def cli(*args: str) -> None:
    if not args:
        args = sys.argv

    if len(args) < 2:
        sys.exit("require one of argument: mypy, pylint, flake8, coverage")

    command = args[1]
    if command == "mypy":
        mypy.compare_with_main_branch()
    elif command == "pylint":
        pylint.compare_with_main_branch()
    elif command == "flake8":
        flake8.compare_with_main_branch()
    elif command == "coverage":
        if len(args) < 3:
            sys.exit('include path for coverage is missing')

        coverage_file_location = args[2]
        coverage.compare_with_main_branch(coverage_file_location)
    else:
        sys.exit(f'command {command!r} not implemented')
