"""
compliance-control-mapper
=========================

Crosswalk tool that maps security controls across ISO/IEC 27001:2022,
NIST Cybersecurity Framework 2.0, CIS Controls v8, and SOC 2 Trust Services
Criteria.

Typical usage from the command line::

    compliance-mapper list iso27001
    compliance-mapper show A.8.13
    compliance-mapper map A.8.13
    compliance-mapper search "backup"
    compliance-mapper stats
    compliance-mapper export markdown > crosswalk.md

Author: Aslam Ahamed - Head of IT @ Prestige One Developments, Dubai
License: MIT
"""

__version__ = "1.0.0"
__author__ = "Aslam Ahamed"
__license__ = "MIT"

from .data import load_framework, load_mappings, FRAMEWORKS  # noqa: F401
from .search import search_controls  # noqa: F401
from .mapper import map_control, map_topic  # noqa: F401
