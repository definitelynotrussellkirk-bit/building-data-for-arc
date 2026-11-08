"""Thin native API. Claim labels are independently executed by qualification."""
from pathlib import Path
import hashlib
import importlib.util


def _adjacent(name):
    path = Path(__file__).resolve().with_name(name + ".py")
    identity = hashlib.sha256(str(path).encode()).hexdigest()[:16]
    spec = importlib.util.spec_from_file_location(f"reflection_{name}_{identity}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_family = _adjacent("native_family")


def program(settings):
    return _family.program(settings)


def generate(seed, settings=None, demos=3, queries=4):
    _family.integer(seed, "seed", 0, 2**63 - 1)
    _family.integer(demos, "demos", 3, 6)
    _family.integer(queries, "queries", 1, 4)
    if settings is None:
        settings = {"selection": _family.SELECTIONS[seed % len(_family.SELECTIONS)]}
    _family.settings_value(settings)
    train, test = _adjacent("sampler").sample_inputs(seed, demos, queries)
    return {
        "train": [{"input": g, "output": _family.solve(g, settings)} for g in train],
        "test": [{"input": g, "output": _family.solve(g, settings)} for g in test],
        "program_solution": program(settings),
    }
