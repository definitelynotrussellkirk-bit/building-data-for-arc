#!/usr/bin/env python3
"""Source-bound distribution and semantic coverage probe for ba9d8eb0cd5a.

Run through packet ``run_with_racket.py`` so shared runtime dependencies and
canonical data are pinned while this script loads the selected source file. The
report is intentionally small and reproducible;
it records replay coordinates for every failure and aggregate coverage for
canonical-scale profiles and the declared sort-then-pack rival.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root


def _load_generator():
    path = Path(__file__).resolve().parents[1] / "generator.py"
    spec = importlib.util.spec_from_file_location("ba9d8eb0cd5a_generator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


BANDS = ("easy", "medium", "hard")


def profile(grid: list[list[int]]) -> tuple[int, int, int]:
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def stable_hash(grid: list[list[int]]) -> str:
    raw = json.dumps(grid, separators=(",", ":"), sort_keys=False).encode()
    return hashlib.sha256(raw).hexdigest()[:16]


def pack_rows(grid: list[list[int]]) -> list[list[int]]:
    result = []
    for row in grid:
        values = [value for value in row if value != 0]
        result.append(values + [0] * (len(row) - len(values)))
    return result


def run(per_band: int) -> dict[str, object]:
    canonical_profiles = sorted({profile(pair["input"]) for pair in canonical_pairs(gen.TASK_ID, root=find_root(__file__))})
    report: dict[str, object] = {
        "schema": "ba9d8eb0cd5a_coverage_probe/1",
        "task_id": gen.TASK_ID,
        "generator_version": gen.VERSION,
        "rule_hash": gen.RULE_HASH,
        "per_band": per_band,
        "canonical_profiles": [list(item) for item in canonical_profiles],
        "bands": {},
        "failures": [],
    }
    failures: list[dict[str, object]] = report["failures"]  # type: ignore[assignment]

    for band_index, band in enumerate(BANDS):
        shapes: set[tuple[int, int]] = set()
        profiles: set[tuple[int, int, int]] = set()
        color_counts: set[int] = set()
        hashes: set[str] = set()
        canonical_hits = 0
        witness_hits = 0
        rival_disagreements = 0

        for index in range(per_band):
            seed = 50_000 + band_index * 10_000 + index
            sample_index = index * 19 + 7
            try:
                grid = gen.generate(seed, sample_index, difficulty=band)
                errors = gen.self_check(grid, difficulty=band)
                if errors:
                    raise AssertionError(f"self_check: {errors}")
                observed = gen.observe_overrides(grid)
                if observed != {
                    "grid_h": len(grid),
                    "grid_w": len(grid[0]),
                    "n_colors": len({v for row in grid for v in row if v}),
                }:
                    raise AssertionError(f"observer mismatch: {observed}")
                oracle = pack_rows(grid)
                if oracle == grid:
                    raise AssertionError("rule has no visible effect")
                witness = bool(gen.SEMANTIC_WITNESSES["order_preservation"](grid))
                rival = gen.SEMANTIC_RIVALS["sort_then_pack"](grid)
                if witness:
                    witness_hits += 1
                if rival != oracle:
                    rival_disagreements += 1
                current_profile = profile(grid)
                if current_profile in canonical_profiles:
                    canonical_hits += 1
                shapes.add((len(grid), len(grid[0])))
                profiles.add(current_profile)
                color_counts.add(observed["n_colors"])
                hashes.add(stable_hash(grid))
            except Exception as exc:  # report replay coordinates instead of hiding a sample
                failures.append(
                    {
                        "band": band,
                        "seed": seed,
                        "sample_index": sample_index,
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )

        report["bands"][band] = {  # type: ignore[index]
            "draws": per_band,
            "unique_inputs": len(hashes),
            "unique_shapes": len(shapes),
            "shape_values": [list(item) for item in sorted(shapes)],
            "unique_profiles": len(profiles),
            "n_colors_values": sorted(color_counts),
            "canonical_profile_hits": canonical_hits,
            "order_witness_hits": witness_hits,
            "sort_rival_disagreements": rival_disagreements,
        }

    report["passed"] = not failures and all(
        stats["canonical_profile_hits"] > 0
        and stats["order_witness_hits"] == per_band
        and stats["sort_rival_disagreements"] == per_band
        and stats["unique_inputs"] == per_band
        for stats in report["bands"].values()  # type: ignore[union-attr]
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-band", type=int, default=100)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.per_band < 1:
        parser.error("--per-band must be positive")
    report = run(args.per_band)
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload)
    print(payload, end="")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
