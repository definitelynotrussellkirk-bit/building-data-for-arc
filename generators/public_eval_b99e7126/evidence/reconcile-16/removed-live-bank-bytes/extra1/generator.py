"""Public b99e7126 periodic self-similar completion. Not owner-approved."""
from pathlib import Path
import hashlib
import importlib.util
import sys

TASK_ID = GENERATOR_ID = "public_eval_b99e7126"
RULE_TASK_ID = 'ee_b99e7126'
VERSION = "1.0.0"
EXAMPLES_NEEDED = 2
PROGRAM = Path(__file__).with_name("reference.rkt").read_text()
RULE_HASH = hashlib.sha256(" ".join(PROGRAM.split()).encode()).hexdigest()[:12]
SUMMARY = "Complete the macro pattern encoded by the anomalous tile's introduced-color mask."
INVARIANTS = [
    "modal-color full separator rows and columns",
    "uniform 3x3 tiles with one repeated ordinary and one repeated anomalous pattern",
    "the anomalous tile introduces exactly one color",
    "visible anomalous clues determine one mask translation",
]
AXES = {}

BASE = Path(__file__).parent / "workspace/parametric/family.py"
NAME = "_b99_base_" + hashlib.sha256(str(BASE).encode()).hexdigest()
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
    return G.solve(grid, "all_ink")


self_check = G.self_check
