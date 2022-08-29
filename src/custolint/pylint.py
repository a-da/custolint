from pathlib import Path
from . import generics


def compare_with_main_branch() -> None:
    config_argument = "--rcfile=config.d/pylintrc" if Path("config.d/pylintrc").exists() else ""
    command = " ".join(("pylint", config_argument, "{lint_file}"))
    generics.lint_compare_with_main_branch(command)
