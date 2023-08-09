from pathlib import Path
from typing import Callable, List, Optional

import logging
from contextlib import nullcontext as does_not_raise
from unittest import mock

from custolint import _typing  # noqa: protected member
from custolint import git

import pytest
from _pytest.logging import LogCaptureFixture


@mock.patch.object(git, "_blame", side_effect=[
    [
        _typing.Blame(
            author='John Snow',
            file_name='care/of/red/potato.py',
            line_number=310,
            email='gus.fring@some-domain.com',
            date='2021-06-25'
        )
    ],
    [
        _typing.Blame(
            author='John Snow',
            file_name='care/of/yellow/banana.py',
            line_number=i,
            email='lalo.salamanca@some-domain.com',
            date='2022-03-07'
        ) for i in [1, 2, 3]
    ]
])
def test_git_changes_success(_, patch_bash: Callable, _autodetect: mock.Mock):
    with \
            _autodetect, \
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

        git_changes = git.changes(do_pull_rebase=False)

        assert git_changes == {
            'care/of/red/potato.py': {
                310: {
                    'author': 'John Snow',
                    'date': '2021-06-25',
                    'email': 'gus.fring@some-domain.com'
                }},
            'care/of/yellow/banana.py': {
                1: {
                    'author': 'John Snow',
                    'date': '2022-03-07',
                    'email': 'lalo.salamanca@some-domain.com'
                },
                2: {
                    'author': 'John Snow',
                    'date': '2022-03-07',
                    'email': 'lalo.salamanca@some-domain.com'
                },
                3: {
                    'author': 'John Snow',
                    'date': '2022-03-07',
                    'email': 'lalo.salamanca@some-domain.com'
                }
            }
        }


def test_git_changes_error(patch_bash: Callable, caplog: LogCaptureFixture, _autodetect: mock.Mock):
    with \
            _autodetect, \
            patch_bash(stderr='no git installed', code=1), \
            pytest.raises(SystemExit, match='1'):

        git.changes(do_pull_rebase=False)

    assert caplog.messages == ['Diff command failed: no git installed']


def test_git_changes_debug_enabled(patch_bash: Callable,
                                   caplog: LogCaptureFixture,
                                   _autodetect: mock.Mock):
    with \
            _autodetect, \
            mock.patch.object(git.LOG, 'isEnabledFor', return_value=True), \
            patch_bash(stdout='some message about diff'):

        git.changes(do_pull_rebase=False)

    assert caplog.messages[2] == 'Git diff output some message about diff'


GIT_BLAME_PORCELAIN_1_3_OUTPUT = (
    "005661f440bcdfefb2fd41d4e781351471dfb3ef 1 1 2\n"
    "author John Snow\n"
    "author-mail <john.snow@some-domain.eu>\n"
    "author-time 1661418629\n"
    "author-tz +0200\n"
    "committer John Snow\n"
    "committer-mail <john.snow@some-domain.eu>\n"
    "committer-time 1661418629\n"
    "committer-tz +0200\n"
    "summary make custolint installable\n"
    "filename  a/b/api/bar.py\n"
    "        [metadata]\n"

    "005661f440bcdfefb2fd41d4e781351471dfb3ef 2 2\n"
    "author John Snow\n"
    "author-mail <john.snow@some-domain.eu>\n"
    "author-time 1661418629\n"
    "author-tz +0200\n"
    "committer John Snow\n"
    "committer-mail <john.snow@some-domain.eu>\n"
    "committer-time 1661418629\n"
    "committer-tz +0200\n"
    "summary make custolint installable\n"
    "filename  a/b/api/bar.py\n"
    "        name = custolint\n"

    "8a82ba664ee030ce7ed156972f1f5e364fb8f8a3 3 3 1\n"
    "author John Snow\n"
    "author-mail <john.snow@some-domain.eu>\n"
    "author-time 1661418629\n"
    "author-tz +0200\n"
    "committer John Snow\n"
    "committer-mail <john.snow@some-domain.eu>\n"
    "committer-time 1686748144\n"
    "committer-tz +0200\n"
    "summary Version 0.2.1: properly handling cli and add color features\n"
    "previous 6241256b9d5e8b37788f67bf5743b345c27badd6  a/b/api/bar.py\n"
    "filename  a/b/api/bar.py\n"
    "        version = 0.2.1\n"
)


