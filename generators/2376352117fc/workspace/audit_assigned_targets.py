"""Findings-only, hash-bound adversarial probes for the two drawn audit targets.

Run from repo: python generators/2376352117fc/workspace/audit_assigned_targets.py \
  --root . --out ../checks/audits --seeds 128
The authoritative sources of both targets are left unchanged.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

TARGETS = ("39c4e8d5275c", "cdb136a26980")


def wires(grid):
    seen_paths = []
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v != 2:
                continue
            queue = [(rr, cc) for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
                     if 0 <= rr < len(grid) and 0 <= cc < len(row) and grid[rr][cc] == 1]
            visited = set(queue)
            while queue:
                rr, cc = queue.pop()
                for a, b in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if 0 <= a < len(grid) and 0 <= b < len(row) and grid[a][b] == 1 and (a, b) not in visited:
                        visited.add((a, b))
                        queue.append((a, b))
            seen_paths.append(visited)
    return seen_paths


def widest_wire(grid):
    out = [row[:] for row in grid]
    paths = wires(grid)
    best = max(paths, key=lambda cells: max(c for _, c in cells) - min(c for _, c in cells))
    for r, c in best:
        out[r][c] = 3
    return out


def left_only(grid):
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        if 9 not in row:
            continue
        anchor = row.index(9)
        for c, value in enumerate(row):
            target = 2 * anchor - c
            if c < anchor and value not in (0, 9) and 0 <= target < len(row):
                out[r][target] = value
    return out


def canonical_pairs(record):
    """Normalize the corpus' row-string grids and singleton test dictionary."""
    test = record.get("test", [])
    tests = [test] if isinstance(test, dict) else test
    return [{key: [[int(value) for value in row] for row in pair[key]]
             for key in ("input", "output")}
            for pair in [*record.get("train", []), *tests]]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--seeds", type=int, default=128)
    args = ap.parse_args()
    root = args.root.resolve()
    args.out.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(root / "src"))
    from arcpuzzles.catalog import Catalog
    from arcpuzzles.runtime import prepare_runtime
    records = {row["task_id"]: row for row in map(json.loads, (root / "shared/data/canonical/puzzles.jsonl").open()) if row.get("task_id") in TARGETS}
    with tempfile.TemporaryDirectory(prefix="drawn-audits-") as tmp:
        stage = Path(tmp)
        prepare_runtime(Catalog(root), stage, task_ids=list(TARGETS))
        sys.path.insert(0, str(stage))
        from arc_repl.racket_bridge import RacketBridge
        from puzzle_generators.rule_wrap import wrap_rule
        with RacketBridge(max_calls_before_restart=512) as bridge:
            for tid, rival in zip(TARGETS, (widest_wire, left_only)):
                gp = stage / f"puzzle_generators/per_puzzle/{tid}/generator.py"
                spec = importlib.util.spec_from_file_location("audit_" + tid, gp)
                gen = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(gen)
                source = records[tid]["program_solution"]
                wrapped = wrap_rule(source)
                def apply(grid):
                    text = "(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
                    return bridge.eval_text(f"({wrapped} '{text})")
                report = {"task_id": tid, "generator_sha256": hashlib.sha256(gp.read_bytes()).hexdigest(),
                    "rule_sha256": hashlib.sha256(source.encode()).hexdigest(), "source_changed": False,
                    "cohort": {"bands": ["easy", "medium", "hard"], "seeds": [0, args.seeds - 1],
                               "sample_index": "same as seed", "requested": args.seeds * 3},
                    "canonical": [], "failures": []}
                for i, pair in enumerate(canonical_pairs(records[tid])):
                    actual = apply(pair["input"])
                    report["canonical"].append({"index": i, "racket_matches": actual == pair["output"],
                        "rival_matches": rival(pair["input"]) == actual, "self_check": gen.self_check(pair["input"])})
                matches = 0
                hashes = set()
                topology = Counter()
                first_override = None
                for band in ("easy", "medium", "hard"):
                    for seed in range(args.seeds):
                        grid = gen.generate(seed, seed, difficulty=band)
                        actual = apply(grid)
                        matches += rival(grid) == actual
                        hashes.add(hashlib.sha256(json.dumps(grid).encode()).hexdigest())
                        if tid == TARGETS[0]:
                            paths = wires(grid)
                            topology["horizontal_only"] += all(len({r for r, _ in path}) == 1 for path in paths)
                            topology["three_wires"] += len(paths) == 3
                            topology["lengths_3_5_7"] += sorted(map(len, paths)) == [3, 5, 7]
                            forced = gen.generate(seed, seed, difficulty=band, n_wires=1)
                            realized = sum(v == 2 for row in forced for v in row)
                            if first_override is None and realized != 1:
                                first_override = {"band": band, "seed": seed, "sample_index": seed,
                                    "overrides": {"n_wires": 1}, "actual_wire_starts": realized, "input": forced}
                        else:
                            right = sum(v not in (0, 9) and c > row.index(9)
                                        for row in grid if 9 in row for c, v in enumerate(row))
                            topology["any_right_source"] += right > 0
                            forced = gen.generate(seed, seed, difficulty=band, marks_per_row=1)
                            realized = [sum(v not in (0, 9) for v in row) for row in forced if 9 in row]
                            if first_override is None and any(n != 1 for n in realized):
                                first_override = {"band": band, "seed": seed, "sample_index": seed,
                                    "overrides": {"marks_per_row": 1}, "actual_marks_per_active_row": realized, "input": forced}
                report.update(default_rival_matches=matches, default_unique_inputs=len(hashes),
                              topology=dict(topology), ignored_override=first_override)
                if tid == TARGETS[0]:
                    counterexample = [[0] * 10 for _ in range(11)]
                    counterexample[1][1] = 2
                    for r in range(2, 10):
                        counterexample[r][1] = 1
                    counterexample[1][4] = 2
                    for c in range(5, 9):
                        counterexample[1][c] = 1
                    bad = gen.generate(0, 0, texture="no_red_start")
                    report["no_red_start"] = {"input": bad, "self_check": gen.self_check(bad)}
                    try:
                        report["no_red_start"]["output"] = apply(bad)
                    except Exception as exc:
                        report["no_red_start"]["racket_error"] = f"{type(exc).__name__}: {exc}"
                else:
                    original = gen.generate(0, 0, difficulty="medium")
                    counterexample = [list(reversed(row)) for row in original]
                actual = apply(counterexample)
                prediction = rival(counterexample)
                report["counterexample"] = {"input": counterexample, "racket_output": actual,
                    "rival_output": prediction, "self_check": gen.self_check(counterexample), "disagrees": actual != prediction}
                assert actual != prediction
                assert first_override is not None
                assert all(p["racket_matches"] for p in report["canonical"])
                (args.out / f"{tid}.json").write_text(json.dumps(report, indent=2) + "\n")
                print(json.dumps({key: report[key] for key in ("task_id", "generator_sha256", "cohort", "canonical", "default_rival_matches", "default_unique_inputs", "topology")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
