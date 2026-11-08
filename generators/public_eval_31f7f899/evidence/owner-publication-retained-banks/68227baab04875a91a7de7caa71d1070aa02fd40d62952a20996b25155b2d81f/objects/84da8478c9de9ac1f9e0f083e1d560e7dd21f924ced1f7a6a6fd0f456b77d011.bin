"""Canonical sampler for the public bar-height sorting family."""
import importlib.util
from pathlib import Path

GENERATOR_ID = TASK_ID = "public_eval_31f7f899"
RULE_TASK_ID = 'ee_31f7f899'
VERSION = "1.0.0"
RULE_HASH = "66ed1576c8f5"
EXAMPLES_NEEDED = 3
SUMMARY = "Measure vertical bar heights on a common carrier and assign the sorted heights from left to right."
AXES = {}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
INVARIANTS = [
    "one fully occupied horizontal carrier row",
    "solid colored bar slots centered on that row",
    "slot colors and widths remain fixed while heights are sorted",
]
_source = Path(__file__).parent / "workspace/parametric/native_family.py"
_spec = importlib.util.spec_from_file_location("selected_public_eval_31f7f899_native", _source)
_native = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_native)


def generate(seed=0, difficulty=None, sample_index=0, **overrides):
    if overrides:
        raise ValueError(f"No exact override axes are declared: {sorted(overrides)}")
    _native._integer(seed, 0, 2**63 - 1, "seed")
    _native._integer(sample_index, 0, 2**63 - 1, "sample_index")
    if difficulty not in (None, "easy", "medium", "hard", "mixed"):
        raise ValueError("unsupported difficulty")
    demos, queries = _native.input_bank(seed)
    return (demos + queries)[sample_index % 10]


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    try:
        _native.plan(grid, "ascending")
        return []
    except (TypeError, ValueError) as error:
        return [str(error)]


def strict_canonical_like(grid):
    return self_check(grid)
