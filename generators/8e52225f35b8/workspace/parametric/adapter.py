"""Native qualification adapter for 8e52225f35b8's closure-order family."""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

_PATH = Path(__file__).with_name("prototype.py")
_SPEC = importlib.util.spec_from_file_location("_arc_8e52225f35b8_prototype", _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load {_PATH}")
_PROTO = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_PROTO)


def program(settings):
    return _PROTO.program(copy.deepcopy(settings))


def generate(seed, settings, demos, queries):
    episode = _PROTO.generate(seed, copy.deepcopy(settings), demos=demos, queries=queries)
    return {
        "train": copy.deepcopy(episode["train"]),
        "test": copy.deepcopy(episode["test"]),
        "program_solution": episode["program_solution"],
    }