@pytest.mark.parametrize("file_name, the_line_numbers, bash_stdout, git_command, expect", [
    pytest.param(
        'a/b/api/bar.py',
        ["310"],
        (
            "005661f440bcdfefb2fd41d4e781351471dfb3ef 26 310 1\n"
            "author John Snow\n"
            "author-mail <john.snow@some-domain.eu>\n"
            "author-time 1661418629\n"
            "author-tz +0200\n"
            "committer John Snow\n"
            "committer-mail <john.snow@some-domain.eu>\n"
            "committer-time 1661418629\n"
            "committer-tz +0200\n"
            "summary make custolint installable\n"
            "filename a/b/api/bar.py\n"
            "def foo(subject: str, reply_to: Optional[str] = None):"
        ),
        'git blame --line-porcelain -L 310,+1 -- /path/to/git/a/b/api/bar.py',
        [
            _typing.Blame(
                author='John Snow',
                file_name='a/b/api/bar.py',
                line_number=310,
                email='john.snow@some-domain.eu',
                date='2022-08-25'
            )
        ],
        id='concrete_line_number'
    ),
    pytest.param(
        'a/b/api/bar.py', ["1,3"],
        GIT_BLAME_PORCELAIN_1_3_OUTPUT,
        'git blame --line-porcelain -L 1,+3 -- /path/to/git/a/b/api/bar.py',
        [
            _typing.Blame(
                author='John Snow',
                file_name='a/b/api/bar.py',
                line_number=i,
                email='john.snow@some-domain.eu',
                date='2022-08-25'
            ) for i in [1, 2, 3]
        ],
        id='two_line_numbers'
    ),
    pytest.param(
        'a/b/api/bar.py', ["1-3"],
        GIT_BLAME_PORCELAIN_1_3_OUTPUT,
        'git blame --line-porcelain -L 1,+2 -- /path/to/git/a/b/api/bar.py',
        [
            _typing.Blame(
                author='John Snow',
                file_name='a/b/api/bar.py',
                line_number=i,
                email='john.snow@some-domain.eu',
                date='2022-08-25'
            ) for i in [1, 2, 3]
        ],
        id='ranges'
    ),
])
def test_blame(file_name: str,  # pylint: disable=too-many-arguments
               the_line_numbers: List[str],
               bash_stdout: str,
               git_command: str,
               expect: List,
               patch_bash: Callable):

    for the_line_number in the_line_numbers:
        with patch_bash(stdout=bash_stdout, stderr='',) as bash:

            blame = list(git._blame(
                root_dir=Path('/path/to/git'),
                line_number=the_line_number,
                file_name=file_name
            ))
            assert blame == expect
            bash.assert_called_once_with(git_command)


def test_blame_with_command_error(patch_bash: Callable):
    with \
            patch_bash(stderr='some_error', code=1),\
            pytest.raises(SystemExit):

        next(git._blame(
            root_dir=Path('/path/to/git'),
            line_number='1',
            file_name="a.py"
        ))


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
        bash.side_effect = [
            mock.Mock(
                stdout=b'/path/to/git',
                stderr='',
                code=0
            )
        ] + list(bash.side_effect)

        assert git._autodetect() == (Path('/path/to/git'), 'main')
        bash.assert_called_with('git remote show origin')


def test_get_main_branch_override(patch_bash: Callable):
    with \
            mock.patch.object(git.env, 'BRANCH_NAME', 'main'), \
            patch_bash(
                stdout="""
                    $ git branch -r --list origin/main
                    origin/main
                """) as bash:
        bash.side_effect = [
            mock.Mock(
                stdout=b'/path/to/git',
                stderr='',
                code=0
            )
        ] + list(bash.side_effect)

        assert git._autodetect() == (Path('/path/to/git'), 'main')
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
            patch_bash(stderr=stderr, code=1) as bash, \
            pytest.raises(SystemExit):

        bash.side_effect = [
            mock.Mock(
                stdout=b'/path/to/git',
                stderr='',
                code=0
            )
        ] + list(bash.side_effect)

        git._autodetect()

    assert caplog.messages == [log_message]


def test_autodetect_not_a_git_repository(patch_bash: Callable):
    with \
            patch_bash(
                stderr='fatal: not a git repository (or any of the parent directories): .git',
                code=128
            ), \
            pytest.raises(SystemExit):

        git._autodetect()


