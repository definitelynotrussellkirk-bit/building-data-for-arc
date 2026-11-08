"""Thin source-bound adapter for the c8e53 anchor-size family."""
import importlib.util
from pathlib import Path

_path = Path(__file__).with_name("prototype.py")
_spec = importlib.util.spec_from_file_location("_c8e53_anchor_size_prototype", _path)
_prototype = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_prototype)


def program(settings):
    return _prototype.program(settings)


def generate(seed, settings, demos, queries):
    episode = _prototype.generate(seed, settings, demos, queries)
    return {
        "train": episode["train"],
        "test": episode["test"],
        "program_solution": episode["program_solution"],
    }
