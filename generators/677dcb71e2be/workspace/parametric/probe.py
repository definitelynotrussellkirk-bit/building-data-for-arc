#!/usr/bin/env python3
"""Bounded adversarial audit for the 677dcb71e2be base and parametric family.

Run from the selected repository through the packet launcher:
    python3 review.py run python3 generators/677dcb71e2be/workspace/parametric/probe.py

The probe is deliberately source-local and reusable by later reviewers.  It
attacks the two retained base-generator shortcuts, the parametric family's
minimum lesson, input-dependent intermediate, count/type boundaries, query
prefix, and 30x30 support.  It is finite evidence, not a uniqueness proof.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import importlib.util
import json
from pathlib import Path
from typing import Any

from reviewer_support import find_root, load_selected_generator


TASK_ID = "677dcb71e2be"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID / "workspace" / "parametric"
REPORT = HOME / "evidence" / "probe-report.json"


def _load_adapter():
    path = HOME / "adapter.py"
    spec = importlib.util.spec_from_file_location("probe_adapter_677dcb71e2be", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _paint(grid: list[list[int]], cells: list[tuple[int, int]], color: int) -> None:
    for row, col in cells:
        if grid[row][col] != 0:
            raise AssertionError("controlled scene overlap")
        grid[row][col] = color


def _crossed_scenes() -> dict[str, list[list[int]]]:
    """Return same-dimension causal and nuisance controls.

    `offset_1` and `offset_2` keep dimensions, component anchors, colors and
    interior components fixed while changing the border selector from four to
    five occupied cells.  `offset_2_nuisance` keeps the five-cell intermediate
    but changes border side/shape, colors, and interior positions.
    """
    offset_1 = [[0] * 15 for _ in range(14)]
    _paint(offset_1, [(0, 5), (0, 6), (1, 5), (1, 6)], 4)
    _paint(offset_1, [(5, 2), (5, 3), (5, 4), (6, 2), (6, 3), (7, 2), (7, 3)], 8)
    _paint(offset_1, [(9, 10), (10, 10), (10, 11)], 2)

    offset_2 = [[0] * 15 for _ in range(14)]
    _paint(offset_2, [(0, 5), (0, 6), (1, 5), (1, 6), (2, 5)], 4)
    _paint(offset_2, [(5, 2), (5, 3), (5, 4), (6, 2), (6, 3), (7, 2), (7, 3)], 8)
    _paint(offset_2, [(9, 10), (10, 10), (10, 11)], 2)

    offset_2_nuisance = [[0] * 15 for _ in range(14)]
    _paint(offset_2_nuisance, [(4, 14), (5, 14), (6, 14), (6, 13), (7, 13)], 7)
    _paint(offset_2_nuisance, [(2, 2), (2, 3), (3, 2), (3, 3), (4, 2), (4, 3), (5, 2)], 1)
    _paint(offset_2_nuisance, [(10, 6), (10, 7), (11, 6)], 9)
    return {
        "offset_1": offset_1,
        "offset_2": offset_2,
        "offset_2_nuisance": offset_2_nuisance,
    }


def _old_palette_rank_rival(generator, grid: list[list[int]]) -> list[list[int]]:
    return generator._rival_old_palette_rank(grid)


def _old_corner_rival(generator, grid: list[list[int]]) -> list[list[int]]:
    return generator._rival_old_corner_slots(grid)


def _run() -> dict[str, Any]:
    generator, source_path, source_sha = load_selected_generator(TASK_ID, root=ROOT)
    adapter = _load_adapter()

    base_draws = 0
    base_corner_matches = 0
    base_palette_matches = 0
    base_origins: set[tuple[int, int]] = set()
    base_palette_orders: set[tuple[int, ...]] = set()
    base_profile_counts: Counter[str] = Counter()
    for band in ("easy", "medium", "hard"):
        for seed in range(24):
            for sample_index in range(8):
                grid = generator.generate(seed, sample_index, difficulty=band)
                errors = generator.self_check(grid)
                if errors:
                    raise AssertionError((band, seed, sample_index, errors))
                expected = generator._official_output(grid)
                facts = generator.semantic_observables(grid)
                base_draws += 1
                base_profile_counts[generator.schedule_profile(seed, sample_index, band)] += 1
                base_corner_matches += _old_corner_rival(generator, grid) == expected
                base_palette_matches += _old_palette_rank_rival(generator, grid) == expected
                comps = generator._components(grid)
                base_origins.update((comp["bbox"][0], comp["bbox"][1]) for comp in comps)
                sorted_colors = sorted(comp["color"] for comp in comps)
                rank_by_color = {color: rank for rank, color in enumerate(sorted_colors)}
                official = sorted(comps, key=lambda comp: (-comp["size"], comp["color"]))
                base_palette_orders.add(tuple(rank_by_color[comp["color"]] for comp in official))
                if facts["n_blobs"] not in {3, 4}:
                    raise AssertionError("bad base component count")

    if base_corner_matches != 0:
        raise AssertionError(f"old corner rival survived {base_corner_matches} base draws")
    if base_palette_matches >= base_draws // 3:
        raise AssertionError(f"old palette rival survived too often: {base_palette_matches}/{base_draws}")
    if len(base_origins) < 40:
        raise AssertionError(f"placement support remained too narrow: {len(base_origins)} origins")
    if len(base_palette_orders) < 6:
        raise AssertionError(f"palette-rank support remained too narrow: {base_palette_orders}")

    exact_axis_cases = 0
    for seed, overrides in enumerate(
        (
            {"grid_h": 10, "grid_w": 10, "n_blobs": 3},
            {"grid_h": 18, "grid_w": 18, "n_blobs": 4},
            {"size_pattern": "consecutive", "input_size_order": "zigzag"},
            {"size_pattern": "spread", "palette_kind": "high"},
        )
    ):
        for band in ("easy", "medium", "hard"):
            grid = generator.generate(9000 + seed, seed, difficulty=band, **overrides)
            observed = generator.observe_overrides(grid)
            for axis, expected in overrides.items():
                if observed[axis] != expected:
                    raise AssertionError((axis, expected, observed[axis]))
            exact_axis_cases += 1

    malformed_base_rejections = 0
    for args, kwargs in (
        ((True, 0), {}),
        ((0, True), {}),
        ((0, -1), {}),
        ((0, 0), {"difficulty": "extreme"}),
        ((0, 0), {"grid_h": True}),
        ((0, 0), {"unknown_axis": 1}),
    ):
        try:
            generator.generate(*args, **kwargs)
        except (TypeError, ValueError):
            malformed_base_rejections += 1
        else:
            raise AssertionError((args, kwargs, "malformed base request accepted"))

    modes = ("size_desc", "border_shift")
    parametric_episodes = 0
    parametric_pairs = 0
    lesson_checks = 0
    query_prefix_checks = 0
    matched_input_checks = 0
    minimum_crossed_nuisance_checks = 0
    dimensions: Counter[str] = Counter()
    offsets: Counter[int] = Counter()
    selector_sides: Counter[str] = Counter()
    rival_kills: Counter[str] = Counter()
    minimum_failures: list[dict[str, Any]] = []

    for seed in range(64):
        episodes = {
            mode: adapter.generate(seed, {"order_mode": mode}, 2, 4)
            for mode in modes
        }
        canonical, shifted = episodes["size_desc"], episodes["border_shift"]
        minimum_grids = [pair["input"] for pair in shifted["train"]]
        minimum_facts = [adapter.scene_facts(grid) for grid in minimum_grids]
        minimum_selectors = [facts["border_components"][0] for facts in minimum_facts]
        nuisance_keys = []
        for grid, facts, selector in zip(minimum_grids, minimum_facts, minimum_selectors):
            r1, c1, r2, c2 = selector["bbox"]
            sides = tuple(
                name
                for name, touches in (
                    ("top", r1 == 0),
                    ("left", c1 == 0),
                    ("bottom", r2 == len(grid) - 1),
                    ("right", c2 == len(grid[0]) - 1),
                )
                if touches
            )
            nonselector_sizes = tuple(
                sorted(comp["size"] for comp in facts["components"] if comp is not selector)
            )
            nuisance_keys.append(
                (len(grid), len(grid[0]), facts["component_count"], sides, nonselector_sizes)
            )
        if len(set(nuisance_keys)) != 1:
            raise AssertionError((seed, "minimum demos confound offset with nuisance profile"))
        if {facts["rotation_offset"] for facts in minimum_facts} != {1, 2}:
            raise AssertionError((seed, "minimum demos do not cross offsets 1 and 2"))
        if shifted["train"][0]["output"] == shifted["train"][1]["output"]:
            raise AssertionError((seed, "crossed minimum outputs collapsed"))
        minimum_crossed_nuisance_checks += 1

        canonical_inputs = [pair["input"] for pair in canonical["train"] + canonical["test"]]
        shifted_inputs = [pair["input"] for pair in shifted["train"] + shifted["test"]]
        if canonical_inputs != shifted_inputs:
            raise AssertionError(f"settings lost matched inputs at seed {seed}")
        matched_input_checks += 1

        for query_count in range(1, 5):
            prefix = adapter.generate(seed, {"order_mode": "border_shift"}, 2, query_count)
            if prefix["test"] != shifted["test"][:query_count]:
                raise AssertionError((seed, query_count, "unstable query prefix"))
            query_prefix_checks += 1

        for mode, episode in episodes.items():
            parametric_episodes += 1
            identities = [
                json.dumps(pair["input"], separators=(",", ":"))
                for pair in episode["train"] + episode["test"]
            ]
            if len(identities) != len(set(identities)):
                raise AssertionError((seed, mode, "duplicate inputs"))
            reasons = adapter.lesson_identifiable(episode["train"], episode["test"])
            lesson_checks += 1
            if reasons:
                minimum_failures.append({"seed": seed, "mode": mode, "reasons": reasons})
                raise AssertionError(minimum_failures[-1])

            for name, rival in adapter._RIVALS.items():
                if any(rival(pair["input"]) != pair["output"] for pair in episode["train"]):
                    rival_kills[name] += 1
                else:
                    raise AssertionError((seed, mode, name, "rival fits both minimum demos"))

            for pair in episode["train"] + episode["test"]:
                parametric_pairs += 1
                grid = pair["input"]
                facts = adapter.scene_facts(grid)
                if pair["output"] != adapter.output_for(grid, mode):
                    raise AssertionError((seed, mode, "Python label mismatch"))
                if len(facts["border_components"]) != 1:
                    raise AssertionError((seed, mode, "nonunique selector"))
                if not 0 < facts["rotation_offset"] < facts["component_count"]:
                    raise AssertionError((seed, mode, "collapsing intermediate"))
                selector = facts["border_components"][0]
                rank = sorted(comp["color"] for comp in facts["components"]).index(selector["color"])
                if rank in {0, facts["rotation_offset"]}:
                    raise AssertionError((seed, mode, "selector color rank shortcut"))
                offsets[facts["rotation_offset"]] += 1
                dimensions[f"{len(grid)}x{len(grid[0])}"] += 1
                r1, c1, r2, c2 = selector["bbox"]
                side = (
                    "top" if r1 == 0 else "bottom" if r2 == len(grid) - 1
                    else "left" if c1 == 0 else "right"
                )
                selector_sides[side] += 1

    if dimensions["30x30"] != 64 * len(modes):
        raise AssertionError(f"30x30 query coverage mismatch: {dimensions['30x30']}")
    if set(offsets) != {1, 2, 3}:
        raise AssertionError(f"insufficient offset support: {dict(offsets)}")
    if set(selector_sides) != {"top", "bottom", "left", "right"}:
        raise AssertionError(f"insufficient border-side support: {dict(selector_sides)}")

    crossed = _crossed_scenes()
    crossed_facts = {name: adapter.scene_facts(grid) for name, grid in crossed.items()}
    if crossed_facts["offset_1"]["rotation_offset"] != 1:
        raise AssertionError("crossed offset-1 control failed")
    if crossed_facts["offset_2"]["rotation_offset"] != 2:
        raise AssertionError("crossed offset-2 control failed")
    if crossed_facts["offset_2_nuisance"]["rotation_offset"] != 2:
        raise AssertionError("crossed nuisance control failed")
    for name, grid in crossed.items():
        canonical = adapter.output_for(grid, "size_desc")
        shifted = adapter.output_for(grid, "border_shift")
        if canonical == shifted:
            raise AssertionError((name, "intermediate became observationally irrelevant"))

    malformed_parametric_rejections = 0
    bad_calls = (
        lambda: adapter.generate(True, {"order_mode": "size_desc"}, 2, 4),
        lambda: adapter.generate(0, {"order_mode": "size_desc"}, True, 4),
        lambda: adapter.generate(0, {"order_mode": "size_desc"}, 2, True),
        lambda: adapter.generate(0, {"order_mode": "size_desc"}, 1, 4),
        lambda: adapter.generate(0, {"order_mode": "size_desc"}, 7, 4),
        lambda: adapter.generate(0, {"order_mode": "size_desc"}, 2, 0),
        lambda: adapter.generate(0, {"order_mode": "size_desc"}, 2, 5),
        lambda: adapter.program({}),
        lambda: adapter.program({"order_mode": "size_desc", "extra": 1}),
        lambda: adapter.scene_facts([[0, True], [0, 1]]),
        lambda: adapter.scene_facts([[0, 1], [0]]),
        lambda: adapter.scene_facts([[0.0, 1], [0, 1]]),
    )
    for call in bad_calls:
        try:
            call()
        except (TypeError, ValueError):
            malformed_parametric_rejections += 1
        else:
            raise AssertionError("malformed parametric request/grid accepted")

    return {
        "schema": "arcpuzzles-677dcb71e2be-adversarial-probe-v1",
        "task_id": TASK_ID,
        "source": {
            "path": source_path.relative_to(ROOT).as_posix(),
            "sha256": source_sha,
            "generator_version": generator.VERSION,
            "rule_hash": generator.RULE_HASH,
        },
        "base": {
            "generated_draws": base_draws,
            "profiles": dict(sorted(base_profile_counts.items())),
            "distinct_component_origins": len(base_origins),
            "distinct_official_palette_rank_orders": len(base_palette_orders),
            "old_corner_rival_matches": base_corner_matches,
            "old_palette_rank_rival_matches": base_palette_matches,
            "exact_axis_cases": exact_axis_cases,
            "malformed_requests_rejected": malformed_base_rejections,
        },
        "parametric": {
            "seeds": 64,
            "minimum_demos": 2,
            "episodes": parametric_episodes,
            "labeled_pairs_checked_in_python": parametric_pairs,
            "minimum_lesson_checks": lesson_checks,
            "matched_input_checks": matched_input_checks,
            "minimum_crossed_nuisance_checks": minimum_crossed_nuisance_checks,
            "query_prefix_checks": query_prefix_checks,
            "dimensions": dict(sorted(dimensions.items())),
            "rotation_offsets": {str(k): v for k, v in sorted(offsets.items())},
            "selector_sides": dict(sorted(selector_sides.items())),
            "rival_kills_at_minimum": dict(sorted(rival_kills.items())),
            "malformed_requests_or_grids_rejected": malformed_parametric_rejections,
            "crossed_controls": {
                name: {
                    "dimensions": [len(grid), len(grid[0])],
                    "rotation_offset": crossed_facts[name]["rotation_offset"],
                    "component_sizes": sorted(
                        comp["size"] for comp in crossed_facts[name]["components"]
                    ),
                }
                for name, grid in crossed.items()
            },
        },
        "limits": [
            "Finite Python-side rival and sampler audit; not a universal uniqueness proof.",
            "Protected Racket parity, source-bound qualification, causal replay, and public projection are separate receipts.",
        ],
    }


def main() -> None:
    report = _run()
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
