"""Public a6f40cea occluded rectangular-wire completion. Not owner-approved."""
from pathlib import Path
import hashlib
import importlib.util
import sys

TASK_ID = GENERATOR_ID = "public_eval_a6f40cea"
RULE_TASK_ID = 'ee_a6f40cea'
VERSION = "1.0.0"
EXAMPLES_NEEDED = 2
PROGRAM = Path(__file__).with_name("reference.rkt").read_text()
RULE_HASH = hashlib.sha256(" ".join(PROGRAM.split()).encode()).hexdigest()[:12]
SUMMARY = "Recover rectangular wires hidden by the largest green box and return its reconstructed interior."
INVARIANTS = [
    "one largest four-connected green rectangular occluder",
    "two or more partially visible monochrome/checkerboard rectangle wires",
    "uniform occluder fill before reconstruction",
    "1..30 input and output dimensions",
]
AXES = {}

BASE = Path(__file__).parent / "workspace/parametric/family.py"
NAME = "_a6_base_" + hashlib.sha256(str(BASE).encode()).hexdigest()
SPEC = importlib.util.spec_from_file_location(NAME, BASE)
G = importlib.util.module_from_spec(SPEC)
sys.modules[NAME] = G
exec(compile(BASE.read_bytes(), str(BASE), "exec"), G.__dict__)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int or seed < 0 or type(sample_index) is not int or sample_index < 0:
        raise ValueError("nonnegative exact integer seed and sample_index required")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("unsupported difficulty")
    if overrides:
        raise TypeError("no override axes")
    return G.ordinary(seed, sample_index, stress=(difficulty == "hard" or sample_index % 4 == 3))


def rule_mirror(grid):
    return G.solve(grid, "all_frames")


self_check = G.self_check
