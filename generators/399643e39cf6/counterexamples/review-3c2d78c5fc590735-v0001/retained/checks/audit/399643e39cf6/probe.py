#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

PACKET = Path(__file__).resolve().parents[3]
REPO = PACKET / "repo"
TASK = "399643e39cf6"
sys.path.insert(0, str(REPO / "shared" / "runtime"))


def load_generator():
    path = REPO / "generators" / TASK / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{TASK}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module, path


def components_without_markers(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color in (0, 9) or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append({
                "color": color,
                "cells": sorted(cells),
                "size": len(cells),
                "top": min(rr for rr, _ in cells),
                "left": min(cc for _, cc in cells),
            })
    return result


def marker_vector(grid):
    markers = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 9]
    if len(markers) != 2:
        raise ValueError(f"expected two markers, found {markers}")
    (r1, c1), (r2, c2) = markers
    return markers, (r2 - r1, c2 - c1)


def apply_choice(grid, choice):
    markers, (dr, dc) = marker_vector(grid)
    comps = components_without_markers(grid)
    if choice == "smallest":
        obj = min(comps, key=lambda x: (x["size"], x["top"], x["left"], x["color"]))
    elif choice == "topmost":
        obj = min(comps, key=lambda x: (x["top"], x["left"], x["color"]))
    else:
        raise ValueError(choice)
    out = [[0 if value == 9 else value for value in row] for row in grid]
    h, w = len(grid), len(grid[0])
    targets = [(r + dr, c + dc) for r, c in obj["cells"]]
    if not all(0 <= r < h and 0 <= c < w for r, c in targets):
        raise ValueError(f"translated cells out of bounds: {targets}")
    for r, c in targets:
        out[r][c] = obj["color"]
    return out


def canonical_row():
    for line in (REPO / "shared" / "data" / "canonical" / "puzzles.jsonl").open():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            return row
    raise AssertionError("canonical row missing")


def main():
    gen, path = load_generator()
    row = canonical_row()
    tests = row["test"] if isinstance(row["test"], list) else [row["test"]]
    def norm(grid):
        return [
            [int(value) for value in row_value] if isinstance(row_value, str) else [int(value) for value in row_value]
            for row_value in grid
        ]
    pairs = [
        {"input": norm(pair["input"]), "output": norm(pair["output"])}
        for pair in [*row["train"], *tests]
    ]
    canonical_fit = [apply_choice(pair["input"], "topmost") == pair["output"] for pair in pairs]
    assert all(canonical_fit), canonical_fit

    candidate = None
    crashes = []
    malformed = []
    for band in ("easy", "medium", "hard"):
        for seed in range(400):
            for sample_index in range(20):
                try:
                    grid = gen.generate(seed, sample_index, difficulty=band)
                except Exception as exc:
                    crashes.append({"band": band, "seed": seed, "sample_index": sample_index,
                                    "error": f"{type(exc).__name__}: {exc}"})
                    continue
                check = gen.self_check(grid, difficulty=band)
                comps = components_without_markers(grid)
                if check or len(comps) != 2 or sorted(obj["size"] for obj in comps) != [3, 4]:
                    malformed.append({
                        "band": band, "seed": seed, "sample_index": sample_index,
                        "self_check": check, "components": comps,
                    })
                    continue
                try:
                    intended = apply_choice(grid, "smallest")
                    rival = apply_choice(grid, "topmost")
                except ValueError:
                    continue
                if intended == rival:
                    continue
                smallest = min(comps, key=lambda x: (x["size"], x["top"], x["left"], x["color"]))
                topmost = min(comps, key=lambda x: (x["top"], x["left"], x["color"]))
                candidate = {
                    "difficulty": band,
                    "seed": seed,
                    "sample_index": sample_index,
                    "input": grid,
                    "self_check": check,
                    "markers_and_vector": marker_vector(grid),
                    "components": comps,
                    "smallest": smallest,
                    "topmost": topmost,
                    "intended_python": intended,
                    "rival_output": rival,
                }
                break
            if candidate:
                break
        if candidate:
            break
    assert candidate is not None

    source_sha = hashlib.sha256(path.read_bytes()).hexdigest()
    program = row["program_solution"]
    rule_hash = hashlib.sha256(" ".join(program.split()).encode()).hexdigest()
    report = {
        "schema": "adversarial-audit-probe-v1",
        "task_id": TASK,
        "generator_sha256": source_sha,
        "canonical_program_normalized_sha256": rule_hash,
        "declared_rule_hash": getattr(gen, "RULE_HASH", None),
        "rival": "copy the topmost ordinary component by the marker vector instead of the smallest component",
        "canonical_pairs": len(pairs),
        "canonical_fit": sum(canonical_fit),
        "canonical_fit_vector": canonical_fit,
        "candidate": candidate,
        "scan": {
            "bands": ["easy", "medium", "hard"],
            "seed_range": "0..399",
            "sample_index_range": "0..19",
            "crashes_before_candidate": crashes[:20],
            "crash_count_before_candidate": len(crashes),
            "malformed_before_candidate": malformed[:20],
            "malformed_count_before_candidate": len(malformed),
        },
        "domain": "ordinary generator output; no overrides or degenerate texture; self_check returned []",
        "command": ["python3", "checks/audit/399643e39cf6/probe.py"],
        "cwd": "packet_root",
    }
    out_dir = Path(__file__).resolve().parent
    (out_dir / "input.json").write_text(json.dumps(candidate["input"], indent=2) + "\n")
    (out_dir / "diagnostic.json").write_text(json.dumps(report, indent=2) + "\n")
    (out_dir / "rival.json").write_text(json.dumps({
        "task_id": TASK,
        "rival": report["rival"],
        "output": candidate["rival_output"],
    }, indent=2) + "\n")
    print(json.dumps({
        "task_id": TASK,
        "candidate": {k: candidate[k] for k in ("difficulty", "seed", "sample_index", "markers_and_vector")},
        "canonical_fit": report["canonical_fit"],
        "generator_sha256": source_sha,
        "smallest": candidate["smallest"],
        "topmost": candidate["topmost"],
    }, indent=2))


if __name__ == "__main__":
    main()
