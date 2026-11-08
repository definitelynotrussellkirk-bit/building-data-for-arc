"""Bounded findings-only audit; selected source and canonical Racket authority."""
from __future__ import annotations

from collections import deque
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import tempfile

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator
from arcpuzzles import Catalog
from arcpuzzles.runtime import prepare_runtime, run_process

TASK = "7e9fd4cf84a9"
ROOT = find_root(__file__)
OUT = Path(__file__).resolve().parent
GEN, SOURCE, SOURCE_SHA = load_selected_generator(TASK, root=ROOT)
from puzzle_generators.base import set_ctx_observer


def component_count(grid):
    pending = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 3}
    count = 0
    while pending:
        count += 1
        todo = deque([pending.pop()])
        while todo:
            r, c = todo.popleft()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in pending:
                    pending.remove(point)
                    todo.append(point)
    return count


def draw(seed=0, sample_index=0, difficulty=None, **overrides):
    contexts = []
    set_ctx_observer(contexts.append)
    try:
        grid = GEN.generate(seed, sample_index, difficulty=difficulty, **overrides)
    finally:
        set_ctx_observer(None)
    ctx = contexts[-1]
    record = {"seed": seed, "sample_index": sample_index, "difficulty": difficulty,
              "overrides": overrides, "draws": ctx.recorded_draws(), "overrides_used": ctx.overrides_used(),
              "shape": [len(grid), len(grid[0])], "green_component_count": component_count(grid),
              "colors": sorted({value for row in grid for value in row}), "self_check": GEN.self_check(grid)}
    return grid, record


def clean_background_rival(grid):
    """Fill isolated green-surrounded zeros but wrongly discard other colors."""
    output = [[value if value in (0, 3) else 0 for value in row] for row in grid]
    for r in range(1, len(grid) - 1):
        for c in range(1, len(grid[0]) - 1):
            if grid[r][c] == 0 and all(grid[rr][cc] == 3 for rr, cc in ((r-1,c),(r+1,c),(r,c-1),(r,c+1))):
                output[r][c] = 8
    return output


def differences(before, after):
    return [[r, c, before[r][c], after[r][c]] for r in range(len(before)) for c in range(len(before[0]))
            if before[r][c] != after[r][c]]


canonical = list(canonical_pairs(TASK, root=ROOT, labeled_only=True))
ordinary = [draw(seed, 0, band) for seed in range(6) for band in (None, "easy", "medium", "hard")]
degenerates = [(name, *draw(texture=name)) for name in GEN.DEGENERATE_TEXTURES]
base, base_record = draw(123, 0)
axis_records = []
for name in ("palette_kind", "texture"):
    for value in GEN.PALETTE_KINDS:
        grid, record = draw(123, 0, **{name: value})
        axis_records.append({**record, "equal_to_unoverridden_base": grid == base})
for override in ({"grid_h": 5}, {"grid_w": 22}, {"n_rectangles": 6}):
    try:
        grid, record = draw(**override)
    except Exception as exc:
        axis_records.append({"seed": 0, "sample_index": 0, "difficulty": None, "overrides": override,
                             "exception": type(exc).__name__, "message": str(exc)})
    else:
        axis_records.append(record)

records = []
with canonical_path(ROOT).open() as handle:
    for line in handle:
        row = json.loads(line)
        if row.get("task_id") == TASK:
            records.append(row)
assert len(records) == 1
program = records[0]["program_solution"]
grids = [pair["input"] for pair in canonical] + [grid for grid, _ in ordinary] + [grid for _, grid, _ in degenerates]
with tempfile.TemporaryDirectory(prefix=f"audit-{TASK}-") as directory:
    stage = Path(directory)
    prepare_runtime(Catalog(ROOT), stage, TASK)
    (stage / "request.json").write_text(json.dumps({"program": program, "grids": grids}))
    payload = """
import json
from pathlib import Path
from puzzle_generators import runner
request=json.loads(Path('request.json').read_text())
bridge,name=runner._open_bridge_with_rule(runner.wrap_rule(request['program']))
try:
    print(json.dumps([runner._apply_rule(bridge,name,g) for g in request['grids']]))
finally:
    bridge.close()
"""
    result = run_process([sys.executable, "-B", "-c", payload], stage, timeout=90)
    assert result["exit_code"] == 0 and not result["timed_out"], result
    outputs = json.loads(result["stdout"])
assert len(outputs) == len(grids)
canonical_outputs = outputs[:len(canonical)]
ordinary_outputs = outputs[len(canonical):len(canonical) + len(ordinary)]
degenerate_outputs = outputs[len(canonical) + len(ordinary):]
canonical_records = []
for index, (pair, label) in enumerate(zip(canonical, canonical_outputs, strict=True)):
    canonical_records.append({"pair_index": index, "self_check": GEN.self_check(pair["input"]),
                              "racket_matches_label": label == pair["output"],
                              "rival_matches_racket": clean_background_rival(pair["input"]) == label,
                              "distractor_colors": sorted({v for row in pair["input"] for v in row} - {0, 3}),
                              "rival_disagreements": differences(clean_background_rival(pair["input"]), label)})
generated_records = []
for (grid, record), label in zip(ordinary, ordinary_outputs, strict=True):
    record.update(rival_matches_racket=clean_background_rival(grid) == label,
                  requested_rectangles=record["draws"]["n_rectangles"],
                  actual_changed_cells=len(differences(grid, label)))
    generated_records.append(record)
degenerate_records = []
for (name, grid, record), label in zip(degenerates, degenerate_outputs, strict=True):
    degenerate_records.append({**record, "texture": name, "input": grid, "racket_output": label,
                               "changed_cells": differences(grid, label)})
report = {
    "schema": "arcpuzzles-focused-audit-v1", "task_id": TASK, "source_path": str(SOURCE),
    "source_sha256": SOURCE_SHA, "source_unchanged": hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA,
    "rule_hash": hashlib.sha256(" ".join(program.split()).encode()).hexdigest()[:12],
    "canonical_program_sha256": hashlib.sha256(program.encode()).hexdigest(),
    "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    "command": "python3 review.py run python3 ../checks/audit/7e9fd4cf84a9/probe.py",
    "cwd": str(ROOT.parents[1]), "racket_grids_checked": len(grids),
    "canonical": canonical_records, "generated": generated_records,
    "degenerates": degenerate_records, "axis_calls": axis_records,
    "count_shortfalls": [r for r in generated_records if r["green_component_count"] != r["requested_rectangles"]],
    "preservation_witness": {"input": canonical[0]["input"], "racket_output": canonical_outputs[0],
                              "rival_output": clean_background_rival(canonical[0]["input"])},
}
(OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
summary = {"source_sha256": SOURCE_SHA, "rule_hash": report["rule_hash"],
           "racket_grids_checked": len(grids),
           "canonical_validator_rejections": sum(bool(r["self_check"]) for r in canonical_records),
           "canonical_reference_matches": sum(r["racket_matches_label"] for r in canonical_records),
           "background_cleanup_rival_generated_matches": sum(r["rival_matches_racket"] for r in generated_records),
           "background_cleanup_rival_canonical_matches": sum(r["rival_matches_racket"] for r in canonical_records),
           "count_shortfalls": len(report["count_shortfalls"]),
           "degenerate_changes": {r["texture"]: len(r["changed_cells"]) for r in degenerate_records},
           "report": str(OUT / "report.json")}
print(json.dumps(summary, indent=2))
