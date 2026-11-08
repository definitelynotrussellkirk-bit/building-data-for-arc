"""Native promotion adapter for the e5ead55c33e7 packing-order family."""
from __future__ import annotations

import importlib.util
from pathlib import Path

_HOME = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "parametric_e5ead55c33e7_prototype", _HOME / "prototype.py"
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load task-local prototype")
prototype = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(prototype)


def _packing_order(settings) -> str:
    if type(settings) is not dict or set(settings) != {"packing_order"}:
        raise ValueError("settings must contain exactly packing_order")
    packing_order = settings["packing_order"]
    prototype._validate_packing_order(packing_order)
    return packing_order


def program(settings):
    return prototype.program_for(_packing_order(settings))


def generate(seed, settings, demos=3, queries=4):
    return prototype.generate_claims(
        seed,
        packing_order=_packing_order(settings),
        demos=demos,
        queries=queries,
    )
