from typing import Tuple, List, Optional, Dict

import logging
import os
import re
import sys
import tempfile
from pathlib import Path

import bash

logging.basicConfig(level=os.getenv('LOG_LEVEL') or logging.INFO)

LOG = logging.getLogger(__name__)

MAIN_BRANCH = os.getenv('MAIN_BRANCH') or 'develop'

TO_LOG = False


def output(msg, *args) -> None:

    if TO_LOG:
        LOG.info(msg, *args)
    else:
        print(msg % args)


def extract_email_and_date_from_blame(blame_line: str) -> Tuple[str, str]:
    """
    Extract email and date from blame message line
    """
    _, tail = blame_line.split("<", maxsplit=1)
    email, tail = tail.split(">", maxsplit=1)
    date, _ = tail.split(maxsplit=1)
    return email, date


def blame(the_line_number: str, file_name: str) -> Optional[Tuple[str, str, str, str]]:
    if "-" in the_line_number:
        start, ends = [int(_) for _ in the_line_number.split("-")]
        plus_start = ends - start
    elif "," in the_line_number:
        start, plus_start = [int(_) for _ in the_line_number.split(",")]
    else:
        plus_start = 1
        start = int(the_line_number)

    # git blame -L 33,+1  --show-email -- helpers/src/pipeline_sdk/helpers/service_api/metadata.py
    # 6d2056da7 (<saul.goodman@some-domain.com> 2020-06-03 14:11:42 +0200 33)     if event_count > 0:
    execute_command = f"git blame -L {start},+{plus_start} --show-email --  {file_name}"
    LOG.debug("Execute git blame command: %r", execute_command)
    command = bash.bash(execute_command)
    if command.stderr:
        LOG.error(command.stderr)
        exit(command.code)

    to_blame = command.stdout.decode()

    for index, line in enumerate(to_blame.strip().split("\n"), start=start):
        email, date = extract_email_and_date_from_blame(line)
        yield file_name, index, email, date


def mypy_compare_with_main_branch() -> None:
    LOG.info("MYPY COMPARE WITH %r branch", MAIN_BRANCH)
    changes = git_changes(MAIN_BRANCH)

    includes = re.compile(r'.py$')
    excludes = re.compile(r"/setup.py")

    paths = "\n".join(i for i in changes.keys() if includes.search(i) and not excludes.search(i))

    if not paths:
        LOG.info("No file was affected")
        return

    # mypy accept a reference to a file as an argument
    _, tmp_path = tempfile.mkstemp()
    Path(tmp_path).write_text(paths)

    has_found_something = False

    # TODO validate cmd before pass
    execute_command = (
            os.getenv("MYPY_CMD") or "mypy --strict --show-error-codes @{tmp_path}"
    ).format(tmp_path=tmp_path)

    LOG.info("execute command %r", execute_command)
    command = bash.bash(execute_command)
    if command.stderr:
        LOG.error(command.stderr)
        exit(1)

    for mypy_line in command.stdout.decode().split("\n"):
        fields = mypy_line.split(":", 3)  # filepath, line number, level, message

        if len(fields) == 4:
            file_name = fields[0]
            line_number = int(fields[1])

            contributor = changes.get(file_name, {}).get(line_number)
            if contributor:

                # FILTERS
                """
                Filter 001
                test functions always return None, make no sense to enforce return None, ignore that
                    def test_a():
                """
                if re.search(r"test_.*\.py", file_name) and "Function is missing a type annotation":
                    code_line = Path(file_name).read_text().splitlines()[line_number - 1]

                    if "def test_" in code_line:
                        continue

                # OUTPUT
                output("%s %s", mypy_line, contributor)
            else:
                LOG.debug(mypy_line)

        elif fields == [""]:
            LOG.debug(mypy_line)
        else:
            if "/test/conftest.py" in mypy_line:
                if "Duplicate module named" in mypy_line:
                    continue
                if "Are you missing an __init__.py" in mypy_line:
                    continue

            if not has_found_something and re.search(r"Found \d+ errors in \d+ file", mypy_line):
                continue

            print("something wrong ", len(fields), mypy_line, fields)

    if not has_found_something:
        print("::Dry and Clean::")


def pylint_filter(pylint_line: str) -> bool:
    """
    Return True if we want to skip the check else False if we want this check
    """
    if "Line too long" in pylint_line:
        return True

    # special rules for test folders
    if "/test_" in pylint_line:
        if "(missing-function-docstring)" in pylint_line:
            return True

        if " function (no-self-use)" in pylint_line:
            return True

        if " (missing-module-docstring)" in pylint_line:
            return True

        if " (protected-access)" in pylint_line:
            return True

    if re.search(r"TODO: SPACE-\d+: ", pylint_line):  # ignore all TODO's marked with Jira reference
        return True

    return False


def pylint_parse_message_line(message: str) -> Optional[Tuple[str, str]]:
    """
    >> pylint_parse_message_line("cli/test/test_cli.py:100:4:")
    (cli/test/test_cli.py, 100)
    """
    # cli/test/test_cli.py:100:4:
    match = re.search(r"(^.+?):(\d+):(\d+):", message)
    if match:
        file_name = match.group(1)
        line_number = match.group(2)
        return file_name, line_number

    return None


