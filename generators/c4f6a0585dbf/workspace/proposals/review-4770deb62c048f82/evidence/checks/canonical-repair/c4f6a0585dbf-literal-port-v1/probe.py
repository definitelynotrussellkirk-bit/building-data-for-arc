from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import time

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import canonical_path, find_root, load_selected_generator, normalize_grid

TASK_ID = "c4f6a0585dbf"
HERE = Path(__file__).resolve()
ROOT = find_root(HERE)
generator, source_path, source_sha256 = load_selected_generator(TASK_ID, root=ROOT)

programs = []
with canonical_path(ROOT).open(encoding="utf-8") as handle:
    for line in handle:
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            programs.append(row["program_solution"])
assert len(set(programs)) == 1
program = programs[0]
function = strip_rule_wrapper(program)


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, separators=(",", ":")).encode()).hexdigest()


def evaluate(bridge, grid):
    datum = "(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    return normalize_grid(bridge.eval_text(f"({function} '{datum})"))


def changed_cells(left, right):
    return sum(a != b for lrow, rrow in zip(left, right, strict=True) for a, b in zip(lrow, rrow, strict=True))


started = time.monotonic()
control = generator.generate(13, 5, difficulty="medium")
no_targets = generator.generate(0, 0, difficulty="medium", texture="no_targets")
full = generator.generate(0, 0, difficulty="medium", texture="full_grid")
assert generator.self_check(control) == []
assert generator.self_check(no_targets) == []
assert generator.self_check(full) == []

recolored = deepcopy(control)
for row in recolored:
    for index, value in enumerate(row):
        if value == 4:
            row[index] = 2
recolor_errors = generator.self_check(recolored)
assert any("literal 4" in error for error in recolor_errors)

try:
    generator.generate(13, 5, difficulty="medium", palette_kind="warm")
except ValueError as exc:
    alias_rejection = str(exc)
else:
    raise AssertionError("palette_kind='warm' was not rejected")

with RacketBridge() as bridge:
    control_output = evaluate(bridge, control)
    no_targets_output = evaluate(bridge, no_targets)
    full_output = evaluate(bridge, full)

control_changes = changed_cells(control, control_output)
assert control_changes > 0
assert no_targets_output == no_targets
assert full_output == full

result = {
    "schema": "c4f6a0585dbf-literal-port-repair-probe-v1",
    "status": "pass",
    "source": {
        "path": str(source_path.relative_to(ROOT)),
        "sha256": source_sha256,
        "version": generator.VERSION,
        "rule_hash": generator.RULE_HASH,
        "canonical_racket_sha256": hashlib.sha256(program.encode()).hexdigest(),
    },
    "control": {
        "seed": 13,
        "sample_index": 5,
        "difficulty": "medium",
        "colors": sorted({cell for row in control for cell in row}),
        "input_sha256": digest(control),
        "output_sha256": digest(control_output),
        "changed_cells": control_changes,
        "observed": generator.observe_overrides(control),
        "self_check": [],
    },
    "rejection_paths": {
        "palette_kind_warm": alias_rejection,
        "recolored_4_to_2": recolor_errors,
    },
    "declared_boundaries": {
        "no_targets": {
            "identity": no_targets_output == no_targets,
            "input_sha256": digest(no_targets),
            "output_sha256": digest(no_targets_output),
        },
        "full_grid": {
            "identity": full_output == full,
            "input_sha256": digest(full),
            "output_sha256": digest(full_output),
        },
    },
    "elapsed_seconds": round(time.monotonic() - started, 3),
    "scope": "One repaired control, two declared degenerates, one alias rejection, and one recolor validator rejection.",
}
(Path(__file__).with_name("result.json")).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps(result, indent=2, sort_keys=True))
