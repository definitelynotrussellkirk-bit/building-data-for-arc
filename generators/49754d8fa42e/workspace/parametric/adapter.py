"""Exact adjacent-file adapter for the mode-selected connectivity family."""
import importlib.util
from pathlib import Path

_path = Path(__file__).with_name("composition.py")
_spec = importlib.util.spec_from_file_location("mode_glyph_49754d8fa42e_composition", _path)
_composition = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_composition)


def program(settings):
    return _composition.program(settings)


def generate(seed, settings, demos=3, queries=4):
    return _composition.generate(seed, settings, demos, queries)
