"""Standalone canonical sampler for public ARC task 78332cb0."""
import hashlib
import importlib.util
from pathlib import Path

GENERATOR_ID = TASK_ID = "public_eval_78332cb0"
RULE_TASK_ID = 'ee_78332cb0'
VERSION = "1.0.0"
EXAMPLES_NEEDED = 2
SUMMARY = "Reorder separator-bounded path panels into their unique contact-matched chain."
AXES = {}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
INVARIANTS = [
    "color-6 rows and columns delimit 5x5 panels",
    "occupied panels contain one monochrome path on color-7 background",
    "edge-contact coordinates determine one complete vertical or horizontal chain",
]
_path = Path(__file__).parent / "workspace/parametric/engine.py"
_spec = importlib.util.spec_from_file_location("selected_public_eval_78332cb0_engine", _path)
_engine = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_engine)
RULE_HASH = hashlib.sha256(" ".join((Path(__file__).parent / "reference.rkt").read_text().split()).encode()).hexdigest()[:12]


def generate(seed=0, difficulty=None, sample_index=0, **overrides):
    if overrides:
        raise ValueError(f"No exact override axes are declared: {sorted(overrides)}")
    _engine._integer(seed, 0, 2**63 - 1, "seed")
    _engine._integer(sample_index, 0, 2**63 - 1, "sample_index")
    if difficulty not in (None, "easy", "medium", "hard", "mixed"):
        raise ValueError("unsupported difficulty")
    demos, queries = _engine.input_bank(seed)
    return (demos + queries)[sample_index % 10]


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    try:
        _engine.analyze(grid)
        return []
    except (TypeError, ValueError) as error:
        return [str(error)]


def strict_canonical_like(grid):
    return self_check(grid)
