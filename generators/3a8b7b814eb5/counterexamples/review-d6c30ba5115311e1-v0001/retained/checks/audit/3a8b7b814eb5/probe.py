#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from collections import Counter, defaultdict

TASK_ID = "3a8b7b814eb5"
ROOT = Path(__file__).resolve().parents[3] / "repo"
GENERATOR_PATH = ROOT / "generators" / TASK_ID / "generator.py"
CANONICAL_PATH = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
OUT = Path(__file__).resolve().parent


def load_generator():
    body = GENERATOR_PATH.read_bytes()
    spec = importlib.util.spec_from_file_location("audit_3a_generator", GENERATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    exec(compile(body, str(GENERATOR_PATH), "exec"), module.__dict__)
    return module, hashlib.sha256(body).hexdigest()


def canonical_row():
    for line in CANONICAL_PATH.open(encoding="utf-8"):
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise KeyError(TASK_ID)


def pairs(grid):
    points = defaultdict(list)
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color:
                points[color].append((r, c))
    rows = []
    for color, pts in sorted(points.items()):
        if len(pts) != 2:
            rows.append({"color": color, "points": pts, "orientation": "count_not_two"})
            continue
        top, bottom = sorted(pts)
        if top[0] == bottom[0] or top[1] == bottom[1]:
            orientation = "axis_aligned"
        elif top[1] < bottom[1]:
            orientation = "nw_se"
        else:
            orientation = "ne_sw"
        rows.append({"color": color, "points": pts, "orientation": orientation})
    return rows


def fill_nw_se_only(grid):
    out = [list(row) for row in grid]
    for row in pairs(grid):
        if row["orientation"] != "nw_se":
            continue
        (r0, c0), (r1, c1) = sorted(row["points"])
        color = row["color"]
        for r in range(r0, r1 + 1):
            for c in range(min(c0, c1), max(c0, c1) + 1):
                out[r][c] = color
    return out


def main():
    gen, source_sha = load_generator()
    sample = {}
    total = Counter()
    failures = []
    for band in ("easy", "medium", "hard"):
        orientations = Counter()
        unique = set()
        for index in range(100):
            seed = 900_000 + index * 41
            try:
                grid = gen.generate(seed, index, difficulty=band)
                diagnostics = gen.self_check(grid)
                if diagnostics:
                    raise AssertionError(diagnostics)
                unique.add(json.dumps(grid, separators=(",", ":")))
                for row in pairs(grid):
                    orientations[row["orientation"]] += 1
                    total[row["orientation"]] += 1
            except Exception as exc:
                failures.append({"band": band, "index": index, "seed": seed, "error": f"{type(exc).__name__}: {exc}"})
        sample[band] = {"draws": 100, "unique_inputs": len(unique), "orientations": dict(sorted(orientations.items()))}

    canonical = canonical_row()
    pair = canonical["train"][1]
    input_grid = pair["input"]
    expected = pair["output"]
    rival = fill_nw_se_only(input_grid)
    (OUT / "input.json").write_text(json.dumps(input_grid, indent=2) + "\n")
    (OUT / "rival-output.json").write_text(json.dumps(rival, indent=2) + "\n")

    report = {
        "schema": "arcpuzzles-audit-probe-v1",
        "task_id": TASK_ID,
        "generator_path": str(GENERATOR_PATH.relative_to(ROOT)),
        "generator_sha256": source_sha,
        "declared_rule_hash": getattr(gen, "RULE_HASH", None),
        "sample": {
            "seed_formula": "900000 + 41 * index",
            "sample_index_range": [0, 99],
            "bands": sample,
            "total_orientations": dict(sorted(total.items())),
            "failures": failures,
        },
        "counterexample": {
            "scope": "canonical train pair 1",
            "input": input_grid,
            "self_check": gen.self_check(input_grid),
            "expected_output": expected,
            "pair_orientations": pairs(input_grid),
            "rival": "fill only paired colors whose top cell is left of the bottom cell (NW-SE); leave NE-SW pairs unchanged",
            "rival_output": rival,
            "rival_fits_sampled_normal_domain": set(total) <= {"nw_se"},
            "rival_differs_from_expected": rival != expected,
        },
    }
    (OUT / "probe-result.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "generator_sha256": source_sha,
        "sampled_draws": 300,
        "orientations": dict(sorted(total.items())),
        "failures": len(failures),
        "canonical_pair_orientations": pairs(input_grid),
        "rival_differs": rival != expected,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
