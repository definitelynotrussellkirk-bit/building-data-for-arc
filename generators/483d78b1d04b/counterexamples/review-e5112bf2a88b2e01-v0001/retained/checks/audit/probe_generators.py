#!/usr/bin/env python3
"""Source-bound adversarial audit probes for the two assigned generators."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2] / "repo"
CANONICAL = REPO / "shared/data/canonical/puzzles.jsonl"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def canonical_row(task_id: str) -> dict[str, Any]:
    with CANONICAL.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == task_id:
                return row
    raise KeyError(task_id)


def pair_features(grid: list[list[int]]) -> dict[str, int]:
    by_color: dict[int, list[tuple[int, int]]] = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                by_color.setdefault(value, []).append((r, c))
    out = {
        "horizontal_clear": 0,
        "horizontal_blocked": 0,
        "vertical_clear": 0,
        "vertical_blocked": 0,
        "unaligned_pairs": 0,
        "singleton_colors": 0,
        "colors_over_two": 0,
    }
    for points in by_color.values():
        if len(points) == 1:
            out["singleton_colors"] += 1
            continue
        if len(points) > 2:
            out["colors_over_two"] += 1
            continue
        (r1, c1), (r2, c2) = points
        if r1 == r2:
            blocked = any(grid[r1][c] != 0 for c in range(min(c1, c2) + 1, max(c1, c2)))
            out[f"horizontal_{'blocked' if blocked else 'clear'}"] += 1
        elif c1 == c2:
            blocked = any(grid[r][c1] != 0 for r in range(min(r1, r2) + 1, max(r1, r2)))
            out[f"vertical_{'blocked' if blocked else 'clear'}"] += 1
        else:
            out["unaligned_pairs"] += 1
    return out


def sum_features(acc: dict[str, int], row: dict[str, int]) -> None:
    for key, value in row.items():
        acc[key] = acc.get(key, 0) + value


def probe_483() -> dict[str, Any]:
    task_id = "483d78b1d04b"
    gen, path = load(task_id)
    comparisons = {
        "anchor_inset_false_vs_true": 0,
        "marker_offset_tight_vs_loose": 0,
        "asymmetry_force_false_vs_true": 0,
    }
    total = 0
    witnesses = []
    for band in ("easy", "medium", "hard"):
        for seed in range(40):
            index = seed % 7
            base = gen.generate(10000 + seed, index, difficulty=band)
            variants = {
                "anchor_inset_false_vs_true": (
                    gen.generate(10000 + seed, index, difficulty=band, anchor_inset=False),
                    gen.generate(10000 + seed, index, difficulty=band, anchor_inset=True),
                ),
                "marker_offset_tight_vs_loose": (
                    gen.generate(10000 + seed, index, difficulty=band, marker_offset_kind="tight"),
                    gen.generate(10000 + seed, index, difficulty=band, marker_offset_kind="loose"),
                ),
                "asymmetry_force_false_vs_true": (
                    gen.generate(10000 + seed, index, difficulty=band, asymmetry_force=False),
                    gen.generate(10000 + seed, index, difficulty=band, asymmetry_force=True),
                ),
            }
            for name, (left, right) in variants.items():
                comparisons[name] += int(left == right)
            if len(witnesses) < 2:
                witnesses.append({
                    "difficulty": band,
                    "seed": 10000 + seed,
                    "sample_index": index,
                    "base_equals_anchor_inset_true": base == variants["anchor_inset_false_vs_true"][1],
                    "grid": base,
                })
            total += 1
    return {
        "task_id": task_id,
        "generator_sha256": sha256(path),
        "draws_per_comparison": total,
        "identical_output_counts": comparisons,
        "advertised_axes": {
            key: gen.AXES[key] for key in ("anchor_inset", "marker_offset_kind", "asymmetry_force")
        },
        "witnesses": witnesses,
        "finding": "three advertised exact controls are output-inert across every sampled replay",
    }


def probe_80() -> dict[str, Any]:
    task_id = "80bd3177b03c"
    gen, path = load(task_id)
    generated = {key: 0 for key in pair_features([[0]]).keys()}
    invalid = 0
    inputs = 0
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for index in range(200):
            grid = gen.generate(20000 + band_index * 1000 + index, index, difficulty=band)
            sum_features(generated, pair_features(grid))
            invalid += int(bool(gen.self_check(grid)))
            inputs += 1

    canonical = {key: 0 for key in generated}
    row = canonical_row(task_id)
    canonical_inputs = [pair["input"] for split in ("train", "test") for pair in row[split]]
    for grid in canonical_inputs:
        sum_features(canonical, pair_features(grid))

    return {
        "task_id": task_id,
        "generator_sha256": sha256(path),
        "generated_inputs": inputs,
        "generated_self_check_failures": invalid,
        "generated_feature_counts": generated,
        "canonical_input_count": len(canonical_inputs),
        "canonical_feature_counts": canonical,
        "finding": (
            "the sampler exercises only clear horizontal pairs, although the authority/canonical "
            "family includes vertical pairs, blocked pairs, singletons, and colors occurring more than twice"
        ),
    }


def main() -> int:
    report = {
        "schema": "arcpuzzles-two-target-audit-probe-v1",
        "canonical_sha256": sha256(CANONICAL),
        "targets": [probe_483(), probe_80()],
    }
    out = Path(__file__).with_name("audit_probe_report.json")
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
