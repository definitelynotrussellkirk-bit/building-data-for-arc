"""Native adapter for the 4de2bae05c7d parametric family."""
from __future__ import annotations

import importlib.util
from pathlib import Path


_HOME = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "_arcpuzzles_parametric_4de2bae05c7d_family", _HOME / "family.py"
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load adjacent parametric family")
_FAMILY = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_FAMILY)
_PROGRAMS = {
    "canonical": (_HOME / "canonical.rkt").read_text(encoding="utf-8"),
    "largest": (_HOME / "largest.rkt").read_text(encoding="utf-8"),
    "smallest": (_HOME / "smallest.rkt").read_text(encoding="utf-8"),
}


def _mode(settings) -> str:
    if type(settings) is not dict or set(settings) != {"postprocess"}:
        raise ValueError("settings must contain exactly postprocess")
    value = settings["postprocess"]
    if type(value) is not str or value not in _FAMILY.MODES:
        raise ValueError("postprocess setting is invalid")
    return value


def program(settings):
    return _PROGRAMS[_mode(settings)]


def generate(seed, settings, demos, queries):
    mode = _mode(settings)
    episode = _FAMILY.generate_episode(seed, mode, demos, queries)
    return {
        "train": episode["train"],
        "test": episode["test"],
        "program_solution": program(settings),
    }
