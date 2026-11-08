"""Native promotion adapter for the extracted-template orientation family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

_HERE = Path(__file__).resolve().parent
_SOURCE = _HERE / "family.py"
_BODY = _SOURCE.read_bytes()
_NAME = "_arc_bf5bed969a6d_family_" + hashlib.sha256(_BODY).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _SOURCE)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load adjacent template family")
_FAMILY = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = _FAMILY
exec(compile(_BODY, str(_SOURCE), "exec"), _FAMILY.__dict__)


def _mode(settings: object) -> str:
    if type(settings) is not dict or set(settings) != {"template_transform"}:
        raise ValueError("settings must contain exactly template_transform")
    return _FAMILY.validate_transform(settings["template_transform"])


def program(settings: object) -> str:
    mode = _mode(settings)
    name = "canonical.rkt" if mode == "as_is" else "rotate-cw.rkt"
    return (_HERE / name).read_text(encoding="utf-8")


def generate(seed: int, settings: object, demos: int, queries: int) -> dict:
    mode = _mode(settings)
    selected = program({"template_transform": mode})
    return _FAMILY.generate_episode(seed, template_transform=mode, demos=demos, queries=queries,
                                    program_solution=selected)
