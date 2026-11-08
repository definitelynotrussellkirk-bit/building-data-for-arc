#!/usr/bin/env python3
"""Independent adversarial probe for audit target 4e16917b1bde."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

from reviewer_support import canonical_pairs

TASK_ID = "4e16917b1bde"
REPO = Path.cwd()
SOURCE = REPO / "generators" / TASK_ID / "generator.py"

spec = importlib.util.spec_from_file_location("audit_4e", SOURCE)
assert spec and spec.loader
GEN = importlib.util.module_from_spec(spec)
spec.loader.exec_module(GEN)


def selected(grid, predicate):
    errors, facts = GEN._analyze(grid)
    if errors:
        raise ValueError(errors)
    out = [list(row) for row in grid]
    for row, col, value in facts["sources"]:
        if predicate(row, col, value, facts):
            out[row][2 * facts["divider_col"] - col] = value
    return out


def nearest_only(grid):
    _, facts = GEN._analyze(grid)
    distance = min(abs(col - facts["divider_col"]) for _, col, _ in facts["sources"])
    return selected(grid, lambda _r, c, _v, f: abs(c - f["divider_col"]) == distance)


def farthest_only(grid):
    _, facts = GEN._analyze(grid)
    distance = max(abs(col - facts["divider_col"]) for _, col, _ in facts["sources"])
    return selected(grid, lambda _r, c, _v, f: abs(c - f["divider_col"]) == distance)


def minimum_color_only(grid):
    _, facts = GEN._analyze(grid)
    color = min(value for _, _, value in facts["sources"])
    return selected(grid, lambda _r, _c, value, _f: value == color)


def maximum_color_only(grid):
    _, facts = GEN._analyze(grid)
    color = max(value for _, _, value in facts["sources"])
    return selected(grid, lambda _r, _c, value, _f: value == color)


def top_half_only(grid):
    _, facts = GEN._analyze(grid)
    return selected(grid, lambda row, _c, _v, f: row < f["grid_h"] / 2)


def bottom_half_only(grid):
    _, facts = GEN._analyze(grid)
    return selected(grid, lambda row, _c, _v, f: row >= f["grid_h"] / 2)


custom_rivals = {
    "nearest_offset_only": nearest_only,
    "farthest_offset_only": farthest_only,
    "minimum_numeric_color_only": minimum_color_only,
    "maximum_numeric_color_only": maximum_color_only,
    "top_half_only": top_half_only,
    "bottom_half_only": bottom_half_only,
}
rivals = dict(GEN.LESSON_COMPETITORS)
rivals.update(custom_rivals)

canonical = canonical_pairs(TASK_ID, root=REPO)
canonical_rule_matches = [GEN.rule_mirror(pair["input"]) == pair["output"] for pair in canonical]
assert all(canonical_rule_matches)

bands = {}
for band in ("easy", "medium", "hard"):
    invalid = 0
    unique = set()
    witness_hits = {name: 0 for name in GEN.SEMANTIC_WITNESSES}
    for index in range(200):
        grid = GEN.generate(410000 + index, index, difficulty=band)
        invalid += bool(GEN.self_check(grid))
        unique.add(json.dumps(grid, separators=(",", ":")))
        for name, predicate in GEN.SEMANTIC_WITNESSES.items():
            witness_hits[name] += bool(predicate(grid))
    assert invalid == 0

    surviving_windows = []
    for start in range(100):
        demos = []
        for offset in range(GEN.EXAMPLES_NEEDED):
            grid = GEN.generate(730000 + start, start + offset, difficulty=band)
            demos.append({"input": grid, "output": GEN.rule_mirror(grid)})
        query_grid = GEN.generate(
            730000 + start, start + GEN.EXAMPLES_NEEDED, difficulty=band
        )
        query = {"input": query_grid, "output": GEN.rule_mirror(query_grid)}
        reasons = GEN.lesson_identifiable(demos, query)
        assert reasons == [], (band, start, reasons)
        survivors = [
            name
            for name, rival in rivals.items()
            if all(rival(item["input"]) == item["output"] for item in demos)
        ]
        if survivors:
            surviving_windows.append({"start": start, "rivals": survivors})
    assert not surviving_windows
    bands[band] = {
        "generated_inputs": 200,
        "unique_inputs": len(unique),
        "invalid_inputs": invalid,
        "four_demo_windows": 100,
        "rivals_checked": len(rivals),
        "surviving_rival_windows": surviving_windows,
        "witness_hits": witness_hits,
    }

report = {
    "schema": "arcpuzzles-adversarial-audit-probe-v1",
    "task_id": TASK_ID,
    "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "rule_hash": GEN.RULE_HASH,
    "canonical_pairs": len(canonical),
    "canonical_rule_matches": sum(canonical_rule_matches),
    "declared_rivals": sorted(GEN.LESSON_COMPETITORS),
    "additional_rivals": sorted(custom_rivals),
    "bands": bands,
    "verdict": "no_issue_found_in_checked_scope",
    "limitations": (
        "Finite source-bound sampling and a finite rival family do not prove unique induction."
    ),
}
Path("../checks/audit/4e16917b1bde/report.json").write_text(
    json.dumps(report, indent=2) + "\n"
)
print(json.dumps(report, indent=2))
