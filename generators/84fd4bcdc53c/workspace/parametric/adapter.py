"""Native promotion adapter for the 84fd4bcdc53c bend-order family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys


HOME = Path(__file__).resolve().parent
_PATH = HOME / "family.py"
_NAME = "_84fd4bcdc53c_parametric_family_" + hashlib.sha256(str(_PATH).encode()).hexdigest()[:12]
_SPEC = importlib.util.spec_from_file_location(_NAME, _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(_PATH)
_FAMILY = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = _FAMILY
_SPEC.loader.exec_module(_FAMILY)


def program(settings):
    return _FAMILY.program(settings)


def generate(seed, settings, demos=3, queries=4):
    return _FAMILY.generate(seed, settings, demos, queries)


def public_turn(episode, query_index=0):
    return _FAMILY.public_turn(episode, query_index)
