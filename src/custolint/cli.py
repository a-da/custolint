"""
Command line interface API
"""
import sys

from . import coverage, flake8, generics, mypy, pylint


def cli(*args: str) -> None:
    """
    CLI entry point
    """
    if not args:
        args = tuple(sys.argv)

    if len(args) < 2:
        sys.exit("Require one of argument: mypy, pylint, flake8, coverage")

    command = args[1]
    if command == "mypy":
        generics.filer_output(mypy.compare_with_main_branch())
        return

    if command == "pylint":
        generics.filer_output(pylint.compare_with_main_branch())
        return

    if command == "flake8":
        generics.filer_output(flake8.compare_with_main_branch())
        return

    if command == "coverage":
        if len(args) < 3:
            sys.exit('Path for coverage is missing, usually it is `.coverage`')

        coverage_file_location = args[2]
        generics.group_by_email_and_file_name(
            coverage.compare_with_main_branch(coverage_file_location)
        )
        return

    sys.exit(f'The command {command!r} is not implemented')
