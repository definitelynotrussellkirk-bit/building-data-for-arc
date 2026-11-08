"""Source-bound axis repair probe; run through review.py with the local venv.

Capture defaults before editing:
  python generators/70c9dccdcc4d/workspace/verify_axes.py --out ../checks/70c9dccdcc4d/defaults-before
After editing, replay defaults and check bounded edges with real Racket labels:
  python generators/70c9dccdcc4d/workspace/verify_axes.py --baseline ../checks/70c9dccdcc4d/defaults-before/report.json --out ../checks/70c9dccdcc4d/edges-after
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import time

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator


TASK = "70c9dccdcc4d"


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def positions(grid):
    return {color: [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == color]
            for color in (2, 3, 4, 5, 6, 7, 8)}


def delta(point, origin):
    return point[0] - origin[0], point[1] - origin[1]


def expected_output(grid):
    """Independent coordinate calculation; never calls generator geometry helpers."""
    found = positions(grid)
    source, target = found[2][0], found[5][0]
    sx, sy = delta(found[3][0], source), delta(found[4][0], source)
    tx, ty = delta(found[6][0], target), delta(found[7][0], target)
    output = [row[:] for row in grid]
    for mark in found[8]:
        offset = delta(mark, source)
        u = sum(a * b for a, b in zip(offset, sx))
        v = sum(a * b for a, b in zip(offset, sy))
        if max(abs(u), abs(v)) <= 3:
            r = target[0] + v * tx[0] + u * ty[0]
            c = target[1] + v * tx[1] + u * ty[1]
            assert 0 <= r < len(grid) and 0 <= c < len(grid[0])
            assert grid[r][c] == 0
            output[r][c] = 8
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--baseline", type=Path)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    root = find_root(__file__)
    generator, source, source_sha = load_selected_generator(TASK, root=root)
    catalog = Catalog(root)
    description = catalog.describe(TASK)
    canonical_rows = [line for line in canonical_path(root).read_bytes().splitlines()
                      if json.loads(line).get("task_id") == TASK]
    report = {"task_id": TASK, "generator_sha256": source_sha,
              "generator_path": source.relative_to(root).as_posix(),
              "version": generator.VERSION, "catalog_rule_hash": description["rule_hash"],
              "canonical_row_sha256": [hashlib.sha256(row).hexdigest() for row in canonical_rows],
              "defaults": [], "passed": False}
    try:
        for difficulty, seed in itertools.product((None, "easy", "medium", "hard"), range(8)):
            grid = generator.generate(seed, 2, difficulty=difficulty)
            assert generator.self_check(grid) == []
            report["defaults"].append({"seed": seed, "sample_index": 2, "difficulty": difficulty,
                                       "grid_sha256": digest(grid)})
        if args.baseline is None:
            pins = {"grid_h": 9, "grid_w": 12, "n_marks": 1}
            grid = generator.generate(17, 3, **pins)
            report["counterexample"] = {"seed": 17, "sample_index": 3, "requested": pins,
                "observed": {"grid_h": len(grid), "grid_w": len(grid[0]),
                             "n_marks": len(positions(grid)[8])}, "input": grid}
            report["passed"] = True
            return

        baseline = json.loads(args.baseline.read_text())
        assert report["defaults"] == baseline["defaults"], "Unpinned seed behavior changed"
        assert report["canonical_row_sha256"] == baseline["canonical_row_sha256"]
        report["baseline_generator_sha256"] = baseline["generator_sha256"]
        report["unchanged_default_samples"] = len(report["defaults"])
        cases, grids = [], []

        def add_case(settings, surface):
            grid = generator.generate(**settings)
            assert generator.self_check(grid) == [], settings
            assert (len(grid), len(grid[0]), len(positions(grid)[8])) == (
                settings["grid_h"], settings["grid_w"], settings["n_marks"]), settings
            expected_output(grid)
            cases.append({"surface": surface, "settings": settings, "input_sha256": digest(grid)})
            grids.append(grid)

        # Surface 1: all corners of the existing three-axis domain, in all bands.
        for h, w, n, difficulty in itertools.product((9, 18), (12, 24), (1, 6),
                                                     (None, "easy", "medium", "hard")):
            add_case({"seed": 17, "sample_index": 3, "difficulty": difficulty,
                      "grid_h": h, "grid_w": w, "n_marks": n}, "axis-domain-corners")
        report["axis_corner_cases"] = len(cases)

        # Surface 2: every source/target orientation pair in the most cramped domain.
        orientations = set()
        for seed in range(1024):
            settings = {"seed": seed, "sample_index": 0, "grid_h": 9, "grid_w": 12, "n_marks": 6}
            grid = generator.generate(**settings)
            found = positions(grid)
            key = tuple(delta(found[arm][0], found[origin][0])
                        for arm, origin in ((3, 2), (4, 2), (6, 5), (7, 5)))
            if key not in orientations:
                orientations.add(key)
                add_case(settings, "cramped-frame-orientations")
            if len(orientations) == 64:
                break
        report["orientation_search_draws"] = seed + 1
        report["orientation_pairs"] = len(orientations)
        assert len(orientations) == 64, "Bounded orientation coverage incomplete"

        # Hand-authored canonical pairs anchor the independent calculation.
        pairs = canonical_pairs(TASK, root=root, labeled_only=True)
        for pair in pairs:
            assert expected_output(pair["input"]) == pair["output"]
            cases.append({"surface": "canonical-example", "split": pair["split"],
                          "pair_index": pair["pair_index"], "input_sha256": digest(pair["input"])})
            grids.append(pair["input"])
        report["canonical_examples"] = len(pairs)
        write(args.out / "cases.json", cases)
        report["racket_cases"] = 0
        report["apply_receipts"] = []
        for start in range(0, len(grids), 64):
            batch = grids[start:start + 64]
            receipt = catalog.apply(TASK, batch, reference="canonical", timeout=120)
            name = f"apply-{start // 64:02d}.json"
            write(args.out / name, receipt)
            report["apply_receipts"].append(name)
            assert receipt["generator_sha256"] == source_sha
            assert receipt["rule_hash_matches_catalog"] is True
            for grid, result in zip(batch, receipt["results"], strict=True):
                assert result["error"] is None, result
                assert result["output"] == expected_output(grid)
            report["racket_cases"] += len(batch)
        report["passed"] = True
    finally:
        report["elapsed_seconds"] = round(time.monotonic() - started, 3)
        write(args.out / "report.json", report)
        print(json.dumps({k: v for k, v in report.items() if k not in ("defaults", "counterexample")}, sort_keys=True))


if __name__ == "__main__":
    main()
