from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root

TASK_ID = "8265382d9c72"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID / "workspace" / "parametric"


def load_probe():
    path = HOME / "probe.py"
    spec = importlib.util.spec_from_file_location("_test_tab_probe", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_prototype():
    path = HOME / "prototype.py"
    name = "_test_tab_prototype_" + hashlib.sha256(str(path).encode()).hexdigest()[:16]
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_adapter():
    path = HOME / "adapter.py"
    name = "_test_tab_adapter_" + hashlib.sha256(str(path).encode()).hexdigest()[:16]
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_program() -> str:
    rows = []
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    rows.append(row)
    assert len(rows) == 1
    return rows[0]["program_solution"]


def components(grid: list[list[int]]) -> list[dict]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            seen.add((row, col))
            stack = [(row, col)]
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            result.append(
                {
                    "color": color,
                    "cells": cells,
                    "bbox": (min(rows), min(cols), max(rows), max(cols)),
                }
            )
    return result


def hole_count(grid: list[list[int]], obj: dict) -> int:
    r0, c0, r1, c1 = obj["bbox"]
    return sum(
        grid[row][col] == 0
        for row in range(r0 + 1, r1)
        for col in range(c0 + 1, c1)
    )


def is_tabbed(obj: dict) -> bool:
    r0, c0, _r1, c1 = obj["bbox"]
    top = [(r, c) for r, c in obj["cells"] if r == r0]
    second = [(r, c) for r, c in obj["cells"] if r == r0 + 1]
    return len(top) == 1 and len(second) == c1 - c0 + 1


def ordered_objects(grid: list[list[int]], mode: str) -> tuple[dict, dict]:
    objects = components(grid)
    assert len(objects) == 2
    left, right = sorted(objects, key=lambda obj: obj["bbox"][1])
    if mode == "left_first":
        first = left
    elif mode == "tab_first":
        tabbed = [obj for obj in objects if is_tabbed(obj)]
        assert len(tabbed) == 1
        first = tabbed[0]
    elif mode == "right_first":
        first = right
    elif mode == "taller_first":
        first = max(objects, key=lambda obj: (obj["bbox"][2] - obj["bbox"][0] + 1, -obj["bbox"][1]))
    elif mode == "smaller_count_first":
        first = min(objects, key=lambda obj: (hole_count(grid, obj), obj["bbox"][1]))
    elif mode == "larger_count_first":
        first = max(objects, key=lambda obj: (hole_count(grid, obj), -obj["bbox"][1]))
    elif mode == "narrower_first":
        first = min(objects, key=lambda obj: (obj["bbox"][3] - obj["bbox"][1] + 1, obj["bbox"][1]))
    elif mode in {"larger_bbox_first", "smaller_bbox_first"}:
        def bbox_area(obj):
            r0, c0, r1, c1 = obj["bbox"]
            return (r1 - r0 + 1) * (c1 - c0 + 1)
        chooser = max if mode == "larger_bbox_first" else min
        first = chooser(objects, key=lambda obj: (bbox_area(obj), -obj["bbox"][1]))
    elif mode == "topmost_first":
        first = min(objects, key=lambda obj: (obj["bbox"][0], obj["bbox"][1]))
    elif mode == "bottommost_first":
        first = max(objects, key=lambda obj: (obj["bbox"][2], -obj["bbox"][1]))
    elif mode == "lower_color_first":
        first = min(objects, key=lambda obj: (obj["color"], obj["bbox"][1]))
    elif mode == "higher_color_first":
        first = max(objects, key=lambda obj: (obj["color"], -obj["bbox"][1]))
    elif mode in {"sparser_first", "denser_first"}:
        def density(obj):
            r0, c0, r1, c1 = obj["bbox"]
            area = (r1 - r0 + 1) * (c1 - c0 + 1)
            return len(obj["cells"]) / area
        chooser = min if mode == "sparser_first" else max
        first = chooser(objects, key=lambda obj: (density(obj), obj["bbox"][1]))
    else:
        raise ValueError(mode)
    second = right if first is left else left
    return first, second


def solve(grid: list[list[int]], mode: str) -> list[list[int]]:
    first, second = ordered_objects(grid, mode)
    n1, n2 = hole_count(grid, first), hole_count(grid, second)
    output = [[0, 0, 0] for _ in range(3)]
    for index in range(n1):
        if index < 9:
            output[index // 3][index % 3] = first["color"]
    start = (n1 + 2) // 3
    for index in range(n2):
        row, col = start + index // 3, index % 3
        if row < 3:
            output[row][col] = second["color"]
    return output


def all_inputs(episode: dict) -> list[list[list[int]]]:
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def test_default_program_is_exact_canonical_bytes_and_tab_rule_is_distinct():
    adapter = load_adapter()
    default = adapter.program({"ordering": "left_first"})
    alternate = adapter.program({"ordering": "tab_first"})
    assert default == canonical_program()
    assert alternate != default
    assert alternate.strip().startswith("(rule!")


def test_generation_is_deterministic_matched_and_query_prefix_stable():
    adapter = load_adapter()
    left = adapter.generate(17, {"ordering": "left_first"}, 3, 4)
    tab = adapter.generate(17, {"ordering": "tab_first"}, 3, 4)
    again = adapter.generate(17, {"ordering": "tab_first"}, 3, 4)
    prefix = adapter.generate(17, {"ordering": "tab_first"}, 3, 1)

    assert tab == again
    assert all_inputs(left) == all_inputs(tab)
    assert prefix["train"] == tab["train"]
    assert prefix["test"] == tab["test"][:1]
    assert len({json.dumps(grid) for grid in all_inputs(tab)}) == 7


def test_labels_match_independent_oracle_and_three_demos_reject_named_shortcuts():
    adapter = load_adapter()
    candidates = (
        "left_first",
        "tab_first",
        "right_first",
        "taller_first",
        "smaller_count_first",
        "larger_count_first",
        "narrower_first",
    )
    for setting in ("left_first", "tab_first"):
        episode = adapter.generate(0, {"ordering": setting}, 3, 4)
        for split in ("train", "test"):
            for pair in episode[split]:
                assert pair["output"] == solve(pair["input"], setting)
        survivors = [
            candidate
            for candidate in candidates
            if all(solve(pair["input"], candidate) == pair["output"] for pair in episode["train"])
        ]
        assert survivors == [setting]


def test_three_demo_lessons_reject_density_position_and_color_shortcuts():
    adapter = load_adapter()
    candidates = (
        "topmost_first",
        "bottommost_first",
        "lower_color_first",
        "higher_color_first",
        "sparser_first",
        "denser_first",
        "larger_bbox_first",
        "smaller_bbox_first",
    )
    for seed in range(32):
        episode = adapter.generate(seed, {"ordering": "tab_first"}, 3, 1)
        for candidate in candidates:
            assert any(
                solve(pair["input"], candidate) != pair["output"]
                for pair in episode["train"]
            ), (seed, candidate)


def test_three_demos_separate_declared_settings_and_break_larger_count_shortcut():
    adapter = load_adapter()
    for setting in ("left_first", "tab_first"):
        episode = adapter.generate(0, {"ordering": setting}, 3, 4)
        declared = [
            candidate
            for candidate in ("left_first", "tab_first")
            if all(solve(pair["input"], candidate) == pair["output"] for pair in episode["train"])
        ]
        assert declared == [setting]
    episode = adapter.generate(0, {"ordering": "tab_first"}, 3, 4)
    assert any(
        solve(pair["input"], "larger_count_first") != pair["output"]
        for pair in episode["train"]
    )


def test_authoring_rival_catalog_covers_and_rejects_adversarial_shortcuts():
    prototype = load_prototype()
    expected = {
        "left_first",
        "tab_first",
        "right_first",
        "taller_first",
        "shorter_first",
        "wider_first",
        "narrower_first",
        "smaller_count_first",
        "larger_count_first",
        "larger_bbox_first",
        "smaller_bbox_first",
        "topmost_first",
        "bottommost_first",
        "lower_color_first",
        "higher_color_first",
        "denser_first",
        "sparser_first",
        "more_cells_first",
        "fewer_cells_first",
    }
    for seed in range(32):
        for setting in ("left_first", "tab_first"):
            episode = prototype.generate(seed, {"ordering": setting}, 3, 1)
            catalogs = [prototype.rival_outputs(pair["input"]) for pair in episode["train"]]
            assert set(catalogs[0]) == expected
            survivors = [
                name
                for name in expected
                if all(catalog[name] == pair["output"] for catalog, pair in zip(catalogs, episode["train"]))
            ]
            assert survivors == [setting], (seed, setting, survivors)


def test_probe_adversarial_census_is_compact_and_intended_only():
    prototype = load_prototype()
    probe = load_probe()
    report = probe._adversarial_census(prototype, 32)
    assert report["status"] == "passed"
    assert report["seed_count"] == 32
    assert report["minimum_demos"] == 3
    assert report["rival_count"] == 19
    assert tuple(report["settings"]) == ('left_first', 'tab_first')
    assert report["case_count"] == 64
    assert report["unexpected_survivors"] == []
    assert len(report["census_sha256"]) == 64


def test_supported_counts_boundaries_and_exact_types():
    adapter = load_adapter()
    for demos in range(3, 7):
        episode = adapter.generate(123, {"ordering": "tab_first"}, demos, 4)
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
    for queries in range(1, 5):
        assert len(adapter.generate(123, {"ordering": "left_first"}, 3, queries)["test"]) == queries

    bad_calls = [
        (True, {"ordering": "tab_first"}, 3, 4),
        (-1, {"ordering": "tab_first"}, 3, 4),
        (0, {"ordering": "unknown"}, 3, 4),
        (0, {"ordering": "tab_first", "extra": 1}, 3, 4),
        (0, {"ordering": "tab_first"}, 1, 4),
        (0, {"ordering": "tab_first"}, 7, 4),
        (0, {"ordering": "tab_first"}, 2, 0),
        (0, {"ordering": "tab_first"}, 2, 5),
        (0, {"ordering": "tab_first"}, 2.0, 4),
    ]
    for args in bad_calls:
        with pytest.raises(ValueError):
            adapter.generate(*args)


def test_fourth_query_is_exact_30_by_30_dense_boundary_stress():
    adapter = load_adapter()
    pair = adapter.generate(17, {"ordering": "tab_first"}, 3, 4)["test"][3]
    grid = pair["input"]
    assert len(grid) == 30 and len(grid[0]) == 30
    active = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    assert len(active) >= 600
    assert max(r for r, _ in active) - min(r for r, _ in active) == 29
    assert max(c for _, c in active) - min(c for _, c in active) == 29
    objects = components(grid)
    assert len(objects) == 2
    assert sum(is_tabbed(obj) for obj in objects) == 1
    assert pair["output"] == solve(grid, "tab_first")


def test_two_demos_are_outside_supported_contract():
    with pytest.raises(ValueError):
        load_adapter().generate(0, {"ordering":"tab_first"}, 2, 4)
