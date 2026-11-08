"""Replay a source-bound default lesson ambiguity after production dedup.

This invokes the production Python runner with an independently implemented
CCW bridge substitute. It exercises the actual acceptance/dedup loop but is
not a new Racket execution or authority check.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[1]
REPO = WORK / "repo"
sys.path.insert(0, str(REPO / "shared/runtime"))

from puzzle_generators import runner


EXPECTED_SHA256 = "2dc1ef5cb5ff40c0365c92a9f309ed8816ce254bb7c342fd80d648de6f390469"
SOURCE = HERE / "generator_2dc1ef5.py"
body = SOURCE.read_bytes()
assert hashlib.sha256(body).hexdigest() == EXPECTED_SHA256
gen = ModuleType("reviewed_rotation_candidate")
gen.__file__ = str(SOURCE)
exec(compile(body, str(SOURCE), "exec"), gen.__dict__)


def ccw(grid):
    h, w = len(grid), len(grid[0])
    return [[grid[r][w - 1 - c] for r in range(h)] for c in range(w)]


class PythonReferenceBridge:
    def define_grid(self, name, grid):
        self.grid = deepcopy(grid)

    def eval_text(self, expression):
        return ccw(self.grid)


bundle = SimpleNamespace(
    kind="per_puzzle",
    generator_module=gen,
    allow_identity_output=False,
    rule_task_id="864eaaac6503",
    rule_file="Python CCW substitute; no Racket execution in this probe",
)
instance = runner.run_one(
    "864eaaac6503", seed=21212, sample_index=0, n_train=3, n_test=1,
    bundle=bundle, bridge=PythonReferenceBridge(), fn_name="ccw",
    difficulty="easy",
)
pairs = instance["train"] + instance["test"]
rotations = []
for query_index, query in enumerate(pairs):
    demos = [pair for i, pair in enumerate(pairs) if i != query_index]
    rotations.append({
        "query_index": query_index,
        "errors": gen.lesson_identifiable(demos, query),
        "rival_fits_demos": all(
            gen.CANONICAL_SHORTCUTS["only_three_by_three"](p["input"]) == p["output"]
            for p in demos
        ),
        "rival_query_prediction": gen.CANONICAL_SHORTCUTS["only_three_by_three"](query["input"]),
    })

assert [p["sample_index"] for p in instance["sampling"]["accepted_pairs"]] == [0, 1, 2, 4]
assert instance["sampling"]["rejections"][0]["reason"] == "validate.duplicate_pair"
assert rotations[1]["errors"] == [
    "rival only_three_by_three fits demonstrations but changes the query"
]
assert gen.generate(21212, 1, difficulty="easy") == gen.generate(21212, 3, difficulty="easy")

metadata_example = gen.generate(63, 1, difficulty="hard")
report = {
    "schema": "rotation-independent-code-review-v1",
    "generator_source_sha256": EXPECTED_SHA256,
    "generator_source_snapshot": str(SOURCE.relative_to(WORK)),
    "runner_sha256": hashlib.sha256(Path(runner.__file__).read_bytes()).hexdigest(),
    "canonical_rule_hash_declared": gen.RULE_HASH,
    "reproduction_scope": "Actual production Python acceptance/dedup loop; independent Python CCW labels; no Racket execution",
    "finding": {
        "severity": "important",
        "summary": "Duplicate extended examples leave only one size witness in an accepted four-pair lesson; rotating that witness to the query is ambiguous.",
        "seed": 21212,
        "sample_index": 0,
        "difficulty": "easy",
        "query_index": 1,
        "rival": "only_three_by_three",
    },
    "instance": instance,
    "query_rotations": rotations,
    "minor_metadata_finding": {
        "seed": 63,
        "sample_index": 1,
        "difficulty": "hard",
        "shape": [len(metadata_example), len(metadata_example[0])],
        "advertised_height_default": gen.AXES["grid_h"]["default"],
        "advertised_width_default": gen.AXES["grid_w"]["default"],
    },
    "scope_clarifications": [
        "The coordinator confirmed that informational guarantees intentionally apply only when effective overrides are empty.",
        "The coordinator confirmed retention of the baseline validator's at-least-two-colors domain even though the rotation operation can execute monochrome inputs.",
        "The proposed repair of alternating extended minimum-dimension parity prevents neighboring extended draws from being identical; this report does not execute that later candidate.",
    ],
}
print(json.dumps(report, indent=2))
