"""
Keep here all custom data type used within this package
"""
from pathlib import Path
from typing import Callable, Dict, NamedTuple, Sequence, TypedDict
from typing_extensions import TypeAlias


class Contributor(TypedDict):
    """Git Blame Contributor data"""
    email: str
    date: str


class SourceCode(NamedTuple):
    """Common params passed into internal API"""
    file_name: str
    line_number: int


class Blame(NamedTuple):
    """
    Full Git Blame data

    Contributor(email and date) is the same but is a Dict not a Tuple
    """
    email: str
    date: str

    # inherit from SourceCode, not possible yet
    file_name: str
    line_number: int


class Lint(NamedTuple):
    """
    Final Data Type to be reported, filtered ...
    """
    message: str

    # inherit from Blame, not possible yet
    email: str
    date: str

    # inherit from SourceCode, not possible yet
    file_name: str
    line_number: int


class Coverage(NamedTuple):
    """
    Python Coverage Data
    """
    contributor: Contributor

    # inherit from SourceCode, not possible yet
    file_name: str
    line_number: int


Changes: TypeAlias = Dict[str, Dict[int, Contributor]]

FiltersType: TypeAlias = Callable[[Path, str, int, Dict[Path, Sequence[str]]], bool]

__all__ = [
    'Changes',
    'Lint',
    'Blame',
    'Coverage',
    'FiltersType',
]
