from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path

WORK = Path(__file__).resolve().parents[3]
TASK = "c1e45a501ca9"
SOURCE = WORK / "repo" / "generators" / TASK / "generator.py"
SPEC = importlib.util.spec_from_file_location("audit_target_c1", SOURCE)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)

requested = 1
grid = GEN.generate(0, 0, difficulty="easy", n_cells=requested)
observed = sum(value not in (0, 8) for row in grid for value in row)
assert GEN.self_check(grid) == []
assert observed == 2 != requested
# Unknown keys are also silently accepted because the generator never validates
# overrides; the returned grid is deterministic but the typo is invisible.
unknown_grid = GEN.generate(0, 0, difficulty="easy", typo_axis=123)
assert unknown_grid == GEN.generate(0, 0, difficulty="easy")

racket = json.loads((Path(__file__).parent / "racket.json").read_text())
result = {
    "task_id": TASK,
    "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "seed": 0,
    "sample_index": 0,
    "difficulty": "easy",
    "requested_overrides": {"n_cells": requested},
    "observed_non_guide_colored_cells": observed,
    "self_check": [],
    "unknown_override_silently_accepted": "typo_axis",
    "input": grid,
    "actual_racket_output": racket["results"][0]["output"],
    "finding": (
        "The advertised exact n_cells axis is not consumed: n_cells=1 returns "
        "two source cells, and unknown override names are accepted silently."
    ),
}
(Path(__file__).parent / "counterexample.json").write_text(
    json.dumps(result, indent=2, sort_keys=True) + "\n"
)
print(json.dumps({"passed": True, "requested": requested, "observed": observed}, sort_keys=True))
