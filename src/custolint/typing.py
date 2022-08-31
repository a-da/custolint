"""
Keep here all custom data type used within this package
"""
from typing import Dict, Tuple

Changes = Dict[str, Dict[int, Dict[str, str]]]
Lint = Tuple[str, int, str, str, str]
"""
file name
line_number
message
email
date
"""

Blame = Tuple[str, int, str, str]

Coverage = Tuple[Dict[str, str], str, int]
"""
contributor
file name
line_number
"""
