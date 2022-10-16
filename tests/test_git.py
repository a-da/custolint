from typing import Callable, List, Optional

from unittest import mock

from custolint import git, typing

import pytest
from _pytest.logging import LogCaptureFixture


@pytest.mark.parametrize("blame", [
    (
        '<gus.fring@some-domain.com> 2021-09-06 14:21:52 +0000 '
        '61)     def value_to_pandas(value) -> pd.Period:"'
    ),
])
def test_extract_email_and_date_from_blame(blame: str):
    assert git._extract_email_and_date_from_blame(blame) == (
        'gus.fring@some-domain.com', '2021-09-06'
    )


@mock.patch.object(git, "_blame", side_effect=[
    [
        typing.Blame(
            file_name='care/of/red/potato.py',
            line_number=310,
            email='gus.fring@some-domain.com',
            date='2021-06-25'
        )
    ],
    [
        typing.Blame(
            file_name='care/of/yellow/banana.py',
            line_number=i,
            email='lalo.salamanca@some-domain.com',
            date='2022-03-07'
        ) for i in [1, 2, 3]
    ]
])
def test_git_changes_success(_, patch_bash: Callable):
    with \
            mock.patch.object(git, '_autodetect_main_branch', return_value="main"), \
            patch_bash(
                stdout="""
                --- a/care/of/red/potato.py
                +++ b/care/of/red/potato.py
                @@ -310 +310 @@ def get_audit_log(
                -def send_mail(subject: str, body: str, ..., cc: List[str] = None, reply_to: Optional[str] = None):
                +def send_mail(subject: str, body: str, ..., reply_to: Optional[str] = None):
                @@ -321,2 +320,0 @@ def send_mail(subject: str, body: str, recipients: List[str], cc: List[str] = No
                -    cc: List[str]
                -        List of email addresses to be included as CC. Empty list by default.
                @@ -340,3 +337,0 @@ def send_mail(subject: str, body: str, recipients: List[str], cc: List[str] = No
                -    if cc:
                -        json["cc"] = ",".join(cc)
                -
                diff --git a/care/of/yellow/banana.py b/care/of/yellow/banana.py
                new file mode 100644
                index 000000000..e0ae31a74
                --- /dev/null
                +++ b/care/of/yellow/banana.py
                @@ -0,0 +1,146 @@
                """):

        assert git.changes() == {
            'care/of/red/potato.py': {
                310: {'date': '2021-06-25', 'email': 'gus.fring@some-domain.com'}},
            'care/of/yellow/banana.py': {
                1: {'date': '2022-03-07', 'email': 'lalo.salamanca@some-domain.com'},
                2: {'date': '2022-03-07', 'email': 'lalo.salamanca@some-domain.com'},
                3: {'date': '2022-03-07', 'email': 'lalo.salamanca@some-domain.com'}
            }
        }


def test_git_changes_error(patch_bash: Callable, caplog: LogCaptureFixture):
    with \
            mock.patch.object(git, '_autodetect_main_branch', return_value="main"), \
            patch_bash(stderr='no git installed', code=1), \
            pytest.raises(SystemExit, match='1'):

        git.changes()

    assert caplog.messages == ['Diff command failed: no git installed']


def test_git_changes_debug_enabled(patch_bash: Callable, caplog: LogCaptureFixture):
    with \
            mock.patch.object(git, '_autodetect_main_branch', return_value="main"), \
            mock.patch.object(git.LOG, 'isEnabledFor', return_value=True), \
            patch_bash(stdout='some message about diff'):

        git.changes()

    assert caplog.messages[2] == 'Git diff output some message about diff'


