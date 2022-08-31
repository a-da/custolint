from typing import List
import os
from pathlib import Path
from unittest import mock

import custolint
import custolint.git

import pytest


@pytest.fixture(autouse=True, scope='session')
def cd_into_root():
    os.chdir(Path(__file__).parent.parent)


@pytest.mark.parametrize("blame, email, date", [
    (
        '<gus.fring@some-domain.com> 2021-09-06 14:21:52 +0000 '
        '61)     def value_to_pandas(value) -> pd.Period:"',
        "gus.fring@some-domain.com",
        "2021-09-06"
    )
])
def test_extract_email_and_date_from_blame(blame: str, email: str, date: str):
    assert custolint.git._extract_email_and_date_from_blame(blame) == (
        'gus.fring@some-domain.com', '2021-09-06'
    )


@mock.patch.object(custolint.git.bash, "bash", side_effect=[
    mock.Mock(
        stderr=b"",
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
""".encode())],
)
@mock.patch.object(custolint.git, "_blame", side_effect=[
    [('care/of/red/potato.py', 310, 'gus.fring@some-domain.com', '2021-06-25')],
    [('care/of/yellow/banana.py', 1, 'lalo.salamanca@@some-domain.com', '2022-03-07'),
     ('care/of/yellow/banana.py', 2, 'lalo.salamanca@@some-domain.com', '2022-03-07'),
     ('care/of/yellow/banana.py', 3, 'lalo.salamanca@@some-domain.com', '2022-03-07')]

])
def test_git_changes(_, _2):
    assert custolint.git.changes(main_branch="develop") == {
        'care/of/red/potato.py': {
            310: {'date': '2021-06-25', 'email': 'gus.fring@some-domain.com'}},
        'care/of/yellow/banana.py': {
            1: {'date': '2022-03-07', 'email': 'lalo.salamanca@@some-domain.com'},
            2: {'date': '2022-03-07', 'email': 'lalo.salamanca@@some-domain.com'},
            3: {'date': '2022-03-07', 'email': 'lalo.salamanca@@some-domain.com'}
        }
    }


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
def test_blame(file_name: str,
               the_line_numbers: List[str],
               bash_stdout: str,
               git_command: str, expect):

    for the_line_number in the_line_numbers:
        with mock.patch.object(custolint.git.bash, "bash", side_effect=[mock.Mock(
                stdout=bash_stdout.encode(),
                stderr='',
        )]) as mocked_bash:

            assert list(custolint.git._blame(the_line_number, file_name)) == expect
            mocked_bash.assert_called_once_with(git_command)


def test_blame_with_command_error():
    with mock.patch.object(custolint.git.bash, "bash", side_effect=[mock.Mock(
            stderr=b'some_error',
    )]), pytest.raises(SystemExit):
        next(custolint.git._blame('1', "a.py"))
