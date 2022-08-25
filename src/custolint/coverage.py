import bash
import logging

from . import git

LOG = logging.getLogger(__name__)


def compare_with_main_branch(coverage_file_location: str) -> None:
    """
    :param coverage_file_location: TODO: use it
    :return:
    """
    changes = git.changes(git.MAIN_BRANCH)

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
