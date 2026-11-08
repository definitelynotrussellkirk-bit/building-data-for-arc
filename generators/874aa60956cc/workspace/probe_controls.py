#!/usr/bin/env python3
"""Exhaust the five declared integer controls for task 874aa60956cc.

From an extracted packet's WORK directory::

    .venv-review/bin/python -B repo/generators/874aa60956cc/workspace/probe_controls.py \
        --seed 20261008 --sample-index 3 --out checks/controls-cartesian.json

The fixed domain has 4,704 combinations per band, or 14,112 across all three
bands. Dimensions and color multiplicities are counted directly from pixels,
independently of the generator's observe_overrides function. This is a finite
structural-control check at one seed/index, not a Racket-label or lesson test.
The source layout is found from this file, so execution does not depend on cwd.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import importlib.util
import itertools
import json
import math
from pathlib import Path
import sys
import time


TASK_ID = "874aa60956cc"
BANDS = ("easy", "medium", "hard")
DOMAINS = {
    "grid_h": tuple(range(5, 19)),
    "grid_w": tuple(range(5, 19)),
    "rectangles": tuple(range(1, 7)),
    "singletons": (0, 1),
    "triples": (0, 1),
}


def _bootstrap_support():
    for ancestor in Path(__file__).resolve().parents:
        for relative in ("reviewer_support.py", "shared/runtime/reviewer_support.py"):
            candidate = ancestor / relative
            if candidate.is_file():
                sys.path.insert(0, str(candidate.parent))
                return candidate
    raise RuntimeError("Cannot find reviewer_support.py in this file's library/runtime tree")


SUPPORT_PATH = _bootstrap_support()
from reviewer_support import find_root  # noqa: E402


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _generator_path(root):
    for relative in (
        f"generators/{TASK_ID}/generator.py",
        f"puzzle_generators/per_puzzle/{TASK_ID}/generator.py",
    ):
        candidate = root / relative
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"Cannot find selected generator {TASK_ID} beneath {root}")


def _load_generator(path):
    name = f"controls_probe_{TASK_ID}"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _observe_pixels(grid):
    """Measure the controls without invoking any generator observer/helper."""
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("Expected a nonempty grid")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("Expected a nonempty first row")
    width = len(grid[0])
    positions = defaultdict(list)
    for r, row in enumerate(grid):
        if not isinstance(row, (list, tuple)) or len(row) != width:
            raise ValueError(f"Ragged or malformed row {r}")
        for c, color in enumerate(row):
            if type(color) is not int or not 0 <= color <= 9:
                raise ValueError(f"Non-ARC cell at ({r}, {c}): {color!r}")
            if color != 0:
                positions[color].append((r, c))
    multiplicities = Counter(len(cells) for cells in positions.values())
    unexpected = sorted(n for n in multiplicities if n not in (1, 2, 3))
    if unexpected:
        raise ValueError(f"Unexpected nonzero-color multiplicities: {unexpected}")
    for color, cells in positions.items():
        if len(cells) == 2:
            (r0, c0), (r1, c1) = cells
            if r0 == r1 or c0 == c1:
                raise ValueError(f"Color {color} has collinear corners")
    return {
        "grid_h": len(grid),
        "grid_w": width,
        "rectangles": multiplicities[2],
        "singletons": multiplicities[1],
        "triples": multiplicities[3],
    }


def _run(args):
    started = datetime.now(timezone.utc).isoformat()
    timer = time.monotonic()
    root = find_root(__file__)
    generator_path = _generator_path(root)
    tracked = [Path(__file__).resolve(), generator_path, SUPPORT_PATH]
    for relative in ("puzzle_generators/base.py", "puzzle_generators/helpers/grid.py"):
        candidate = SUPPORT_PATH.parent / relative
        if candidate.is_file():
            tracked.append(candidate)
    before = {str(path): _sha256(path) for path in tracked}
    expected_per_band = math.prod(len(values) for values in DOMAINS.values())
    report = {
        "schema": "874aa60956cc-controls-cartesian-v1",
        "task_id": TASK_ID,
        "status": "running",
        "source": {
            "root": str(root),
            "generator_path": str(generator_path),
            "generator_sha256": before[str(generator_path)],
            "probe_path": str(Path(__file__).resolve()),
            "probe_sha256": before[str(Path(__file__).resolve())],
            "tracked_files_sha256": before,
        },
        "verification_command": {
            "cwd": str(Path.cwd().resolve()),
            "argv": list(sys.orig_argv),
            "python_executable": sys.executable,
            "python_version": sys.version,
            "exit_code": None,
        },
        "settings": {
            "seed": args.seed,
            "sample_index": args.sample_index,
            "bands": list(BANDS),
            "domains": {name: list(values) for name, values in DOMAINS.items()},
            "expected_cases_per_band": expected_per_band,
            "expected_total_cases": expected_per_band * len(BANDS),
        },
        "checks": [
            "Independent rectangular dimensions and integer ARC cell values",
            "Independent nonzero-color multiplicities equal all five requested controls",
            "Every paired color has distinct corner rows and columns",
            "Generator self_check returns no errors",
            "Tracked source bytes remain unchanged during the run",
        ],
        "limits": [
            "Exhausts the declared control Cartesian product at one explicit seed and sample index.",
            "Explicit overrides bypass the generator's default teaching-witness filter.",
            "Does not enumerate every lawful pixel layout, all seeds, or lesson assemblies.",
            "Does not execute Racket or verify output labels.",
            "Successful case rows are omitted; settings retain the complete replayable case matrix.",
        ],
        "per_band": {},
        "failures": [],
        "source_changes": [],
        "started_at": started,
    }
    generator = _load_generator(generator_path)
    for band in BANDS:
        stats = {"cases": 0, "passed": 0, "failed": 0}
        for values in itertools.product(*DOMAINS.values()):
            controls = dict(zip(DOMAINS, values))
            stats["cases"] += 1
            failure = None
            try:
                grid = generator.generate(args.seed, args.sample_index,
                                          difficulty=band, **controls)
                observed = _observe_pixels(grid)
                validation_errors = generator.self_check(grid)
                if observed != controls or validation_errors:
                    failure = {"observed": observed,
                               "self_check_errors": validation_errors}
            except Exception as exc:
                failure = {"error": f"{type(exc).__name__}: {exc}"}
            if failure is None:
                stats["passed"] += 1
            else:
                stats["failed"] += 1
                report["failures"].append({"band": band, "controls": controls,
                                           **failure})
        report["per_band"][band] = stats
    for path, digest in before.items():
        after = _sha256(path)
        if after != digest:
            report["source_changes"].append({"path": path, "before": digest, "after": after})
    report["counts"] = {
        key: sum(stats[key] for stats in report["per_band"].values())
        for key in ("cases", "passed", "failed")
    }
    report["source_unchanged"] = not report["source_changes"]
    report["status"] = ("passed" if not report["failures"] and report["source_unchanged"]
                        else "failed")
    exit_code = 0 if report["status"] == "passed" else 1
    report["verification_command"]["exit_code"] = exit_code
    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    report["duration_seconds"] = time.monotonic() - timer
    return report, exit_code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20261008)
    parser.add_argument("--sample-index", type=int, default=3)
    parser.add_argument("--out", type=Path, required=True,
                        help="New JSON report path; existing files are refused")
    args = parser.parse_args()
    if args.sample_index < 0:
        parser.error("--sample-index must be nonnegative")
    if args.out.exists():
        parser.error(f"Output already exists: {args.out}")
    report, exit_code = _run(args)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps({"status": report["status"], "counts": report["counts"],
                      "generator_sha256": report["source"]["generator_sha256"],
                      "probe_sha256": report["source"]["probe_sha256"],
                      "source_unchanged": report["source_unchanged"],
                      "exit_code": exit_code, "out": str(args.out.resolve())},
                     sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
