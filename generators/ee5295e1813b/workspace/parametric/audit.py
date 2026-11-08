"""Bounded source-local audit for the diamond-center relay family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load_family():
    path = HERE / "family.py"
    spec = importlib.util.spec_from_file_location("_audit_center_relay_family", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _aligned_equal_pairs(anchors: list[tuple[int, int, int]]) -> int:
    return sum(
        1
        for index, first in enumerate(anchors)
        for second in anchors[index + 1 :]
        if first[2] == second[2]
        and (first[0] == second[0] or first[1] == second[1])
        and (first[0], first[1]) != (second[0], second[1])
    )


def run() -> dict:
    family = _load_family()
    settings = (
        {"composition": "fill_centers"},
        {"composition": "connect_equal_centers"},
    )
    episodes = 0
    pairs = 0
    wrong_intermediate_disagreements = 0
    center_colors: set[int] = set()
    sizes: set[tuple[int, int]] = set()
    max_nonzero = 0
    min_anchor_count: int | None = None
    max_anchor_count = 0
    min_aligned_pairs: int | None = None
    max_aligned_pairs = 0

    for seed in range(12):
        baseline = family.generate(seed, settings[0], 6, 4)
        alternate = family.generate(seed, settings[1], 6, 4)
        baseline_inputs = [
            pair["input"] for split in ("train", "test") for pair in baseline[split]
        ]
        alternate_inputs = [
            pair["input"] for split in ("train", "test") for pair in alternate[split]
        ]
        assert baseline_inputs == alternate_inputs

        for demos in range(2, 7):
            for queries in range(1, 5):
                generated = [
                    family.generate(seed, setting, demos, queries)
                    for setting in settings
                ]
                episodes += len(generated)
                assert generated[0]["train"] == baseline["train"][:demos]
                assert generated[0]["test"] == baseline["test"][:queries]
                assert generated[1]["train"] == alternate["train"][:demos]
                assert generated[1]["test"] == alternate["test"][:queries]
                left_inputs = [
                    pair["input"]
                    for split in ("train", "test")
                    for pair in generated[0][split]
                ]
                right_inputs = [
                    pair["input"]
                    for split in ("train", "test")
                    for pair in generated[1][split]
                ]
                assert left_inputs == right_inputs
                assert len(
                    {json.dumps(grid, separators=(",", ":")) for grid in left_inputs}
                ) == demos + queries

        for split in ("train", "test"):
            for plain_pair, connected_pair in zip(baseline[split], alternate[split]):
                grid = plain_pair["input"]
                anchors = family.center_intermediate(grid)
                aligned_pairs = _aligned_equal_pairs(anchors)
                assert anchors
                assert aligned_pairs >= 1
                assert plain_pair["output"] == family.transform(grid, "fill_centers")
                assert connected_pair["output"] == family.transform(
                    grid, "connect_equal_centers"
                )
                assert plain_pair["output"] != connected_pair["output"]
                wrong = family.transform_wrong_intermediate(grid)
                if wrong != connected_pair["output"]:
                    wrong_intermediate_disagreements += 1
                center_colors.update(color for _, _, color in anchors)
                sizes.add((len(grid), len(grid[0])))
                max_nonzero = max(
                    max_nonzero,
                    sum(cell != 0 for row in grid for cell in row),
                )
                min_anchor_count = (
                    len(anchors)
                    if min_anchor_count is None
                    else min(min_anchor_count, len(anchors))
                )
                max_anchor_count = max(max_anchor_count, len(anchors))
                min_aligned_pairs = (
                    aligned_pairs
                    if min_aligned_pairs is None
                    else min(min_aligned_pairs, aligned_pairs)
                )
                max_aligned_pairs = max(max_aligned_pairs, aligned_pairs)
                pairs += 1

    assert center_colors == set(range(1, 10))
    assert wrong_intermediate_disagreements == pairs
    assert (30, 30) in sizes and max_nonzero >= 70
    assert min_anchor_count is not None and min_anchor_count >= 3
    assert min_aligned_pairs is not None and min_aligned_pairs >= 1
    sources = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(HERE.iterdir())
        if path.is_file() and path.suffix in {".py", ".rkt", ".json"}
    }
    return {
        "schema": "arcpuzzles-parametric-self-audit-v1",
        "task_id": family.TASK_ID,
        "status": "passed",
        "seeds": 12,
        "episodes_checked": episodes,
        "pairs_checked": pairs,
        "supported_counts": {"demos": [2, 6], "queries": [1, 4]},
        "setting_independent_inputs": True,
        "prefix_stable_streams": True,
        "all_pairs_distinguish_settings": True,
        "wrong_intermediate_disagreements": wrong_intermediate_disagreements,
        "center_colors_seen": sorted(center_colors),
        "anchor_count_range": [min_anchor_count, max_anchor_count],
        "aligned_equal_pair_count_range": [min_aligned_pairs, max_aligned_pairs],
        "sizes_seen": [list(size) for size in sorted(sizes)],
        "max_input_nonzero_cells": max_nonzero,
        "limits": (
            "Finite deterministic audit; protected Racket parity is established "
            "separately by authoring preflight."
        ),
        "sources": sources,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = run()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {key: report[key] for key in ("status", "episodes_checked", "pairs_checked")}
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
