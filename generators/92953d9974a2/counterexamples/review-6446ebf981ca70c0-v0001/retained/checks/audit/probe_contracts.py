#!/usr/bin/env python3
"""Source-bound adversarial probes for the two assigned audit targets."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

from reviewer_support import canonical_pairs, find_root, load_selected_generator

HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)


def dump(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def grid_nz(grid):
    return sum(value != 0 for row in grid for value in row)


def probe_da() -> dict:
    task = "da776131ac9a"
    mod, source, source_hash = load_selected_generator(task, root=ROOT)
    overrides = {
        "grid_n": 3,
        "nz": 1,
        "palette_size": 1,
        "palette_kind": "small",
        "cell_layout": "scattered",
        "position_bias": "spread",
        "anchor_corner": True,
    }
    witness = None
    for seed in range(256):
        grid = mod.generate(seed, 0, difficulty="medium", **overrides)
        if grid_nz(grid) != overrides["nz"]:
            base_overrides = dict(overrides)
            base_overrides["anchor_corner"] = False
            unanchored = mod.generate(seed, 0, difficulty="medium", **base_overrides)
            witness = {
                "seed": seed,
                "sample_index": 0,
                "difficulty": "medium",
                "overrides": overrides,
                "generator_source": str(source.relative_to(ROOT)),
                "generator_sha256": source_hash,
                "generated_grid": grid,
                "generated_nz": grid_nz(grid),
                "requested_nz": overrides["nz"],
                "unanchored_grid_same_draw": unanchored,
                "unanchored_nz": grid_nz(unanchored),
                "self_check": mod.self_check(grid, difficulty="medium", meta=None),
            }
            break
    if witness is None:
        raise AssertionError("No anchor_corner/nz mismatch found in seeds 0..255")

    # A contract-respecting realization of nz=1 + anchor_corner=True must use the
    # sole nonzero at the anchor, rather than adding the anchor after selection.
    color = witness["generated_grid"][0][0]
    expected_grid = [[0] * 3 for _ in range(3)]
    expected_grid[0][0] = color
    witness["contract_respecting_grid"] = expected_grid
    witness["contract_respecting_nz"] = grid_nz(expected_grid)
    witness["canonical_pair_count"] = len(canonical_pairs(task, root=ROOT, labeled_only=True))

    out_dir = HERE / task
    dump(out_dir / "probe.json", witness)
    dump(out_dir / "input.json", witness["generated_grid"])
    dump(out_dir / "contract_respecting_input.json", expected_grid)
    return witness


def probe_929() -> dict:
    task = "92953d9974a2"
    mod, source, source_hash = load_selected_generator(task, root=ROOT)
    counts = {}
    failures = []
    witness = None
    samples_per_band = 200
    for difficulty in ("easy", "medium", "hard"):
        counter = Counter()
        accepted = 0
        for seed in range(samples_per_band):
            try:
                grid = mod.generate(seed, 0, difficulty=difficulty)
            except Exception as exc:  # retained honestly in the report
                failures.append({"difficulty": difficulty, "seed": seed, "error": repr(exc)})
                continue
            accepted += 1
            code = grid[-1][0]
            counter[str(code)] += 1
            if witness is None and code == 0:
                witness = {
                    "seed": seed,
                    "sample_index": 0,
                    "difficulty": difficulty,
                    "input": grid,
                    "bottom_left_code": code,
                    "self_check": mod.self_check(grid, difficulty=difficulty, meta=None),
                }
        counts[difficulty] = {
            "requested": samples_per_band,
            "materialized": accepted,
            "bottom_left_code_counts": dict(sorted(counter.items(), key=lambda kv: int(kv[0]))),
        }
    if witness is None:
        raise AssertionError("No code=0 witness found")

    canonical = canonical_pairs(task, root=ROOT, labeled_only=True)
    canonical_codes = [row["input"][-1][0] for row in canonical]
    report = {
        "task_id": task,
        "generator_source": str(source.relative_to(ROOT)),
        "generator_sha256": source_hash,
        "sample_policy": {
            "difficulties": ["easy", "medium", "hard"],
            "seed_range_each": [0, samples_per_band - 1],
            "sample_index": 0,
            "total_requested": 3 * samples_per_band,
        },
        "counts": counts,
        "generation_failures": failures,
        "canonical_bottom_left_codes": canonical_codes,
        "source_domain_observation": (
            "The normal-path color pool is [2,3,4,5,6,7,8,9] and the grid "
            "background is 0, so bottom-left code 1 is unreachable by construction."
        ),
        "witness": witness,
    }
    out_dir = HERE / task
    dump(out_dir / "census.json", report)
    dump(out_dir / "input.json", witness["input"])
    return report


def main() -> None:
    da = probe_da()
    nine = probe_929()
    summary = {
        "schema": "arcpuzzles-assigned-audit-probes-v1",
        "probe_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "da776131ac9a": {
            "generator_sha256": da["generator_sha256"],
            "seed": da["seed"],
            "requested_nz": da["requested_nz"],
            "generated_nz": da["generated_nz"],
        },
        "92953d9974a2": {
            "generator_sha256": nine["generator_sha256"],
            "total_requested": nine["sample_policy"]["total_requested"],
            "generation_failures": len(nine["generation_failures"]),
            "canonical_codes": nine["canonical_bottom_left_codes"],
            "generated_code_1_count": sum(
                row["bottom_left_code_counts"].get("1", 0)
                for row in nine["counts"].values()
            ),
        },
    }
    dump(HERE / "summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
