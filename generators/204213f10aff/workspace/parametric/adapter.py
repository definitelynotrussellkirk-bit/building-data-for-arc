"""Thin source-bound adapter for the 204213f10aff piece-order family."""
import importlib.util
from pathlib import Path

_path = Path(__file__).with_name("prototype.py")
_spec = importlib.util.spec_from_file_location("_204213f10aff_piece_order_prototype", _path)
_prototype = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
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
