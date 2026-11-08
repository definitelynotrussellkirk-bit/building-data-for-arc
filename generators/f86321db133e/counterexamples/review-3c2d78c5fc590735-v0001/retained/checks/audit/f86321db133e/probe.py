#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

PACKET = Path(__file__).resolve().parents[3]
REPO = PACKET / "repo"
TASK = "f86321db133e"
sys.path.insert(0, str(REPO / "shared" / "runtime"))


def load_generator():
    path = REPO / "generators" / TASK / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{TASK}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module, path


def components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
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
            top = min(rr for rr, _ in cells)
            left = min(cc for _, cc in cells)
            normalized = sorted((rr - top, cc - left) for rr, cc in cells)
            height = max(rr for rr, _ in normalized) + 1
            width = max(cc for _, cc in normalized) + 1
            result.append({
                "color": color,
                "cells": sorted(cells),
                "normalized": normalized,
                "size": len(cells),
                "top": top,
                "left": left,
                "height": height,
                "width": width,
            })
    return result


def pack(grid, tie):
    comps = components(grid)
    if tie == "color":
        comps.sort(key=lambda x: (-x["size"], x["color"]))
    elif tie == "reading_order":
        comps.sort(key=lambda x: (-x["size"], x["top"], x["left"], x["color"]))
    else:
        raise ValueError(tie)
    out_h = max(obj["height"] for obj in comps)
    out_w = sum(obj["width"] for obj in comps) + len(comps) - 1
    out = [[0] * out_w for _ in range(out_h)]
    left = 0
    for obj in comps:
        for r, c in obj["normalized"]:
            out[r][left + c] = obj["color"]
        left += obj["width"] + 1
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
    canonical_fit = [pack(pair["input"], "reading_order") == pair["output"] for pair in pairs]
    assert all(canonical_fit), canonical_fit

    candidate = None
    crashes = []
    for band in ("easy", "medium", "hard"):
        for seed in range(200):
            for sample_index in range(12):
                try:
                    grid = gen.generate(seed, sample_index, difficulty=band)
                except Exception as exc:
                    crashes.append({"band": band, "seed": seed, "sample_index": sample_index,
                                    "error": f"{type(exc).__name__}: {exc}"})
                    continue
                intended = pack(grid, "color")
                rival = pack(grid, "reading_order")
                if intended == rival:
                    continue
                comps = components(grid)
                tie_sizes = sorted({obj["size"] for obj in comps if sum(x["size"] == obj["size"] for x in comps) > 1})
                if not tie_sizes:
                    continue
                candidate = {
                    "difficulty": band,
                    "seed": seed,
                    "sample_index": sample_index,
                    "input": grid,
                    "components": comps,
                    "tie_sizes": tie_sizes,
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
        "rival": "sort by area descending, but break equal-area ties by input reading order instead of color ascending",
        "canonical_pairs": len(pairs),
        "canonical_fit": sum(canonical_fit),
        "canonical_fit_vector": canonical_fit,
        "candidate": candidate,
        "scan": {
            "bands": ["easy", "medium", "hard"],
            "seed_range": "0..199",
            "sample_index_range": "0..11",
            "crashes_before_candidate": crashes[:20],
            "crash_count_before_candidate": len(crashes),
        },
        "domain": "ordinary generator output; no overrides or degenerate texture",
        "command": ["python3", "checks/audit/f86321db133e/probe.py"],
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
        "candidate": {k: candidate[k] for k in ("difficulty", "seed", "sample_index", "tie_sizes")},
        "canonical_fit": report["canonical_fit"],
        "generator_sha256": source_sha,
    }, indent=2))


if __name__ == "__main__":
    main()
