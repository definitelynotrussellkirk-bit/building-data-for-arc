"""Unapproved canonical pattern-board sampler from public parent8698868d."""
from __future__ import annotations
import importlib.util
from pathlib import Path
from puzzle_generators.base import gen_ctx

GENERATOR_ID = TASK_ID = "public_eval_8698868d"
VERSION = "1.0.0"
RULE_HASH = "6fd48cdc010b"
EXAMPLES_NEEDED = 3
SUMMARY = "Match enclosed-region counts, insert each loose pattern into its matching board tile, and crop to the board."
AXES = {}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
INVARIANTS = [
    "exact-integer ARC grid with a unique modal background",
    "one largest foreground-component bounding box is the tiled board",
    "detached monochrome framed square patterns share a common side length",
    "board tile side is pattern side plus two; enclosed four-connected background-region counts match one-to-one",
]
_source = Path(__file__).parent / "workspace/parametric/native_family.py"
_spec = importlib.util.spec_from_file_location("selected_pattern_native", _source)
_native = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_native)


def generate(seed=0, difficulty=None, sample_index=0, **overrides):
    """One canonical input; the native adapter assembles the teaching episode."""
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
        _native.plan(grid)
        return []
    except (ValueError, TypeError) as error:
        return [str(error)]


def strict_canonical_like(grid):
    return self_check(grid)
