#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import deque
from pathlib import Path

HERE = Path(__file__).resolve()
Grid = list[list[int]]


def components(grid: Grid, color: int) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
    result: list[list[tuple[int, int]]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        stack = [start]
        comp: list[tuple[int, int]] = []
        while stack:
            r, c = stack.pop()
            comp.append((r, c))
            for pos in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if pos in unseen:
                    unseen.remove(pos)
                    stack.append(pos)
        result.append(comp)
    return result


def prepare(grid: Grid) -> tuple[Grid, int, list[list[tuple[int, int]]]]:
    out = [row[:] for row in grid]
    target = out[0][0]
    out[0][0] = 0
    return out, target, components(out, target) if target else []


def topological_rule(grid: Grid) -> Grid:
    out, target, comps = prepare(grid)
    for comp in comps:
        rs = [r for r, _ in comp]
        cs = [c for _, c in comp]
        r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
        solid = set(comp)
        exterior: set[tuple[int, int]] = set()
        queue: deque[tuple[int, int]] = deque()
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if (r in (r0, r1) or c in (c0, c1)) and (r, c) not in solid:
                    exterior.add((r, c))
                    queue.append((r, c))
        while queue:
            r, c = queue.popleft()
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                pos = (nr, nc)
                if r0 <= nr <= r1 and c0 <= nc <= c1 and pos not in solid and pos not in exterior:
                    exterior.add(pos)
                    queue.append(pos)
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if (r, c) not in solid and (r, c) not in exterior:
                    out[r][c] = target
    return out


def bbox_fill_rival(grid: Grid) -> Grid:
    out, target, comps = prepare(grid)
    for comp in comps:
        rs = [r for r, _ in comp]
        cs = [c for _, c in comp]
        for r in range(min(rs), max(rs) + 1):
            for c in range(min(cs), max(cs) + 1):
                if out[r][c] == 0:
                    out[r][c] = target
    return out


probe = json.loads((HERE.parent / "probe-preapply.json").read_text())
racket = json.loads((HERE.parent / "racket.json").read_text())
inputs = json.loads((HERE.parent / "input.json").read_text())
assert racket["generator_sha256"] == probe["generator_sha256"]
assert racket["rule_hash_matches_catalog"] is True
assert len(racket["results"]) == len(inputs) == 31
assert all(row["error"] is None for row in racket["results"])
assert all(row["generator_domain"]["status"] == "valid" for row in racket["results"])
for grid, row in zip(inputs, racket["results"]):
    assert row["input"] == grid
    assert row["output"] == topological_rule(grid)

witness = racket["results"][0]
assert witness["output"] == probe["witness"]["python_topological_output"]
assert witness["output"] != bbox_fill_rival(witness["input"])
generated_rival_matches = sum(
    bbox_fill_rival(row["input"]) == row["output"]
    for row in racket["results"][1:]
)
assert generated_rival_matches == 30

record = {
    "schema": "arcpuzzles-audit-finding-v1",
    "task_id": probe["task_id"],
    "severity": "moderate",
    "finding": "Ordinary generation uses only hollow rectangles, so bbox filling is a perfect shortcut on the sampled support but fails an accepted nonrectangular component with both an enclosed hole and exterior-connected bbox space.",
    "generator_sha256": probe["generator_sha256"],
    "catalog_rule_hash": racket["catalog_rule_hash"],
    "executed_rule_hash": racket["executed_rule_hash"],
    "rule_hash_matches_catalog": racket["rule_hash_matches_catalog"],
    "rule_text_sha256": racket["rule_text_sha256"],
    "generated_census": {
        **probe["generated_census"],
        "rival_matches_actual_racket": generated_rival_matches,
    },
    "canonical_census": probe["canonical_census"],
    "input": witness["input"],
    "generator_domain": witness["generator_domain"],
    "actual_racket_output": witness["output"],
    "rival_name": probe["rival_name"],
    "rival_output": bbox_fill_rival(witness["input"]),
    "separating_cell": probe["witness"]["separating_cell"],
    "construction": probe["witness"]["construction"],
    "command": probe["apply_command"],
    "limitation": "Finite census of 30 ordinary draws; it does not prove every seed follows the rectangular shortcut.",
}
(HERE.parent / "finding.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
print(json.dumps({
    "task_id": probe["task_id"],
    "authority_verified": True,
    "generated_rival_fit": f"{generated_rival_matches}/30",
    "witness_rival_differs": True,
}, sort_keys=True))
