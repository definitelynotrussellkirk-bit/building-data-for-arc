#!/usr/bin/env python3
from __future__ import annotations

from collections import deque
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / "shared/runtime"))


def load(task):
    path = ROOT / "generators" / task / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module, path


def canonical(task):
    for line in (ROOT / "shared/data/canonical/puzzles.jsonl").open():
        row = json.loads(line)
        if row.get("task_id") == task:
            test = row["test"] if isinstance(row["test"], list) else [row["test"]]
            return row, list(row["train"]) + list(test)
    raise KeyError(task)


def rectangle_border(grid, cutoff=7):
    h, w = len(grid), len(grid[0])
    out = [[0] * w for _ in range(h)]
    by = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                by.setdefault(value, []).append((r, c))
    for color, points in by.items():
        if len(points) != 2:
            continue
        (r0, c0), (r1, c1) = points
        r0, r1 = sorted((r0, r1)); c0, c1 = sorted((c0, c1))
        if r1 - r0 > cutoff or c1 - c0 > cutoff:
            continue
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if r in (r0, r1) or c in (c0, c1):
                    out[r][c] = color
    return out


def rectangle_authority(grid):
    return rectangle_border(grid, cutoff=10**9)


def components(grid):
    h, w = len(grid), len(grid[0]); seen = set(); result = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            todo = [(r, c)]; seen.add((r, c)); cells = set()
            while todo:
                rr, cc = todo.pop(); cells.add((rr, cc))
                for dr, dc in ((-1,0),(1,0),(0,-1),(0,1)):
                    nr, nc = rr+dr, cc+dc
                    if 0 <= nr < h and 0 <= nc < w and (nr,nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr,nc)); todo.append((nr,nc))
            result.append((color, cells))
    return result


def border_authority(grid, cutoff=None):
    h, w = len(grid), len(grid[0]); out = [[0]*w for _ in range(h)]
    for color, cells in components(grid):
        touches = any(r in (0,h-1) or c in (0,w-1) for r,c in cells)
        if touches and (cutoff is None or len(cells) <= cutoff):
            for r,c in cells: out[r][c] = color
    return out


def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    reports = {}

    # 1713: the sampler hard-codes each corner span to 2..4 cells, although
    # self_check has no span ceiling and canonical rectangles are larger.
    task = "1713e09a3132"; gen, path = load(task); row, pairs = canonical(task)
    maximum = [0, 0]; failures = []; rival_mismatches = []
    samples = 0
    for band in ("easy", "medium", "hard"):
        for index in range(200):
            grid = gen.generate(171300 + index, index, difficulty=band)
            errors = gen.self_check(grid)
            if errors: failures.append({"band":band,"index":index,"errors":errors})
            by = {}
            for r, line in enumerate(grid):
                for c, value in enumerate(line):
                    if value: by.setdefault(value, []).append((r,c))
            for points in by.values():
                if len(points) == 2:
                    maximum[0] = max(maximum[0], abs(points[0][0]-points[1][0]))
                    maximum[1] = max(maximum[1], abs(points[0][1]-points[1][1]))
            if rectangle_border(grid) != rectangle_authority(grid):
                rival_mismatches.append({"band":band,"index":index})
            samples += 1
    counter = [[0]*12 for _ in range(10)]
    counter[0][0] = counter[8][8] = 2
    counter[0][9] = counter[2][11] = 5
    (ROOT.parent / "checks/audit/1713e09a3132/input.json").write_text(json.dumps(counter)+"\n")
    (ROOT.parent / "checks/audit/1713e09a3132/rival.json").write_text(json.dumps(rectangle_border(counter))+"\n")
    reports[task] = {
        "finding": "cap_every_rectangle_span_at_7 shortcut fits canonical pairs and sampled production but fails a lawful span-8 rectangle",
        "generator_sha256": digest(path), "declared_rule_hash": getattr(gen,"RULE_HASH",None),
        "sampled": samples, "bands": ["easy","medium","hard"], "indices_per_band": "0..199",
        "maximum_observed_row_span": maximum[0], "maximum_observed_col_span": maximum[1],
        "sample_self_check_failures": failures, "sample_rival_mismatches": rival_mismatches,
        "canonical_pairs_fit_rival": all(rectangle_border(p["input"]) == p["output"] for p in pairs),
        "counterexample_self_check": gen.self_check(counter),
        "counterexample_input": counter, "rival_output": rectangle_border(counter),
        "authority_mirror_output": rectangle_authority(counter),
    }

    # b46: all production shapes have 2..4 cells, though the validator has no
    # upper bound and the rule is size-independent.
    task = "b46e718788e1"; gen, path = load(task); row, pairs = canonical(task)
    maximum_size = 0; failures = []; rival_mismatches = []; samples = 0
    for band in ("easy", "medium", "hard"):
        for index in range(200):
            grid = gen.generate(246000 + index, index, difficulty=band)
            errors = gen.self_check(grid)
            if errors: failures.append({"band":band,"index":index,"errors":errors})
            maximum_size = max(maximum_size, *(len(cells) for _,cells in components(grid)))
            if border_authority(grid, cutoff=4) != border_authority(grid):
                rival_mismatches.append({"band":band,"index":index})
            samples += 1
    counter = [[0]*7 for _ in range(6)]
    for c in range(1,6): counter[0][c] = 2
    counter[3][2] = counter[3][3] = 4
    (ROOT.parent / "checks/audit/b46e718788e1/input.json").write_text(json.dumps(counter)+"\n")
    (ROOT.parent / "checks/audit/b46e718788e1/rival.json").write_text(json.dumps(border_authority(counter, cutoff=4))+"\n")
    reports[task] = {
        "finding": "keep_border_object_only_when_size_at_most_4 shortcut fits sampled production but fails a lawful size-5 border object",
        "generator_sha256": digest(path), "declared_rule_hash": getattr(gen,"RULE_HASH",None),
        "sampled": samples, "bands": ["easy","medium","hard"], "indices_per_band": "0..199",
        "maximum_observed_object_size": maximum_size,
        "sample_self_check_failures": failures, "sample_rival_mismatches": rival_mismatches,
        "canonical_pairs_fit_rival": all(border_authority(p["input"], cutoff=4) == p["output"] for p in pairs),
        "counterexample_self_check": gen.self_check(counter),
        "counterexample_input": counter, "rival_output": border_authority(counter, cutoff=4),
        "authority_mirror_output": border_authority(counter),
    }

    for task, report in reports.items():
        out = ROOT.parent / f"checks/audit/{task}/analysis.json"
        out.write_text(json.dumps(report, indent=2, sort_keys=True)+"\n")
    print(json.dumps({task:{k:v for k,v in report.items() if k in (
        "sampled","maximum_observed_row_span","maximum_observed_col_span",
        "maximum_observed_object_size","canonical_pairs_fit_rival",
        "counterexample_self_check","sample_rival_mismatches")}
        for task,report in reports.items()}, indent=2, sort_keys=True))

if __name__ == "__main__": main()
