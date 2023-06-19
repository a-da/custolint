"""
Keep here all custom data type used within this package
"""
from typing import (Callable, Dict, NamedTuple, Sequence, Tuple, TypedDict,
                    Union)

from datetime import datetime
from pathlib import Path

from typing_extensions import TypeAlias


class Contributor(TypedDict):
    """Git Blame Contributor data"""
    email: str
    author: str
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
    author: str
    date: str

    # inherit from SourceCode, not possible yet
    file_name: str
    line_number: int

    @classmethod
    def from_porcelain(cls, porcelain: Tuple[str, ...]) -> 'Blame':
        """
        Convert git blame chunk output into a blame object
        """
        line_number = int(porcelain[0].split()[2])

        author = porcelain[1].replace('author ', '')

        email = porcelain[2].split('<')[1].split('>')[0]

        date = datetime.utcfromtimestamp(
            int(porcelain[3].replace('author-time ', ''))
        ).strftime('%Y-%m-%d')

        file_name = porcelain[10].split()[-1]

        return cls(
            author=author,
            email=email,
            date=date,
            file_name=file_name,
            line_number=line_number
        )


class Lint(NamedTuple):
    """
    Final Data Type to be reported, filtered ...
    """
    message: str

    # inherit from Blame, not possible yet
    author: str
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
LogLine: TypeAlias = Union[FiltersType, Lint]

__all__ = [
    'Changes',
    'Lint',
    'Blame',
    'Coverage',
    'FiltersType',
]
