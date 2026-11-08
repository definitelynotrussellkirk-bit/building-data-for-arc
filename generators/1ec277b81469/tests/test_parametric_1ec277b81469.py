from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import pytest
from reviewer_support import canonical_path, find_root

TASK = "1ec277b81469"
HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"
SPEC = importlib.util.spec_from_file_location(f"parametric_{TASK}", PARAMETRIC / "prototype.py")
PROTO = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(PROTO)

CANONICAL_SETTINGS = {"finish": "canonical"}
SEQUENTIAL_SETTINGS = {"finish": "fill_largest_bbox"}


def _canonical_program():
    import json
    with canonical_path(find_root(__file__)).open() as handle:
        rows = [json.loads(line) for line in handle]
    return next(row["program_solution"] for row in rows if row["task_id"] == TASK)


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_exact_canonical_program_and_nontrivial_sequential_program():
    canonical = _canonical_program()
    assert PROTO.program(CANONICAL_SETTINGS) == canonical
    assert (PARAMETRIC / "canonical.rkt").read_text() == canonical
    sequential = PROTO.program(SEQUENTIAL_SETTINGS)
    assert sequential != canonical
    assert "intermediate" in sequential
    assert "objects intermediate 0" in sequential
    assert "draw-rect-filled" in sequential


def test_generation_is_count_independent_setting_blind_and_distinct():
    short = PROTO.generate(17, CANONICAL_SETTINGS, demos=2, queries=1)
    long = PROTO.generate(17, CANONICAL_SETTINGS, demos=6, queries=4)
    alternate = PROTO.generate(17, SEQUENTIAL_SETTINGS, demos=6, queries=4)
    assert short["train"] == long["train"][:2]
    assert short["test"] == long["test"][:1]
    assert _inputs(long) == _inputs(alternate)
    assert len({PROTO.digest(grid) for grid in _inputs(long)}) == 10


def test_two_demos_identify_both_settings_and_queries_transfer():
    for seed in (0, 7, 17, 41, 91):
        episodes = {
            name: PROTO.generate(seed, {"finish": name}, demos=2, queries=4)
            for name in ("canonical", "fill_largest_bbox")
        }
        for chosen, episode in episodes.items():
            survivors = []
            for candidate in ("canonical", "fill_largest_bbox"):
                setting = {"finish": candidate}
                if all(PROTO.transform(pair["input"], setting) == pair["output"] for pair in episode["train"]):
                    survivors.append(candidate)
            assert survivors == [chosen]
            assert all(
                PROTO.transform(pair["input"], {"finish": chosen}) == pair["output"]
                for pair in episode["test"]
            )


def test_step_b_uses_a_unique_largest_component_created_by_step_a():
    episode = PROTO.generate(31, SEQUENTIAL_SETTINGS, demos=6, queries=4)
    summaries = [PROTO.stage_summary(pair["input"]) for pair in episode["train"] + episode["test"]]
    assert len({tuple(summary["largest_anchor"]) for summary in summaries}) >= 4
    assert len({summary["largest_size"] for summary in summaries}) >= 3
    assert len({summary["largest_color"] for summary in summaries}) >= 3
    assert len({tuple(summary["largest_bbox"]) for summary in summaries}) >= 5
    for pair, summary in zip(episode["train"] + episode["test"], summaries):
        intermediate = PROTO.transform(pair["input"], CANONICAL_SETTINGS)
        assert summary["intermediate"] == intermediate
        assert summary["source_largest_size"] < summary["largest_size"]
        assert pair["output"] != intermediate
        r1, c1, r2, c2 = summary["largest_bbox"]
        changed = {
            (r, c)
            for r, row in enumerate(pair["output"])
            for c, value in enumerate(row)
            if value != intermediate[r][c]
        }
        assert changed
        assert all(r1 <= r <= r2 and c1 <= c <= c2 for r, c in changed)
        assert summary["skip_a_output"] != pair["output"]


def test_query_bank_covers_boundary_aspect_ratios_and_dense_30_by_30_stress():
    episode = PROTO.generate(5, SEQUENTIAL_SETTINGS, demos=2, queries=4)
    shapes = [(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]]
    assert shapes[0] == (7, 11)
    assert shapes[-1] == (30, 30)
    assert len({height > width for height, width in shapes}) == 2
    large = episode["test"][-1]["input"]
    assert sum(cell != 0 for row in large for cell in row) >= 180
    summary = PROTO.stage_summary(large)
    assert summary["component_count"] >= 10
    assert summary["largest_size"] >= 20
    assert summary["skip_a_output"] != episode["test"][-1]["output"]


def test_fixed_shape_crossed_controls_change_intermediate_not_just_nuisance_position():
    rows = [PROTO.sample_input(seed, "cross", 0, 18, 24) for seed in range(8)]
    summaries = [PROTO.stage_summary(grid) for grid in rows]
    assert len({summary["largest_color"] for summary in summaries}) >= 4
    assert len({tuple(summary["largest_bbox"]) for summary in summaries}) >= 5
    assert len({PROTO.digest(summary["intermediate"]) for summary in summaries}) == len(rows)
    assert len({PROTO.digest(grid) for grid in rows}) == len(rows)


