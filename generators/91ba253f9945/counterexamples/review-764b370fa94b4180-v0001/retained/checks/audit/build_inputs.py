#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

PACKET = Path(__file__).resolve().parents[2]
REPO = PACKET / "repo"
OUT = PACKET / "checks" / "audit"


def load(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def unconditional_plus(grid):
    h, w = len(grid), len(grid[0])
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 0:
                continue
            for dr, dc in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w:
                    out[nr][nc] = value
    return out


# Audit target 1: generate one ordinary panel/divider instance from the selected
# source; the canonical task expects two color-tripod coordinate frames instead.
g91, p91 = load("91ba253f9945")
grid91 = g91.generate(17, 9, difficulty="medium")
write(OUT / "91ba253f9945" / "input.json", grid91)
write(
    OUT / "91ba253f9945" / "source.json",
    {
        "task_id": g91.TASK_ID,
        "generator_sha256": sha(p91),
        "declared_rule_hash": getattr(g91, "RULE_HASH", None),
        "seed": 17,
        "sample_index": 9,
        "difficulty": "medium",
        "overrides": {},
        "self_check": g91.self_check(grid91),
        "shape": [len(grid91), len(grid91[0])],
        "colors": sorted({v for row in grid91 for v in row}),
        "documented_domain": True,
        "observation": "ordinary generated panel/divider grid; no required 2/3/4 and 5/6/7 coordinate frames",
    },
)

# Audit target 2A: source-domain lessons. The unconditional rival is expected to
# match the real rule because every generated colored cell is unique, isolated,
# interior, and far from every other cell.
g65, p65 = load("65a142eb4d9b")
grids65 = []
records65 = []
bands = ["easy"] * 21 + ["medium"] * 21 + ["hard"] * 22
for index, band in enumerate(bands):
    seed = 1000 + index
    sample_index = index * 7 + 3
    grid = g65.generate(seed, sample_index, difficulty=band)
    errors = g65.self_check(grid, difficulty=band)
    if errors:
        raise RuntimeError((index, errors))
    grids65.append(grid)
    records65.append(
        {
            "index": index,
            "seed": seed,
            "sample_index": sample_index,
            "difficulty": band,
            "self_check": errors,
        }
    )
write(OUT / "65a142eb4d9b" / "generated-inputs.json", {"inputs": grids65})
write(
    OUT / "65a142eb4d9b" / "generated-rival.json",
    {"outputs": [unconditional_plus(grid) for grid in grids65]},
)
write(
    OUT / "65a142eb4d9b" / "generated-source.json",
    {
        "task_id": g65.TASK_ID,
        "generator_sha256": sha(p65),
        "declared_rule_hash": getattr(g65, "RULE_HASH", None),
        "draws": len(grids65),
        "records": records65,
        "documented_domain": True,
        "rival": "paint a clipped plus around every nonzero cell, ignoring same-color cardinal neighbors",
    },
)

# Audit target 2B: a validator-accepted branch witness. The adjacent 4-cells
# each have a same-color cardinal neighbor and therefore must remain unchanged;
# the isolated 6 must expand. This is outside the normal sampler's stated domain
# but accepted by its self_check, exposing both distribution and validator gaps.
counterexample = [[0] * 7 for _ in range(7)]
counterexample[2][2] = 4
counterexample[2][3] = 4
counterexample[5][5] = 6
write(OUT / "65a142eb4d9b" / "counterexample-input.json", counterexample)
write(
    OUT / "65a142eb4d9b" / "counterexample-rival.json",
    {"outputs": [unconditional_plus(counterexample)]},
)
write(
    OUT / "65a142eb4d9b" / "counterexample-source.json",
    {
        "task_id": g65.TASK_ID,
        "generator_sha256": sha(p65),
        "declared_rule_hash": getattr(g65, "RULE_HASH", None),
        "self_check": g65.self_check(counterexample),
        "documented_domain": False,
        "reason_outside_documented_domain": "contains a same-color cardinally adjacent pair",
        "purpose": "distinguish the real isolation precondition from unconditional plus stamping",
    },
)
