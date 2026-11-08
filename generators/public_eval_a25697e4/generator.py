"""Unapproved canonical socket/key sampler, originating from public a25697e4."""
from __future__ import annotations
RULE_TASK_ID = 'ee_a25697e4'
import importlib.util
from pathlib import Path
from puzzle_generators.base import gen_ctx

GENERATOR_ID = TASK_ID = "public_eval_a25697e4"
VERSION = "1.0.0"
RULE_HASH = "3baf4daa1663"
EXAMPLES_NEEDED = 3
SUMMARY = "Fit two-color keys into edge sockets; proper rotations preserve colors and reflected fits exchange the two colors."
AXES = {}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
INVARIANTS = [
    "rectangular exact-integer ARC grid with a unique modal background",
    "one to four noncorner edge sockets, grouped by edge and anchor color",
    "one free colorblind four-connected two-color key per socket",
    "exactly one complete D4 placement assignment with no anchor/final-key collisions",
]
_source = Path(__file__).parent / "workspace/parametric/native_family.py"
_spec = importlib.util.spec_from_file_location("selected_socket_native", _source)
_native = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_native)


def generate(seed=0, difficulty=None, sample_index=0, **overrides):
    """Return one canonical input; the native adapter owns full episode assembly."""
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
