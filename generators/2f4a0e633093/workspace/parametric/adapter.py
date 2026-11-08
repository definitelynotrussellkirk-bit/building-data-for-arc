"""Thin native adapter for the 2f4a0e633093 area-ranked gallery family."""
from __future__ import annotations

import importlib.util
from pathlib import Path


def _load(name):
    path = Path(__file__).with_name(name + ".py")
    spec = importlib.util.spec_from_file_location("_2f4_parametric_" + name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


family = _load("family")


def program(settings):
    return family.program(settings)


def generate(seed, settings=None, demos=3, queries=4):
    if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
        raise ValueError("seed must be an exact integer in 0..2**63-1")
    if settings is None:
        settings = {"layout": family.LAYOUTS[seed % len(family.LAYOUTS)]}
    settings = family.parse_settings(settings)
    sampled = _load("sampler").inputs(seed, demos=demos, queries=queries)
    episode = {split: [{"input": grid, "output": family.apply(grid, settings)}
                       for grid in sampled[split]] for split in ("train", "test")}
    return {**episode, "program_solution": program(settings), "settings": dict(settings)}
