"""Native ARCpuzzles adapter; labels are independently replayed at qualification."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys


def _load(name):
    path = Path(__file__).resolve().with_name(name + ".py")
    key = "_lattice_parametric_" + hashlib.sha256(str(path).encode()).hexdigest()
    if key not in sys.modules:
        spec = importlib.util.spec_from_file_location(key, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[key] = module
        try:
            spec.loader.exec_module(module)
        except BaseException:
            sys.modules.pop(key, None)
            raise
    return sys.modules[key]


def _settings(settings):
    if (type(settings) is not dict or set(settings) != {"retention"}
            or type(settings["retention"]) is not str
            or settings["retention"] not in ("all", "largest_filled_component")):
        raise ValueError("settings must contain only retention=all|largest_filled_component")
    return settings["retention"]


def program(settings):
    _settings(settings)
    return _load("programs").program(settings)


def generate(seed, settings, demos=3, queries=4):
    retention = _settings(settings)
    programs = _load("programs")
    train, test, metadata = _load("sampler").sample_episode_inputs(seed, demos, queries)
    return {
        "train": [{"input": g, "output": programs.evaluate(g, retention)} for g in train],
        "test": [{"input": g, "output": programs.evaluate(g, retention)} for g in test],
        "program_solution": programs.program(settings),
        "settings": dict(settings),
        "metadata": metadata,
    }
