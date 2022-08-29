from pathlib import Path

from . import generics


def compare_with_main_branch() -> None:
    config_argument = "--config=config.d/.flake8" if Path("config.d/.flake8").exists() else ""
    command = " ".join(("flake8", config_argument, "{lint_file}"))
    generics.lint_compare_with_main_branch(command)
