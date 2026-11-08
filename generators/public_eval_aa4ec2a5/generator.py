"""Canonical input sampler for the unapproved public topology family."""
import importlib.util
from pathlib import Path
from puzzle_generators.base import gen_ctx

GENERATOR_ID = TASK_ID = "public_eval_aa4ec2a5"
RULE_TASK_ID = 'ee_aa4ec2a5'
VERSION = "1.0.0"
RULE_HASH = "41fa9a387754"
EXAMPLES_NEEDED = 3
SUMMARY = "Detect enclosed holes, recolor their entire foreground objects, fill the holes, and add an eight-neighbor exterior outline."
AXES = {}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
INVARIANTS = [
    "two exact input colors with a unique modal background",
    "foreground four-components have no mutual diagonal contact or nested foreground",
    "input colors exclude fixed semantic output colors2,6,8",
    "component-local cavity classification precedes whole-object recoloring, hole filling, and clipped exterior outlining",
]
_source = Path(__file__).parent / "workspace/parametric/native_family.py"
_spec = importlib.util.spec_from_file_location("selected_topology_native", _source)
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
        _native.plan(grid, 4)
        return []
    except (ValueError, TypeError) as error:
        return [str(error)]


def strict_canonical_like(grid):
    return self_check(grid)