def test_validation_rejects_bad_settings_counts_and_cells_without_mutation():
    with pytest.raises(ValueError, match="exactly finish"):
        PROTO.program({})
    with pytest.raises(ValueError, match="finish"):
        PROTO.program({"finish": "unknown"})
    with pytest.raises(ValueError, match="demos"):
        PROTO.generate(0, CANONICAL_SETTINGS, demos=1, queries=4)
    with pytest.raises(ValueError, match="queries"):
        PROTO.generate(0, CANONICAL_SETTINGS, demos=2, queries=5)
    bad = [[0, True], [3, 0]]
    before = copy.deepcopy(bad)
    with pytest.raises(ValueError, match="exact integer"):
        PROTO.transform(bad, CANONICAL_SETTINGS)
    assert bad == before


def _bbox_of(component):
    rows = [row for row, _ in component["cells"]]
    cols = [col for _, col in component["cells"]]
    return min(rows), min(cols), max(rows), max(cols)


def _fill_bbox(grid, component):
    result = [row[:] for row in grid]
    r1, c1, r2, c2 = _bbox_of(component)
    for row in range(r1, r2 + 1):
        for col in range(c1, c2 + 1):
            result[row][col] = 9
    return result


def _components_8(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    components = []
    for start_row in range(height):
        for start_col in range(width):
            color = grid[start_row][start_col]
            if color == 0 or (start_row, start_col) in seen:
                continue
            stack = [(start_row, start_col)]
            seen.add((start_row, start_col))
            cells = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = row + dr, col + dc
                        if (
                            0 <= nr < height
                            and 0 <= nc < width
                            and (nr, nc) not in seen
                            and grid[nr][nc] == color
                        ):
                            seen.add((nr, nc))
                            stack.append((nr, nc))
            components.append({"color": color, "cells": tuple(sorted(cells))})
    return components


def _rank_shortcuts(grid):
    from collections import Counter

    intermediate = PROTO._right_pack(grid)
    components = PROTO._components(intermediate)

    def area(component):
        r1, c1, r2, c2 = _bbox_of(component)
        return (r2 - r1 + 1) * (c2 - c1 + 1)

    def height(component):
        r1, _, r2, _ = _bbox_of(component)
        return r2 - r1 + 1

    def width(component):
        _, c1, _, c2 = _bbox_of(component)
        return c2 - c1 + 1

    largest = max(components, key=lambda component: len(component["cells"]))
    frequencies = Counter(value for row in intermediate for value in row if value)
    modal_color = max(frequencies, key=lambda color: (frequencies[color], -color))
    modal_component = max(
        (component for component in components if component["color"] == modal_color),
        key=lambda component: len(component["cells"]),
    )
    all_largest_color = {
        "color": largest["color"],
        "cells": tuple(
            (row, col)
            for row, values in enumerate(intermediate)
            for col, value in enumerate(values)
            if value == largest["color"]
        ),
    }
    return {
        "largest_bbox_area": _fill_bbox(intermediate, max(components, key=lambda c: (area(c), len(c["cells"])))),
        "largest_bbox_height": _fill_bbox(intermediate, max(components, key=lambda c: (height(c), len(c["cells"])))),
        "largest_bbox_width": _fill_bbox(intermediate, max(components, key=lambda c: (width(c), len(c["cells"])))),
        "largest_8_connected": _fill_bbox(intermediate, max(_components_8(intermediate), key=lambda c: len(c["cells"]))),
        "most_frequent_color": _fill_bbox(intermediate, modal_component),
        "all_cells_of_largest_color": _fill_bbox(intermediate, all_largest_color),
        "first_component": _fill_bbox(intermediate, components[0]),
        "topmost_component": _fill_bbox(intermediate, min(components, key=lambda c: (_bbox_of(c)[0], _bbox_of(c)[1]))),
        "bottommost_component": _fill_bbox(intermediate, max(components, key=lambda c: (_bbox_of(c)[2], len(c["cells"])))),
        "rightmost_component": _fill_bbox(intermediate, max(components, key=lambda c: (_bbox_of(c)[3], len(c["cells"])))),
    }


def test_two_demo_minimum_rejects_rank_frequency_color_and_connectivity_shortcuts():
    for seed in (0, 7, 17, 20, 41, 91, 123):
        episode = PROTO.generate(seed, SEQUENTIAL_SETTINGS, demos=2, queries=4)
        expected = [pair["output"] for pair in episode["train"]]
        candidate_outputs = {}
        for pair in episode["train"]:
            for name, output in _rank_shortcuts(pair["input"]).items():
                candidate_outputs.setdefault(name, []).append(output)
        assert candidate_outputs
        for name, outputs in candidate_outputs.items():
            assert outputs != expected, (seed, name)


def test_many_seed_semantic_sweep_tool_reports_no_shortcut_survivors():
    import importlib.util

    path = PARAMETRIC / "semantic_sweep.py"
    spec = importlib.util.spec_from_file_location(f"semantic_sweep_{TASK}", path)
    sweep = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(sweep)
    report = sweep.build_report(seed_count=12)
    assert report["status"] == "passed"
    assert report["seed_count"] == 12
    assert report["rival_count"] >= 12
    assert report["survivor_count"] == 0
    assert report["ambiguous_count"] == 0
