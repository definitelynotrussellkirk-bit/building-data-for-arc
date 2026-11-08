"""Thin promotion adapter for the 0d27a69b5a98 parametric family."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from typing import Any

_FAMILY_PATH = Path(__file__).resolve().with_name("family.py")
_NAME = "_0d27a69b5a98_parametric_family"
_spec = importlib.util.spec_from_file_location(_NAME, _FAMILY_PATH)
if _spec is None or _spec.loader is None:
    raise RuntimeError(f"cannot load family module from {_FAMILY_PATH}")
_family = importlib.util.module_from_spec(_spec)
sys.modules[_NAME] = _family
_spec.loader.exec_module(_family)


def program(settings: Any) -> str:
    checked = _family.validate_settings(settings)
    return _family.rule_text(checked["mode"])


def generate(seed: Any, settings: Any, demos: Any = 3, queries: Any = 4):
    checked = _family.validate_settings(settings)
    return _family.generate_episode(seed, checked["mode"], demos, queries)
