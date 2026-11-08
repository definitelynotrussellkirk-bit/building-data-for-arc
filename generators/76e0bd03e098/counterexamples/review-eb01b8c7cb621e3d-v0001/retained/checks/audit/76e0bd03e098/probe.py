"""Finite, audit-only probes. Run through run_with_racket.py from packet root."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path

from puzzle_generators.base import set_ctx_observer


TASK = "76e0bd03e098"
REPO = Path.cwd()
OUT = Path(__file__).resolve().parent
GENERATOR = REPO / "generators" / TASK / "generator.py"


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":")).encode()).hexdigest()


def route(grid, clear_fallback_required):
    """Independent rival: require the fallback L to be clear before drawing it."""
    out = [row[:] for row in grid]
    colors = list(dict.fromkeys(v for row in grid for v in row if v not in (0, 8)))
    analyses = []
    for color in colors:
        points = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == color]
        if len(points) != 2:
            continue
        (r1, c1), (r2, c2) = points
        rr = list(range(r1, r2 + (1 if r2 >= r1 else -1), 1 if r2 >= r1 else -1))
        cc = list(range(c1, c2 + (1 if c2 >= c1 else -1), 1 if c2 >= c1 else -1))
        path_h = [(r1, c) for c in cc] + [(r, c2) for r in rr[1:]]
        path_v = [(r, c1) for r in rr] + [(r2, c) for c in cc[1:]]
        blockers_h = [[r, c, grid[r][c]] for r, c in path_h if (r, c) not in points and grid[r][c] != 0]
        blockers_v = [[r, c, grid[r][c]] for r, c in path_v if (r, c) not in points and grid[r][c] != 0]
        analyses.append({"color": color, "points": points, "horizontal_blockers": blockers_h, "vertical_blockers": blockers_v})
        if not blockers_h:
            chosen = path_h
        elif not clear_fallback_required or not blockers_v:
            chosen = path_v
        else:
            chosen = []
        for r, c in chosen:
            if out[r][c] != 8:
                out[r][c] = color
    return out, analyses


spec = importlib.util.spec_from_file_location("audit_generator_76e0bd03e098", GENERATOR)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
canonical = next(json.loads(line) for line in (REPO / "shared/data/canonical/puzzles.jsonl").open()
                 if json.loads(line).get("task_id") == TASK)
source = {
    "generator_path": "repo/generators/76e0bd03e098/generator.py",
    "generator_sha256": hashlib.sha256(GENERATOR.read_bytes()).hexdigest(),
    "generator_version": module.VERSION,
    "rule_path": "repo/shared/data/canonical/puzzles.jsonl",
    "rule_record_task_id": TASK,
    "rule_sha256": hashlib.sha256(canonical["program_solution"].encode()).hexdigest(),
    "canonical_record_sha256": digest(canonical),
}
overrides_cases = [
    {},
    {"palette_size": 3},
    {"palette_size": 5},
    {"n_distinct_colors": 3},
    {"n_distinct_colors": 5},
    {"palette_kind": "warm"},
    {"palette_kind": "cool"},
    {"texture": "warm"},
    {"texture": "cool"},
]
cases = []
grids = []
for overrides in overrides_cases:
    contexts = []
    set_ctx_observer(contexts.append)
    try:
        grid = module.generate(0, 0, difficulty="medium", **overrides)
    finally:
        set_ctx_observer(None)
    counts = Counter(v for row in grid for v in row)
    cases.append({
        "seed": 0, "sample_index": 0, "difficulty": "medium", "overrides": overrides,
        "input_sha256_compact_json": digest(grid),
        "same_as_baseline": not grids or grid == grids[0],
        "colors_including_background": sorted(counts),
        "palette_size_including_background": len(counts),
        "n_distinct_nonzero_colors": len([c for c in counts if c]),
        "pair_colors": sorted(c for c in counts if c not in (0, 8)),
        "self_check_errors": module.self_check(grid),
        "recorded_draws": contexts[0].recorded_draws(),
        "overrides_used": contexts[0].overrides_used(),
    })
    grids.append(grid)

canonical_checks = []
for split in ("train", "test"):
    for index, pair in enumerate(canonical[split]):
        rival, analyses = route(pair["input"], True)
        canonical_checks.append({
            "split": split, "index": index,
            "self_check_errors": module.self_check(pair["input"]),
            "clear_fallback_rival_matches_canonical_output": rival == pair["output"],
            "both_elbows_blocked_colors": [a["color"] for a in analyses if a["horizontal_blockers"] and a["vertical_blockers"]],
        })

canonical_witness = canonical["train"][2]
rival, analyses = route(canonical_witness["input"], True)
generated_rival, generated_analyses = route(grids[0], True)
inputs = [grids[0], canonical_witness["input"]]
(OUT / "input.json").write_text(json.dumps(inputs, indent=2) + "\n")
(OUT / "rival.json").write_text(json.dumps({
    "rival_name": "clear_fallback_required",
    "definition": "Use the horizontal L if it is clear in the input; otherwise draw the vertical L only if it is clear. If neither L is clear, leave that pair undrawn. Preserve walls and paint pairs in reading order.",
    "outputs": [generated_rival, rival],
}, indent=2) + "\n")
report = {
    "task_id": TASK,
    "status": "audit-only; no generator or rule edits",
    "source": source,
    "generation_probe_denominator": len(cases),
    "unique_generated_inputs": len({digest(g) for g in grids}),
    "generation_cases": cases,
    "canonical_pair_denominator": len(canonical_checks),
    "canonical_checks": canonical_checks,
    "inputs": [
        {"input_index": 0, "provenance": "seed=0, sample_index=0, difficulty=medium; shared by all nine recorded override cases",
         "grid": inputs[0], "self_check_errors": module.self_check(inputs[0]),
         "documented_domain_membership": "Generated by the target. Runtime generation allows 2-4 pairs and 2-5 walls; narrower INVARIANTS text is stale.",
         "pair_analysis": generated_analyses},
        {"input_index": 1, "provenance": "canonical train[2] (third visible demonstration)",
         "seed": None, "sample_index": None, "overrides": None,
         "grid": inputs[1], "self_check_errors": module.self_check(inputs[1]),
         "documented_domain_membership": "Canonical input accepted by self_check; outside generator's enforced at-least-one-clear-elbow and cell-isolation restrictions.",
         "pair_analysis": analyses},
    ],
    "limits": "Nine deterministic generation calls at one seed/index and all five canonical labelled pairs. No stochastic coverage or general identifiability claim. Racket labels are obtained separately with the supported apply command.",
}
(OUT / "probe.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({"source": source, "generation_probe_denominator": len(cases),
                  "unique_generated_inputs": report["unique_generated_inputs"],
                  "generation_cases": cases, "canonical_checks": canonical_checks}, indent=2))
