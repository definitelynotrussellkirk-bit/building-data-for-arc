"""Canonical input sampler for the unapproved public nozzle family."""
import importlib.util
from pathlib import Path
from puzzle_generators.base import gen_ctx

GENERATOR_ID = TASK_ID = "public_eval_b9e38dc0"
RULE_TASK_ID = 'ee_b9e38dc0'
VERSION = "1.0.0"
RULE_HASH = "2819124fd538"
EXAMPLES_NEEDED = 3
SUMMARY = "Continue a nozzle's stepped walls, identify its dye, and fill the inferred band while preserving parallel obstacle shadows."
AXES = {}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
INVARIANTS = [
    "unique modal background and uniquely next-most-frequent connected wall",
    "two wall endpoints identify cardinal flow and complete repeated terminal staircases",
    "a contiguous rear cap and connected interior identify the earliest dye marker",
    "only reached interior foreign colors cast parallel shadows; existing colored cells are preserved",
]
_source = Path(__file__).parent / "workspace/parametric/native_family.py"
_spec = importlib.util.spec_from_file_location("selected_nozzle_native", _source)
_native = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_native)


def generate(seed=0, difficulty=None, sample_index=0, **overrides):
    if overrides:
        raise ValueError(f"No exact override axes are declared: {sorted(overrides)}")
    _native._integer(seed, 0, 2**63 - 1, "seed")
    _native._integer(sample_index, 0, 2**63 - 1, "sample_index")
    if difficulty not in (None, "easy", "medium", "hard", "mixed"):
        raise ValueError("unsupported difficulty")
    ctx = gen_ctx(seed=seed, task_id=TASK_ID, version=VERSION, sample_index=sample_index, difficulty=difficulty)
    episode_seed = ctx.draw_int("episode_seed", 0, 2**63 - 1)
    train, query = _native.input_bank(episode_seed)
    return (train + query)[sample_index % 10]


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    try:
        _native.plan(grid, "opaque")
        return []
    except (ValueError, TypeError) as error:
        return [str(error)]


def strict_canonical_like(grid):
    return self_check(grid)
