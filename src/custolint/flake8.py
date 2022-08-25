from . import generics


def compare_with_main_branch() -> None:
    generics.lint_compare_with_main_branch("flake8 {lint_file}")
