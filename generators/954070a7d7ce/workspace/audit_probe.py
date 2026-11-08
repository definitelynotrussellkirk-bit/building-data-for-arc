"""Findings-only reproduction for the two immutable audit assignments.

No audited generator or Racket authority is edited. Run through the packet's
run_with_racket.py; outputs are evidence, not new safety/approval labels.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib
import json
from pathlib import Path
import sys
import tempfile

REPO = Path(__file__).resolve().parents[3]
AUDITS = ("62cf899c2e1b", "9917c0a4fb29")


def rotations(g):
    values = []
    current = [row[:] for row in g]
    for _ in range(4):
        values.append(current)
        current = [list(row) for row in zip(*current[::-1])]
    return values


def collage(g):
    r0, r90, r180, r270 = rotations(g)
    return [a + b for a, b in zip(r0, r270)] + [a + b for a, b in zip(r180, r90)]


def mirror(g, *, left_only=False):
    h, w = len(g), len(g[0])
    guides = [c for c in range(w) if all(g[r][c] == 9 for r in range(h))]
    out = [row[:] for row in g]
    if not guides:
        return out
    guide = guides[0]
    for r in range(h):
        for c in range(w):
            v, mc = g[r][c], 2 * guide - c
            if v in (0, 9) or (left_only and c >= guide):
                continue
            if 0 <= mc < w and out[r][mc] == 0:
                out[r][mc] = v
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--per-band", type=int, default=200)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(REPO / "src"))
    from arcpuzzles.catalog import Catalog
    from arcpuzzles.runtime import prepare_runtime
    canonical = {}
    for line in (REPO / "shared/data/canonical/puzzles.jsonl").open():
        row = json.loads(line)
        if row.get("task_id") in AUDITS:
            canonical[row["task_id"]] = row
    reports = {}
    with tempfile.TemporaryDirectory(prefix="frame-review-audits-") as temporary:
        runtime = Path(temporary) / "runtime"
        prepare_runtime(Catalog(REPO), runtime, task_ids=list(AUDITS))
        sys.path.insert(0, str(runtime))
        from puzzle_generators import runner
        for task in AUDITS:
            gen = importlib.import_module(f"puzzle_generators.per_puzzle.{task}.generator")
            report = {"task_id": task, "generator_sha256": hashlib.sha256(Path(gen.__file__).read_bytes()).hexdigest(),
                      "runtime_directory": str(runtime), "default_draws": 0, "default_self_check_failures": 0,
                      "canonical": [], "witnesses": [], "failures": []}
            bundle = runner._load_bundle(task)
            bridge, fn = runner._open_bridge_with_rule(bundle.rule_callable_text)
            try:
                def authority(g):
                    return runner._apply_rule(bridge, fn, g)
                for split in ("train", "test"):
                    for index, pair in enumerate(canonical[task][split]):
                        actual = authority(pair["input"])
                        entry = {"split": split, "index": index, "authority_matches_pair": actual == pair["output"],
                                 "self_check": gen.self_check(pair["input"])}
                        if task == AUDITS[1]:
                            rival = mirror(pair["input"], left_only=True)
                            entry["left_only_matches_pair"] = rival == pair["output"]
                            entry["left_only_missed_cells"] = [[r, c] for r, row in enumerate(actual) for c, v in enumerate(row)
                                                              if rival[r][c] != v]
                        report["canonical"].append(entry)
                        if not entry["authority_matches_pair"]:
                            report["failures"].append({"canonical": entry})
                rotation_counts = Counter()
                right_source_cases = 0
                first_default_symmetry = None
                for band in ("easy", "medium", "hard"):
                    for seed in range(args.per_band):
                        g = gen.generate(seed, seed % 8, difficulty=band)
                        report["default_draws"] += 1
                        report["default_self_check_failures"] += bool(gen.self_check(g))
                        if task == AUDITS[0]:
                            unique = len({json.dumps(rot) for rot in rotations(g)})
                            rotation_counts[str(unique)] += 1
                            if unique < 4 and first_default_symmetry is None:
                                first_default_symmetry = {"seed": seed, "sample_index": seed % 8, "difficulty": band,
                                                          "input": g, "distinct_rotations": unique,
                                                          "self_check": gen.self_check(g), "reference_output": authority(g)}
                        else:
                            guide = next(c for c in range(len(g[0])) if all(row[c] == 9 for row in g))
                            right_source_cases += any(v not in (0, 9) for row in g for v in row[guide + 1:])
                if task == AUDITS[0]:
                    report["default_distinct_rotation_counts"] = dict(rotation_counts)
                    if first_default_symmetry is not None:
                        report["witnesses"].append({"type": "default_rotation_collision", **first_default_symmetry})
                    overrides = {"grid_n": 4, "palette_size": 2, "texture": "checkerboard", "bg_density": 0,
                                 "noise_overlay": 0, "asymmetry_force": True}
                    g = gen.generate(0, 0, difficulty="medium", **overrides)
                    report["witnesses"].append({"type": "helpful_override_rotation_collision", "seed": 0, "sample_index": 0,
                                              "difficulty": "medium", "overrides": overrides, "input": g,
                                              "distinct_rotations": len({json.dumps(rot) for rot in rotations(g)}),
                                              "self_check": gen.self_check(g), "reference_output": authority(g),
                                              "authority_matches_collage": authority(g) == collage(g)})
                    flat = [[2] * 4 for _ in range(4)]
                    report["witnesses"].append({"type": "checker_accepts_monochrome", "input": flat,
                                              "distinct_rotations": 1, "self_check": gen.self_check(flat)})
                else:
                    report["default_cases_with_right_side_source"] = right_source_cases
                    g = [[0] * 9 for _ in range(5)]
                    for row in g:
                        row[4] = 9
                    g[2][6] = 3
                    actual = authority(g)
                    report["witnesses"].append({"type": "missing_right_to_left_branch", "input": g,
                                              "reference_output": actual, "left_only_output": mirror(g, left_only=True),
                                              "reference_matches_bidirectional_mirror": actual == mirror(g),
                                              "self_check": gen.self_check(g), "missing_cell": [2, 2]})
            finally:
                bridge.shutdown()
            (args.out / f"{task}.json").write_text(json.dumps(report, indent=2) + "\n")
            reports[task] = {key: value for key, value in report.items() if key not in ("witnesses", "canonical")}
    (args.out / "summary.json").write_text(json.dumps(reports, indent=2) + "\n")
    print(json.dumps(reports, indent=2))
    return int(any(report["failures"] for report in reports.values()))


if __name__ == "__main__":
    raise SystemExit(main())
