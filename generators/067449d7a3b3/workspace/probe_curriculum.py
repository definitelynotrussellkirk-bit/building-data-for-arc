#!/usr/bin/env python3
"""Audit generated four-pair curricula before runner-level uniqueness filtering.

This probe is deliberately source-bound: it imports the selected generator,
materializes every scheduled four-pair window, checks byte-level pair
uniqueness, and rotates each pair through the query position.  It is useful for
catching a subtle failure mode where two scheduled examples are semantically
correct but identical, so the lesson runner silently skips one and changes the
teaching profile.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Iterable, Sequence

WORKSPACE = Path(__file__).resolve().parent
TASK_DIR = WORKSPACE.parent
REPO_ROOT = TASK_DIR.parents[1]
RUNTIME_ROOT = REPO_ROOT / "shared" / "runtime"
for import_root in (REPO_ROOT, RUNTIME_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))


def _load_generator():
    path = TASK_DIR / "generator.py"
    spec = importlib.util.spec_from_file_location(
        "generator_067449d7a3b3_curriculum_probe", path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _pair_signature(pair: dict) -> str:
    payload = json.dumps(pair, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _source_sha256() -> str:
    return hashlib.sha256((TASK_DIR / "generator.py").read_bytes()).hexdigest()


def audit_curriculum(
    *,
    seeds: Iterable[int],
    starts: Iterable[int],
    bands: Sequence[str | None],
) -> dict:
    """Return a JSON-serializable curriculum audit report."""
    gen = _load_generator()
    seed_values = tuple(int(seed) for seed in seeds)
    start_values = tuple(int(start) for start in starts)
    band_values = tuple(bands)
    if not seed_values or not start_values or not band_values:
        raise ValueError("seeds, starts, and bands must all be nonempty")

    failures: list[dict] = []
    windows_checked = 0
    rotations_checked = 0
    duplicate_windows = 0
    profile_histogram: dict[str, int] = {}

    for seed in seed_values:
        for band in band_values:
            band_label = "default" if band is None else str(band)
            for start in start_values:
                windows_checked += 1
                pairs = []
                profiles = []
                for offset in range(4):
                    sample_index = start + offset
                    grid = gen.generate(seed, sample_index, difficulty=band)
                    pair = {"input": grid, "output": gen._mirror(grid)}
                    pairs.append(pair)
                    profile = gen.observe_overrides(grid)["scene_profile"]
                    profiles.append(profile)
                    profile_histogram[profile] = profile_histogram.get(profile, 0) + 1

                signatures = [_pair_signature(pair) for pair in pairs]
                duplicate_groups: dict[str, list[int]] = {}
                for offset, signature in enumerate(signatures):
                    duplicate_groups.setdefault(signature, []).append(start + offset)
                duplicates = [group for group in duplicate_groups.values() if len(group) > 1]
                if duplicates:
                    duplicate_windows += 1
                    failures.append(
                        {
                            "kind": "duplicate_pair",
                            "seed": seed,
                            "band": band_label,
                            "start": start,
                            "profiles": profiles,
                            "duplicate_sample_indices": duplicates,
                        }
                    )

                for query_offset in range(4):
                    rotations_checked += 1
                    demos = [
                        pair for offset, pair in enumerate(pairs) if offset != query_offset
                    ]
                    findings = list(gen.lesson_identifiable(demos, pairs[query_offset]))
                    if findings:
                        failures.append(
                            {
                                "kind": "rotation_not_identifiable",
                                "seed": seed,
                                "band": band_label,
                                "start": start,
                                "query_sample_index": start + query_offset,
                                "profiles": profiles,
                                "findings": findings,
                            }
                        )

    return {
        "task_id": getattr(gen, "TASK_ID", TASK_DIR.name),
        "generator_version": getattr(gen, "VERSION", None),
        "generator_sha256": _source_sha256(),
        "status": "pass" if not failures else "fail",
        "seeds": list(seed_values),
        "starts": list(start_values),
        "bands": ["default" if band is None else str(band) for band in band_values],
        "windows_checked": windows_checked,
        "rotations_checked": rotations_checked,
        "pairs_materialized": windows_checked * 4,
        "duplicate_windows": duplicate_windows,
        "profile_histogram": dict(sorted(profile_histogram.items())),
        "failure_count": len(failures),
        "failures": failures,
    }


def _parse_ints(text: str) -> tuple[int, ...]:
    values = tuple(int(item.strip()) for item in text.split(",") if item.strip())
    if not values:
        raise argparse.ArgumentTypeError("expected at least one comma-separated integer")
    return values


def _parse_range(text: str) -> range:
    pieces = text.split(":")
    try:
        if len(pieces) == 1:
            value = int(pieces[0])
            return range(value, value + 1)
        if len(pieces) in (2, 3):
            args = [int(piece) for piece in pieces]
            return range(*args)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc
    raise argparse.ArgumentTypeError("use N, START:STOP, or START:STOP:STEP")


def _parse_bands(text: str) -> tuple[str | None, ...]:
    valid = {"default": None, "none": None, "easy": "easy", "medium": "medium", "hard": "hard"}
    bands = []
    for raw in text.split(","):
        key = raw.strip().lower()
        if not key:
            continue
        if key not in valid:
            raise argparse.ArgumentTypeError(f"unknown band {raw!r}")
        bands.append(valid[key])
    if not bands:
        raise argparse.ArgumentTypeError("expected at least one band")
    return tuple(bands)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--seeds",
        type=_parse_ints,
        default=(6007, 198222630054986, 20261007),
        help="comma-separated integer seeds",
    )
    parser.add_argument(
        "--starts",
        type=_parse_range,
        default=range(32),
        help="N, START:STOP, or START:STOP:STEP",
    )
    parser.add_argument(
        "--bands",
        type=_parse_bands,
        default=("easy", "medium", "hard"),
        help="comma-separated default,easy,medium,hard",
    )
    parser.add_argument("--out", type=Path, help="write the JSON report to this path")
    args = parser.parse_args(argv)

    report = audit_curriculum(seeds=args.seeds, starts=args.starts, bands=args.bands)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
