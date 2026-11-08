#!/usr/bin/env python3
"""Check task-local distribution and teaching contracts without reading labels.

This source-bound probe uses generator inputs only.  It detects exact replay of a
same seed/sample across difficulty bands, verifies that every ordinary object is
initially off-center, and checks that each four-sample first-frame-key window
covers keys 2, 3, 4, and 5.  A zero exit is finite sampled evidence for these
three declared contracts, not a general diversity or learnability guarantee.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

TASK_ID = "f2dbde875127"
HOME = Path(__file__).resolve().parents[1]
WORKSPACE = Path(__file__).resolve().parent
REPO = HOME.parents[1]
RUNTIME = REPO / "shared/runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))
BANDS = ("easy", "medium", "hard")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _is_centered(record: dict) -> bool:
    r0, c0, r1, c1 = record["box"]
    points = record["points"]
    lo_r = min(r for r, _ in points)
    lo_c = min(c for _, c in points)
    obj_h = max(r for r, _ in points) - lo_r + 1
    obj_w = max(c for _, c in points) - lo_c + 1
    interior_h = r1 - r0 - 1
    interior_w = c1 - c0 - 1
    target = (r0 + 1 + (interior_h - obj_h) // 2,
              c0 + 1 + (interior_w - obj_w) // 2)
    return (lo_r, lo_c) == target


def analyze(*, start_seed: int, count: int, sample_index: int,
            generator_path: Path | None = None) -> dict:
    if start_seed < 0 or sample_index < 0 or count < 1:
        raise ValueError("start_seed/sample_index must be nonnegative and count positive")
    source_path = (HOME / "generator.py" if generator_path is None else Path(generator_path)).resolve()
    if not source_path.is_file():
        raise ValueError(f"generator source does not exist: {source_path}")
    source_hash_before = _sha(source_path)
    generator = _load("distribution_contract_generator", source_path)
    key_probe = _load("distribution_contract_key_probe", WORKSPACE / "key_contrast_probe.py")

    duplicate_seeds: list[dict] = []
    off_center_violations: list[dict] = []
    failed_windows: list[dict] = []
    all_hashes: set[str] = set()
    generated_grid_count = 0

    for seed in range(start_seed, start_seed + count):
        by_band: dict[str, str] = {}
        for band in BANDS:
            grid = generator.generate(seed, sample_index, difficulty=band)
            digest = _canonical_hash(grid)
            all_hashes.add(digest)
            by_band[band] = digest
            generated_grid_count += 1
            for frame_index, record in enumerate(key_probe.frame_records(grid)):
                if _is_centered(record):
                    off_center_violations.append({
                        "seed": seed,
                        "sample_index": sample_index,
                        "difficulty": band,
                        "frame_index": frame_index,
                        "box": record["box"],
                        "key_cell": record["key_cell"],
                    })

            keys = []
            for offset in range(4):
                window_grid = generator.generate(
                    seed, sample_index + offset, difficulty=band
                )
                keys.append(key_probe.frame_records(window_grid)[0]["key_cell"][2])
            if set(keys) != {2, 3, 4, 5}:
                failed_windows.append({
                    "seed": seed,
                    "difficulty": band,
                    "sample_index_first": sample_index,
                    "keys": keys,
                })

        groups: dict[str, list[str]] = {}
        for band, digest in by_band.items():
            groups.setdefault(digest, []).append(band)
        collisions = [bands for bands in groups.values() if len(bands) > 1]
        if collisions:
            duplicate_seeds.append({
                "seed": seed,
                "sample_index": sample_index,
                "duplicate_band_groups": collisions,
                "hashes": by_band,
            })

    source_hash_after = _sha(source_path)
    source_bound = (
        source_hash_before == source_hash_after
        and Path(generator.__file__).resolve() == source_path.resolve()
    )
    passed = source_bound and not duplicate_seeds and not off_center_violations and not failed_windows
    return {
        "schema": "distribution-contract-probe-v1",
        "task_id": TASK_ID,
        "generator_sha256": source_hash_after,
        "source_path": str(source_path),
        "probe_sha256": _sha(Path(__file__)),
        "sampling": {
            "seed_first": start_seed,
            "seed_last": start_seed + count - 1,
            "seed_count": count,
            "sample_index": sample_index,
            "difficulties": list(BANDS),
            "key_window_length": 4,
        },
        "counts": {
            "generated_primary_grids": generated_grid_count,
            "unique_primary_grids": len(all_hashes),
            "cross_band_duplicate_seed_count": len(duplicate_seeds),
            "off_center_violations": len(off_center_violations),
            "four_sample_key_windows_checked": count * len(BANDS),
            "four_sample_key_windows_failed": len(failed_windows),
        },
        "cross_band_duplicate_seeds": duplicate_seeds,
        "off_center_violation_examples": off_center_violations[:20],
        "failed_key_windows": failed_windows[:20],
        "source_bound": source_bound,
        "labels_or_query_answers_read": False,
        "passed": passed,
        "limitation": "finite input-only sample; exact replay, pose, and declared key-coverage contracts only",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-seed", type=int, default=0)
    parser.add_argument("--count", type=int, default=256)
    parser.add_argument("--sample-index", type=int, default=0)
    parser.add_argument("--generator", type=Path, default=HOME / "generator.py",
                        help="generator source or retained snapshot to probe")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        report = analyze(
            start_seed=args.start_seed,
            count=args.count,
            sample_index=args.sample_index,
            generator_path=args.generator,
        )
    except ValueError as exc:
        parser.error(str(exc))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({
        "generator_sha256": report["generator_sha256"],
        "sampling": report["sampling"],
        "counts": report["counts"],
        "source_bound": report["source_bound"],
        "passed": report["passed"],
    }, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