@pytest.mark.parametrize("file_name, the_line_numbers, bash_stdout, git_command, expect", [
    pytest.param(
        'a/b/api/bar.py',
        ["310"],
        (
            "938a7025ba (<john.snow@some-domain.eu> 2022-05-06 08:11:20 +0000 310) "
            "def foo(subject: str, reply_to: Optional[str] = None):"
        ),
        'git blame -L 310,+1 --show-email --  a/b/api/bar.py',
        [
            typing.Blame(
                file_name='a/b/api/bar.py',
                line_number=310,
                email='john.snow@some-domain.eu',
                date='2022-05-06'
            )
        ],
        id='concrete_line_number'
    ),
    pytest.param(
        'a/b/api/bar.py', ["1,3"],
        (
            "938a7025ba (<john.snow@some-domain.eu> 2022-05-06 08:11:20 +0000 1) "
            "def foo(subject: str, reply_to: Optional[str] = None):\n"
            "1435a446cd (<john.snow@some-domain.eu> 2022-05-06 08:11:20 +0000 2) "
            "    a = 1\n"
            "ac24534653 (<john.snow@some-domain.eu> 2022-05-06 08:11:20 +0000 3) "
            "    return a"
        ),
        'git blame -L 1,+3 --show-email --  a/b/api/bar.py',
        [
            typing.Blame(
                file_name='a/b/api/bar.py',
                line_number=i,
                email='john.snow@some-domain.eu',
                date='2022-05-06'
            ) for i in [1, 2, 3]
        ],
        id='two_line_numbers'
    ),
    pytest.param(
        'a/b/api/bar.py', ["10-23"],
        (
            "938a7025ba (<john.snow@some-domain.eu> 2022-05-06 08:11:20 +0000 1) "
            "def foo(subject: str, reply_to: Optional[str] = None):\n"
            "1435a446cd (<john.snow@some-domain.eu> 2022-05-06 08:11:20 +0000 2) "
            "    a = 1\n"
            "ac24534653 (<john.snow@some-domain.eu> 2022-05-06 08:11:20 +0000 3) "
            "    return a"
        ),
        'git blame -L 10,+13 --show-email --  a/b/api/bar.py',
        [
            typing.Blame(
                file_name='a/b/api/bar.py',
                line_number=i,
                email='john.snow@some-domain.eu',
                date='2022-05-06'
            ) for i in [10, 11, 12]
        ],
        id='range_of_line_numbers'
    )
])
def test_blame(file_name: str,  # pylint: disable=too-many-arguments
               the_line_numbers: List[str],
               bash_stdout: str,
               git_command: str,
               expect: List,
               patch_bash: Callable):

    for the_line_number in the_line_numbers:
        with patch_bash(stdout=bash_stdout, stderr='',) as bash:

            assert list(git._blame(the_line_number, file_name)) == expect
            bash.assert_called_once_with(git_command)


def test_blame_with_command_error(patch_bash: Callable):
    with \
            patch_bash(stderr='some_error', code=1),\
            pytest.raises(SystemExit):

        next(git._blame('1', "a.py"))


def test_get_main_branch_default(patch_bash: Callable):
    with patch_bash(stdout="""
        $ git remote show origin
        * remote origin
          Fetch URL: git@github.com:a-da/custolint.git
          Push  URL: git@github.com:a-da/custolint.git
          HEAD branch: main
          Remote branch:
            main tracked
          Local branch configured for 'git pull':
            main merges with remote main
          Local ref configured for 'git push':
            main pushes to main (up to date)
    """) as bash:

        assert git._autodetect_main_branch() == 'main'
        bash.assert_called_with('git remote show origin')


def test_get_main_branch_override(patch_bash: Callable):
    with \
            mock.patch.object(git.env, 'BRANCH_NAME', 'main'), \
            patch_bash(
                stdout="""
                    $ git branch -r --list origin/main
                    origin/main
                """) as bash:

        assert git._autodetect_main_branch() == 'main'
        bash.assert_called_with('git branch -r --list origin/main')


@pytest.mark.parametrize(
    'branch_name, stderr, log_message',
    (
        pytest.param(
            'main', 'no-branch',
            "Branch name 'main' provided through OS env "
            "'CUSTOLINT_MAIN_BRANCH' can not be found in git: no-branch",
            id='override'
        ),
        pytest.param(
            '', 'some-git-error',
            "Could not find default/main branch: 'some-git-error'",
            id='no-override'
        ),
    )
)
def test_get_main_branch_error(
        branch_name: Optional[str],
        stderr: str,
        log_message: str,
        caplog: LogCaptureFixture,
        patch_bash: Callable):
    with \
            mock.patch.object(git.env, 'BRANCH_NAME', branch_name), \
            patch_bash(stderr=stderr, code=1), \
            pytest.raises(SystemExit):

        git._autodetect_main_branch()

    assert caplog.messages == [log_message]
