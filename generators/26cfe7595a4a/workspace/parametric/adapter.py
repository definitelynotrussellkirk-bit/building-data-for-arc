"""Native adapter for the crop-created perimeter selector family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

_SOURCE = Path(__file__).resolve().with_name("family.py")
if _SOURCE.is_symlink() or not _SOURCE.is_file():
    raise ImportError("adapter requires adjacent regular family.py")
_BODY = _SOURCE.read_bytes()
_NAME = "_parametric_26_" + hashlib.sha256(str(_SOURCE).encode() + _BODY).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _SOURCE)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load adjacent family")
_IMPL = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = _IMPL
exec(compile(_BODY, str(_SOURCE), "exec"), _IMPL.__dict__)


def program(settings):
    return _IMPL.program_for(_IMPL.validate_settings(settings))


def generate(seed, settings, demos, queries):
    border_rule = _IMPL.validate_settings(settings)
    _IMPL.validate_request(seed, demos, queries)
    return _IMPL.generate_episode(seed, border_rule, demos=demos, queries=queries)
