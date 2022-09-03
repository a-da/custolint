from typing import Callable, Dict, List

from unittest import mock

from custolint import git

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
    [('care/of/red/potato.py', 310, 'gus.fring@some-domain.com', '2021-06-25')],
    [('care/of/yellow/banana.py', 1, 'lalo.salamanca@some-domain.com', '2022-03-07'),
     ('care/of/yellow/banana.py', 2, 'lalo.salamanca@some-domain.com', '2022-03-07'),
     ('care/of/yellow/banana.py', 3, 'lalo.salamanca@some-domain.com', '2022-03-07')]

])
def test_git_changes_success(_, patch_bash: Callable):
    #
    with \
            mock.patch.object(git, '_autodetect_main_branch', return_value="main"), \
            patch_bash(
                stdout="""
                --- a/care/of/red/potato.py
                +++ b/care/of/red/potato.py
                @@ -310 +310 @@ def get_audit_log(
                -def send_mail(subject: str, body: str, recipients: List[str], cc: List[str] = None, reply_to: Optional[str] = None):
                +def send_mail(subject: str, body: str, recipients: List[str], reply_to: Optional[str] = None):
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


def test_git_changes_error(patch_bash: Callable, caplog):
    with \
            mock.patch.object(git, '_autodetect_main_branch', return_value="main"), \
            patch_bash(stderr='no git installed', code=1), \
            pytest.raises(SystemExit, match='1'):

        git.changes()

    assert caplog.messages == ['Diff command failed: no git installed']


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
            ('a/b/api/bar.py', 310, 'john.snow@some-domain.eu', '2022-05-06')
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
            ('a/b/api/bar.py', 1, 'john.snow@some-domain.eu', '2022-05-06'),
            ('a/b/api/bar.py', 2, 'john.snow@some-domain.eu', '2022-05-06'),
            ('a/b/api/bar.py', 3, 'john.snow@some-domain.eu', '2022-05-06')
        ],
        id='tow_line_numbers'
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
            ('a/b/api/bar.py', 10, 'john.snow@some-domain.eu', '2022-05-06'),
            ('a/b/api/bar.py', 11, 'john.snow@some-domain.eu', '2022-05-06'),
            ('a/b/api/bar.py', 12, 'john.snow@some-domain.eu', '2022-05-06')
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
            mock.patch.dict('os.environ', {git.BRANCH_ENV: 'main'}), \
            patch_bash(
                stdout="""
                    $ git branch -r --list origin/main
                    origin/main
                """) as bash:

        assert git._autodetect_main_branch() == 'main'
        bash.assert_called_with('git branch -r --list origin/main')


@pytest.mark.parametrize(
    'env, stderr, log_message',
    (
        pytest.param(
            {git.BRANCH_ENV: 'main'}, 'no-branch',
            "Branch name 'main' provided through OS env "
            "'CUSTOLINT_MAIN_BRANCH' can not be found in git: no-branch",
            id='override'
        ),
        pytest.param(
            {}, 'some-git-error',
            "Could not find default/main branch: 'some-git-error'",
            id='no-override'
        ),
    )
)
def test_get_main_branch_error(
        env: Dict[str, str],
        stderr: str,
        log_message: str,
        caplog: LogCaptureFixture,
        patch_bash: Callable):
    with \
            mock.patch.dict('os.environ', env, clear=True), \
            patch_bash(stderr=stderr, code=1), \
            pytest.raises(SystemExit):

        git._autodetect_main_branch()

    assert caplog.messages == [log_message]
