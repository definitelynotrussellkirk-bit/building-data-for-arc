"""Native entry point; resolve this family's implementation by exact path."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

_path = Path(__file__).resolve().with_name("family.py")
_name = "_mirror_rank_family_" + hashlib.sha256(str(_path).encode()).hexdigest()
_spec = importlib.util.spec_from_file_location(_name, _path)
family = importlib.util.module_from_spec(_spec)
sys.modules[_name] = family
_spec.loader.exec_module(family)

program = family.program
generate = family.generate
