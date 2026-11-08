"""Exact-path native adapter for the L-completion fill-mode family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

_PATH = Path(__file__).with_name("family.py").resolve()
_NAME = "_arc_68e9f92d8e4b_family_" + hashlib.sha256(str(_PATH).encode()).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load adjacent family.py")
family = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = family
_SPEC.loader.exec_module(family)
program = family.program
generate = family.generate
