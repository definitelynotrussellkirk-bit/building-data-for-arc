#!/usr/bin/env python3
"""Reproduce the two adversarial audit findings from a full review packet.

The script stages immutable runtime copies of the audited generators, then:
1. measures a largest-object-only transform shortcut for 7a31a33585cc; and
2. checks canonical acceptance plus declared override behavior for ed55b2928ac3.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import importlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
from typing import Any

TARGETS = ("7a31a33585cc", "ed55b2928ac3")


def _module(task_id: str):
    return importlib.import_module(
        f"puzzle_generators.per_puzzle.{task_id}.generator"
    )


def _canonical_rows(path: Path) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for line in path.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") in TARGETS:
            rows[row["task_id"]] = row
    return rows


def _mask_unique_largest(module, panel):
    objects = module._color_objects(panel)
    maximum = max(item["size"] for item in objects)
    largest = [item for item in objects if item["size"] == maximum]
    if len(largest) != 1:
        return None, {"tie": True, "size": maximum, "count": len(largest)}
    color = largest[0]["color"]
    return (
        [[value if value == color else 0 for value in row] for row in panel],
        {"tie": False, "size": maximum, "color": color},
    )


def probe_7a31(module, canonical: dict[str, Any], samples_per_band: int):
    results: dict[str, Any] = {}
    witnesses: list[dict[str, Any]] = []
    for band_index, band in enumerate(("easy", "medium", "hard")):
        counts: Counter[str] = Counter()
        by_profile: defaultdict[str, Counter[str]] = defaultdict(Counter)
        for index in range(samples_per_band):
            seed = 9_100_000 + band_index * 100_000 + index
            sample_index = 17 * index + band_index
            grid = module.generate(seed, sample_index, difficulty=band)
            panels, errors = module._split_panels(grid)
            assert not errors
            a, b, c = panels
            observed = module.observe_overrides(grid)
            profile = observed["component_profile"]
            masked_a, meta = _mask_unique_largest(module, a)
            if meta["tie"]:
                counts["largest_tie"] += 1
                by_profile[profile]["largest_tie"] += 1
                continue
            color = meta["color"]
            masked_b = [[value if value == color else 0 for value in row] for row in b]
            matches = module._matching_transforms(masked_a, masked_b)
            if len(matches) == 1:
                counts["unique_largest_only"] += 1
                by_profile[profile]["unique_largest_only"] += 1
                inferred = matches[0]
                assert inferred == observed["transform"]
                assert module._transform(c, inferred) == module._analysis(grid)["facts"]["output"]
                if len(witnesses) < 6:
                    witnesses.append(
                        {
                            "band": band,
                            "seed": seed,
                            "sample_index": sample_index,
                            "profile": profile,
                            "transform": inferred,
                            "largest_color": color,
                            "largest_size": meta["size"],
                            "objects_per_panel": observed["objects_per_panel"],
                        }
                    )
            elif observed["transform"] in matches:
                counts["ambiguous_largest_only"] += 1
                by_profile[profile]["ambiguous_largest_only"] += 1
            else:
                counts["largest_mismatch"] += 1
                by_profile[profile]["largest_mismatch"] += 1
        results[band] = {
            "samples": samples_per_band,
            "counts": dict(counts),
            "unique_largest_only_rate": counts["unique_largest_only"] / samples_per_band,
            "by_profile": {key: dict(value) for key, value in by_profile.items()},
        }

    canonical_results = []
    pairs = list(canonical.get("train") or [])
    test = canonical.get("test")
    pairs.extend(test if isinstance(test, list) else [test])
    for index, pair in enumerate(pairs):
        panels, errors = module._split_panels(pair["input"])
        assert not errors
        a, b, c = panels
        masked_a, meta = _mask_unique_largest(module, a)
        if meta["tie"]:
            canonical_results.append({"pair": index, "largest_tie": True})
            continue
        color = meta["color"]
        masked_b = [[value if value == color else 0 for value in row] for row in b]
        matches = module._matching_transforms(masked_a, masked_b)
        canonical_results.append(
            {
                "pair": index,
                "largest_color": color,
                "largest_size": meta["size"],
                "matches": matches,
                "exact_output": len(matches) == 1
                and module._transform(c, matches[0]) == pair["output"],
            }
        )
    return {"sample_results": results, "canonical_pairs": canonical_results, "witnesses": witnesses}


def _grid_observation(grid):
    blob = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0 and (row, col) != (0, 0)
    ]
    return {
        "shape": [len(grid), len(grid[0])],
        "key": grid[0][0],
        "blob_size": len(blob),
        "blob_colors": sorted({value for _, _, value in blob}),
    }


def probe_ed55(module, canonical: dict[str, Any]):
    pairs = [(f"train_{index}", item) for index, item in enumerate(canonical.get("train") or [])]
    test = canonical.get("test")
    test_items = test if isinstance(test, list) else [test]
    pairs.extend((f"test_{index}", item) for index, item in enumerate(test_items))
    canonical_checks = [
        {"pair": label, "errors": module.self_check(item["input"])}
        for label, item in pairs
    ]

    override_cases = [
        {"key": 1},
        {"blob_size": 3},
        {"palette_kind": "warm"},
        {"texture": "warm"},
        {"grid_h": 6, "grid_w": 6},
        {"unknown_axis_for_audit": 123},
    ]
    override_results = []
    for overrides in override_cases:
        try:
            grid = module.generate(0, 0, **overrides)
        except Exception as error:  # evidence includes exact rejection text
            override_results.append(
                {
                    "overrides": overrides,
                    "exception": type(error).__name__,
                    "message": str(error),
                }
            )
            continue
        override_results.append(
            {
                "overrides": overrides,
                "observation": _grid_observation(grid),
                "self_check": module.self_check(grid),
            }
        )
    return {"canonical_self_check": canonical_checks, "override_cases": override_results}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--samples-per-band", type=int, default=300)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    root = args.packet_root.resolve()
    sys.path.insert(0, str(root / "repo/src"))
    from arcpuzzles.catalog import Catalog
    from arcpuzzles.runtime import prepare_runtime

    temp = Path(tempfile.mkdtemp(prefix="arcpuzzles-audit-probes-"))
    old_path = list(sys.path)
    try:
        prepare_runtime(Catalog(root / "repo"), temp, task_ids=list(TARGETS))
        sys.path.insert(0, str(temp))
        modules = {task_id: _module(task_id) for task_id in TARGETS}
        rows = _canonical_rows(temp / "data/canonical/puzzles.jsonl")
        payload = {
            "schema": "arcpuzzles-adversarial-audit-evidence-v1",
            "targets": {
                TARGETS[0]: probe_7a31(modules[TARGETS[0]], rows[TARGETS[0]], args.samples_per_band),
                TARGETS[1]: probe_ed55(modules[TARGETS[1]], rows[TARGETS[1]]),
            },
        }
        out = (args.out or root / "checks/audit/audit_probe_results.json").resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2) + "\n")
        print(out)
    finally:
        sys.path[:] = old_path
        shutil.rmtree(temp, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