def generic_lint_compare_with_main_branch(execute_command: str) -> None:
    has_found_something = False
    changes = git_changes(MAIN_BRANCH)

    includes = re.compile(r'.py$')
    excludes = re.compile(r"/setup.py")

    paths = list(i for i in changes.keys() if includes.search(i) and not excludes.search(i))

    LOG.info("Execute lint commands %r for %r files ...", execute_command, len(paths))
    for lint_file in paths:  # TODO make parallel per path
        execute_command_ = execute_command.format(lint_file=lint_file)
        LOG.debug("Execute lint command: %r", execute_command_)
        command = bash.bash(execute_command_)
        for pylint_line in command.stdout.decode().split("\n"):
            if pylint_filter(pylint_line):
                continue

            file_name_line_number = pylint_parse_message_line(pylint_line)
            if file_name_line_number:
                file_name, line_number = file_name_line_number
                contributor = changes.get(file_name, {}).get(int(line_number))
                if contributor:
                    has_found_something = True
                    output("%s %s", pylint_line, contributor)
            else:
                if not pylint_line.strip("-"):
                    continue
                if pylint_line.startswith("Your code has been rated at "):
                    continue
                if pylint_line.startswith("*****"):
                    continue

                LOG.error("Can not parse lint line", pylint_line)

    if not has_found_something:
        LOG.info("::Dry and Clean::")


def pylint_compare_with_main_branch() -> None:
    generic_lint_compare_with_main_branch("pylint {lint_file}")


def flake8_compare_with_main_branch() -> None:
    generic_lint_compare_with_main_branch("flake8 {lint_file}")


def git_changes(main_branch: str) -> Dict[str, List[str]]:

    files: Dict[str, Dict[int, Dict[str, str]]] = {}

    the_file = None
    execute_command = f"git diff origin/{main_branch} -U0 --diff-filter=ACMRTUXB"
    LOG.info("Execute git diff command %r", execute_command)
    command = bash.bash(execute_command)
    for line in command.stdout.decode().split("\n"):

        # line like +++ b/care/share/calc/_methods2.py
        if line.startswith("+++ "):
            _, the_file = line.split("+++ ", maxsplit=1)
            the_file = the_file[2:]
            continue

        # line like @@ -0,0 +1,146 @@
        if line.startswith("@@"):
            affected_lines = line.split("+", maxsplit=1)[1].split(maxsplit=1)[0]

            if affected_lines.endswith(",0"):  # the line is deleted and have to be ignored
                continue

            for file_name, index, email, date in blame(
                    the_line_number=affected_lines,
                    file_name=the_file):

                if the_file not in files:
                    files[the_file] = {}

                files[the_file][index] = {
                    'email': email,
                    'date': date
                }

    return files


def coverage_compare_with_main_branch(include_path: str) -> None:
    changes = git_changes(MAIN_BRANCH)

    header = None
    has_found_something = False

    execute_command = f"coverage report --show-missing --include=space/*"
    LOG.info('execute coverage command: %r', execute_command)
    command = bash.bash(execute_command)

    for coverage_line in command.stdout.decode().split("\n"):

        if not coverage_line:
            continue

        # how looks a coverage line ?
        fields = coverage_line.split()

        # header is alike 'Name    Stmts   Miss Branch BrPart  Cover   Missing'
        if coverage_line.startswith("Name "):
            continue

        # footer
        if coverage_line.startswith('TOTAL '):
            continue

        # alike 'care/__init__.py 6 0 0 0 100%'
        if fields[-1] == "100%":
            continue

        # alike 'b.py 104 16 40 9  81% 54-59, 63, 182, 220, 257, 277-278, 357-360, 383, 406
        if len(fields) > 4 and "Missing" not in fields[-1]:
            missing_coverage_lines = "".join(fields[6:]).split(",")

            for missing in missing_coverage_lines:
                # cli/test/test_cli.py:100:4:

                file_name = fields[0]

                # if "/test_" in file_name:
                #     continue

                if "-" in missing:
                    if missing.endswith("->exit"):  # alike '8->exit'
                        start, _ = missing.split("->exit")
                        end = int(start) + 1
                    elif ">" in missing:  # alike '278->280'
                        start, end = missing.split("->")
                    else:  # alike 36-935
                        start, end = missing.split("-")
                else:
                    start = int(missing)
                    end = start + 1

                start_end = list(range(int(start), int(end)))

                for line_number in start_end:
                    contributor = changes.get(file_name, {}).get(int(line_number))
                    if contributor:
                        LOG.info("%s %s:%s", contributor, file_name, line_number)

    if not has_found_something:
        print("::Dry and Clean::")


def main(*args):
    if len(args) < 2:
        sys.exit("require one of argument: mypy, pylint, flake8, coverage")

    command = args[1]
    if command == "mypy":
        mypy_compare_with_main_branch()
    elif command == "pylint":
        pylint_compare_with_main_branch()
    elif command == "flake8":
        flake8_compare_with_main_branch()
    elif command == "coverage":
        if len(args) < 3:
            sys.exit('include path for coverage is missing')

        coverage_file_location = args[2]
        coverage_compare_with_main_branch(coverage_file_location)
    else:
        sys.exit(f'command {command!r} not implemented')


if __name__ == "__main__":
    main(*sys.argv)
