"""Promotion adapter for the reviewed metric/direction prototype."""
from __future__ import annotations

import importlib.util
from pathlib import Path

_PATH = Path(__file__).resolve().with_name("prototype.py")
_SPEC = importlib.util.spec_from_file_location("_parametric_7e52d15790d7_adapter", _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load local prototype: {_PATH}")
prototype = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(prototype)


def program(settings):
    return prototype.program_for(settings)


def generate(seed, settings, demos, queries):
    return prototype.generate_claims(seed, settings, demos, queries)
