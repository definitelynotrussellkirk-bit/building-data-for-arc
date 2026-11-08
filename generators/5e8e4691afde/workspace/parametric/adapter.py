"""Native promotion adapter for rotation and scale in 5e8e4691afde."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

_HERE = Path(__file__).resolve().parent
_NAME = "arcpuzzles_5e8e4691afde_rotation_scale_prototype"
_SPEC = importlib.util.spec_from_file_location(_NAME, _HERE / "prototype.py")
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load adjacent rotation-scale prototype")
prototype = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = prototype
_SPEC.loader.exec_module(prototype)


def _setting(settings):
    if type(settings) is not dict or set(settings) != {"quarter_turns", "distance_scale"}:
        raise ValueError("settings must contain exactly quarter_turns and distance_scale")
    return prototype.Setting(
        quarter_turns=settings["quarter_turns"],
        distance_scale=settings["distance_scale"],
    )


def program(settings):
    return prototype.program_for(_setting(settings))


def generate(seed, settings, demos, queries):
    return prototype.generate_episode(seed, _setting(settings), demos, queries)
