"""Native adapter for the 08f1d9bdd2ef area-ranked arm family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys


_PATH = Path(__file__).with_name("area_ranked.py").resolve()
_NAME = "_arc_08f1d9bdd2ef_area_ranked_" + hashlib.sha256(str(_PATH).encode()).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load adjacent area_ranked.py")
_FAMILY = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = _FAMILY
_SPEC.loader.exec_module(_FAMILY)

program = _FAMILY.program
generate = _FAMILY.generate
