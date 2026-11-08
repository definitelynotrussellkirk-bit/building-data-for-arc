"""Thin exact-path adapter for the 00f37833e26f residual family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

_PATH = Path(__file__).resolve().with_name("prototype.py")
_NAME = "_arc_00f37833e26f_parametric_" + hashlib.sha256(str(_PATH).encode()).hexdigest()[:16]
_SPEC = importlib.util.spec_from_file_location(_NAME, _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(_PATH)
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = _PROTOTYPE
_SPEC.loader.exec_module(_PROTOTYPE)


def program(settings):
    return _PROTOTYPE.program(settings)


def generate(seed, settings, demos=3, queries=4):
    return _PROTOTYPE.generate(seed, settings, demos=demos, queries=queries)


def public_turn(episode, query_index=0):
    return _PROTOTYPE.public_turn(episode, query_index)
