"""Thin native adapter loading only the exact adjacent bbox-selection family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys


_SOURCE = Path(__file__).resolve().with_name("prototype.py")
if _SOURCE.is_symlink() or not _SOURCE.is_file():
    raise ImportError("adapter requires its adjacent regular prototype.py")
_BODY = _SOURCE.read_bytes()
_NAME = "_e3f1bc75d654_bbox_native_" + hashlib.sha256(
    str(_SOURCE).encode() + _BODY
).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _SOURCE)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load adjacent prototype: {_SOURCE}")
_FAMILY = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = _FAMILY
exec(compile(_BODY, str(_SOURCE), "exec"), _FAMILY.__dict__)


def program(settings):
    return _FAMILY.program(settings)


def generate(seed, settings, demos, queries):
    return _FAMILY.generate(seed, settings, demos, queries)
