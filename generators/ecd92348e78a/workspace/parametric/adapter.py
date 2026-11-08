"""Native promotion adapter for the ecd92348e78a bar-chart family."""
from __future__ import annotations

import hashlib
from pathlib import Path
import sys
import types


_PATH = Path(__file__).resolve().with_name("native_family.py")
_BODY = _PATH.read_bytes()
_NAME = "_ecd92348e78a_native_" + hashlib.sha256(str(_PATH).encode() + _BODY).hexdigest()
_FAMILY = sys.modules.get(_NAME)
if _FAMILY is None:
    _FAMILY = types.ModuleType(_NAME)
    _FAMILY.__file__ = str(_PATH)
    sys.modules[_NAME] = _FAMILY
    try:
        exec(compile(_BODY, str(_PATH), "exec"), _FAMILY.__dict__)
    except BaseException:
        sys.modules.pop(_NAME, None)
        raise

program = _FAMILY.program
generate = _FAMILY.generate
solve_variant = _FAMILY.solve_variant
measured_intermediate = _FAMILY.measured_intermediate
render_intermediate = _FAMILY.render_intermediate
