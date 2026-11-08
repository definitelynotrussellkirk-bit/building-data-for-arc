"""Thin native adapter, loading only exact adjacent source files."""
import importlib.util
from pathlib import Path

HOME = Path(__file__).resolve().parent


def _load(name):
    spec = importlib.util.spec_from_file_location('_skyline_b1e6ee6856bf_' + name, HOME / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def program(settings):
    return _load('native_family').program(settings)


def generate(seed, settings, demos=3, queries=4):
    family = _load('native_family')
    mode = family.parse_settings(settings)
    inputs = _load('sampler').sample_inputs(seed, demos=demos, queries=queries)
    return {**{split: [{'input': grid, 'output': family.apply(grid, mode)} for grid in inputs[split]]
               for split in ('train', 'test')}, 'program_solution': family.program(settings)}
