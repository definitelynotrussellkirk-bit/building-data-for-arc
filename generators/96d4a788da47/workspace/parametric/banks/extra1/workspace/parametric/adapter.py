"""Native adapter for all-object and anchor-indexed left-slide rules."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys


def _family_module():
    path = Path(__file__).with_name("family.py").resolve()
    name = "_task_96d4a788da47_parametric_family_" + hashlib.sha256(
        str(path).encode("utf-8")
    ).hexdigest()
    module = sys.modules.get(name)
    if module is not None:
        return module
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load adjacent family source {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def program(settings):
    return _family_module().program(settings)


def generate(seed, settings, demos, queries):
    return _family_module().generate(seed, settings, demos, queries)


def __getattr__(name):
    if name in {
        "anchor_selector",
        "apply_policy",
        "apply_wrong_intermediate",
        "causal_case",
        "counterfactual_program",
        "objects_by_color",
        "validate_settings",
    }:
        return getattr(_family_module(), name)
    raise AttributeError(name)