@pytest.mark.parametrize(
    'stdout, stderr, code, raise_expect, log_messages',
    (
        pytest.param(
            'git version 2.39.2 (Apple Git-143)',
            '',
            0,
            does_not_raise(),
            [],
            id='equal'
        ),
        pytest.param(
            'git version 200.39.2 (Apple Git-143)',
            '',
            0,
            does_not_raise(),
            [],
            id='greater'
        ),
        pytest.param(
            'git version 2.39.0 (Apple Git-143)',
            '',
            0,
            does_not_raise(),
            ["Be aware that current git version (2, 39, 0) is less than recommended (2, 39, 2)"],
            id='lower'
        ),
        pytest.param(
            '',
            'git: command not found',
            127,
            pytest.raises(SystemExit, match='127'),
            ['Could not find git version name: git: command not found'],
            id='command-not-found'
        ),
    )
)
def test_check_git_version(  # pylint: disable=too-many-arguments
        stdout: Optional[str],
        stderr: str,
        code: int,
        raise_expect,
        log_messages: List[str],
        caplog: LogCaptureFixture,
        patch_bash: Callable):
    with patch_bash(stdout=stdout, stderr=stderr, code=code):
        with raise_expect:
            git._check_git_version()

    assert caplog.messages == log_messages


@pytest.mark.parametrize(
    'stdout, stderr, code, raise_expect, log_messages',
    (
        pytest.param(
            'NASA-124-improve_xxx',
            '',
            0,
            does_not_raise(),
            [],
            id='NASA-124-improve_xxx'
        ),
        pytest.param(
            '',
            'git: command not found',
            127,
            pytest.raises(SystemExit, match='127'),
            ['Could not find branch name: git: command not found'],
            id='command-not-found'
        ),
    )
)
def test_current_branch_name(  # pylint: disable=too-many-arguments
        stdout: Optional[str],
        stderr: str,
        code: int,
        raise_expect,
        log_messages: List[str],
        caplog: LogCaptureFixture,
        patch_bash: Callable):
    with patch_bash(stdout=stdout, stderr=stderr, code=code):
        with raise_expect:
            assert 'NASA-124-improve_xxx' == git._current_branch_name()

    assert caplog.messages == log_messages


@pytest.mark.parametrize(
    'stdout, stderr, code, log_messages',
    (
        pytest.param(
            '\n'.join((
                'From https://a.b.c/d/cfw/d-lib',
                ' * branch                master    -> FETCH_HEAD',
                'Successfully rebased and updated refs/heads/NASA-29550-Report_missing_series'
            )),
            '',
            0,
            [
                "Execute git pull --rebase command 'git pull --rebase origin master'",
                'git pull: From https://a.b.c/d/cfw/d-lib\n'
                ' * branch                master    -> FETCH_HEAD\n'
                'Successfully rebased and updated refs/heads/NASA-29550-Report_missing_series',

                'HINTS: revert pull with: \n'
                '>>> git reset --hard origin/NASA-29550-Report_missing_series'
            ],
            id='NASA-29550'
        ),
        pytest.param(
            '',
            'git: command not found',
            127,
            [
                "Execute git pull --rebase command 'git pull --rebase origin master'",
                'Pull command failed: git: command not found'
            ],
            id='command-not-found'
        ),
    )
)
def test_pull_rebase(  # pylint: disable=too-many-arguments
        stdout: Optional[str],
        stderr: str,
        code: int,
        log_messages: List[str],
        caplog: LogCaptureFixture,
        patch_bash: Callable):
    with caplog.at_level(logging.INFO):
        caplog.clear()
        with patch_bash(stdout=stdout, stderr=stderr, code=code):
            git._pull_rebase('master', 'NASA-29550-Report_missing_series')

    assert caplog.messages == log_messages


def test_git_sync_success(patch_bash: Callable):
    with patch_bash() as mocked:
        mocked.side_effect = [
            mock.Mock(
                stdout=b"git version 2.39.2 (Apple Git-143)",
                code=0,
            ),
            mock.Mock(
                stdout=b"* main",
                code=0,
            ),
            mock.Mock(
                stdout=(" From github.com:a-da/custolint\n"
                        "  * branch            main       -> FETCH_HEAD\n"
                        " Already up to date.\n").encode(),
                code=0,
            )
        ]
        git._git_sync(True, 'name')
