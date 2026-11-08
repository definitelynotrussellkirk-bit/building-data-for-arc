#!/usr/bin/env python3
"""Finite source-bound audit for required 1-component shape coverage in 7d9e19053098."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

TASK_ID = "7d9e19053098"
REQUIRED = ("hline", "vline", "square")


def _load_generator(repo: Path):
    source = repo / "generators" / TASK_ID / "generator.py"
    runtime = repo / "shared" / "runtime"
    sys.path.insert(0, str(runtime))
    spec = importlib.util.spec_from_file_location("peer_shape_audit_generator", source)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, source


def _components(grid):
    height, width = len(grid), len(grid[0])
    seen, result = set(), []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 1 or (row, col) in seen:
                continue
            todo, cells = [(row, col)], []
            seen.add((row, col))
            while todo:
                r, c = todo.pop()
                cells.append((r, c))
                for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (0 <= rr < height and 0 <= cc < width and grid[rr][cc] == 1
                            and (rr, cc) not in seen):
                        seen.add((rr, cc))
                        todo.append((rr, cc))
            result.append(cells)
    return result


def _classify(cells):
    rows, cols = [r for r, _ in cells], [c for _, c in cells]
    height = max(rows) - min(rows) + 1
    width = max(cols) - min(cols) + 1
    if height == 1 and width >= 2 and len(cells) == width:
        return "hline"
    if width == 1 and height >= 2 and len(cells) == height:
        return "vline"
    if height == width and height >= 2 and len(cells) == height * width:
        return "square"
    return "other"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--seeds", type=int, default=64)
    parser.add_argument("--samples", type=int, default=8)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.seeds < 1 or args.samples < 1:
        parser.error("--seeds and --samples must be positive")
    if args.out.exists() or args.out.is_symlink():
        raise FileExistsError(args.out)

    repo = args.repo.resolve()
    module, source = _load_generator(repo)
    source_before = source.read_bytes()
    total_kinds = Counter()
    failures = []
    for difficulty in ("easy", None, "hard"):
        band = "medium" if difficulty is None else difficulty
        for seed in range(args.seeds):
            for sample_index in range(args.samples):
                grid = module.generate(seed, sample_index, difficulty=difficulty)
                kinds = Counter(_classify(cells) for cells in _components(grid))
                total_kinds.update(kinds)
                missing = [kind for kind in REQUIRED if kinds[kind] < 1]
                self_check = module.self_check(grid, difficulty=difficulty)
                if missing or self_check:
                    failures.append({
                        "difficulty": band,
                        "seed": seed,
                        "sample_index": sample_index,
                        "shape": [len(grid), len(grid[0])],
                        "kinds": dict(kinds),
                        "missing": missing,
                        "self_check": self_check,
                        "input": grid,
                    })
    if source.read_bytes() != source_before:
        raise RuntimeError("generator changed during audit")
    draws = args.seeds * args.samples * 3
    report = {
        "schema": "arcpuzzles-bounded-peer-audit-v1",
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(source_before).hexdigest(),
        "scope": f"{args.seeds} seeds x {args.samples} sample indices x 3 difficulty bands = {draws} draws; finite invariant/teaching audit only.",
        "draws": draws,
        "component_counts": dict(total_kinds),
        "failure_count": len(failures),
        "missing_counts": {kind: sum(kind in row["missing"] for row in failures) for kind in REQUIRED},
        "self_check_failure_count": sum(bool(row["self_check"]) for row in failures),
        "self_check_missed_failure_count": sum(bool(row["missing"]) and not row["self_check"] for row in failures),
        "first_failure": failures[0] if failures else None,
        "status": "finding" if failures else "no_finding",
        "finding": "Placement can omit a required teaching shape." if failures else None,
        "suggested_repair": ("Retry the complete scene or fail explicitly until all three classes exist; strengthen self_check to reconstruct components."
                             if failures else None),
        "limits": "No protected-Racket labels were needed for this input-distribution invariant check; finite sample only.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in (
        "draws", "failure_count", "missing_counts", "self_check_failure_count",
        "self_check_missed_failure_count", "status")}, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
