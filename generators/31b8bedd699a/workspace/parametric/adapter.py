"""Exact-path native adapter for the token-size / spatial-order family."""
from __future__ import annotations

import hashlib
from pathlib import Path
import sys
import types


_PATH = Path(__file__).resolve().with_name("native_family.py")
_BODY = _PATH.read_bytes()
_NAME = "_native_token_order_31b8bedd699a_" + hashlib.sha256(
    str(_PATH).encode() + _BODY
).hexdigest()
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

program = _FAMILY.program_for
generate = _FAMILY.generate
