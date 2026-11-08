"""Independent semantic and boundary checks for the opt-in parametric family.

This suite never uses the prototype's object or ranking helpers for expected
labels. Native qualification separately executes every retained label in Racket.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
import sys

import pytest


HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]
SOURCE = HOME / "workspace" / "parametric" / "prototype.py"
TASK = "ef03216cf2fa"
RANKINGS = ("perimeter", "normalized_top_edge")


def _load_prototype():
    assert SOURCE.is_file(), "the native parametric prototype is not implemented"
    spec = importlib.util.spec_from_file_location("ef03216cf2fa_parametric_test", SOURCE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def prototype():
    return _load_prototype()


def _objects(grid):
    """Literal flood fill; source grammar keeps object bounding boxes disjoint."""
    rows, cols = len(grid), len(grid[0])
    seen = set()
    objects = []
    for row in range(rows):
        for col in range(cols):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            pending = [(row, col)]
            seen.add((row, col))
            cells = []
            while pending:
                r, c = pending.pop()
                cells.append((r, c))
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (0 <= nr < rows and 0 <= nc < cols
                            and (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        pending.append((nr, nc))
            top, bottom = min(r for r, _ in cells), max(r for r, _ in cells)
            left, right = min(c for _, c in cells), max(c for _, c in cells)
            crop = [[0] * (right - left + 1) for _ in range(bottom - top + 1)]
            for r, c in cells:
                crop[r - top][c - left] = color
            objects.append({"color": color, "top": top, "left": left,
                            "crop": crop, "cells": cells})
    return objects


def _quarter_turn(crop, clockwise=True):
    height, width = len(crop), len(crop[0])
    turned = [[0] * height for _ in range(width)]
    for row in range(height):
        for col in range(width):
            if clockwise:
                turned[col][height - row - 1] = crop[row][col]
            else:
                turned[width - col - 1][row] = crop[row][col]
    return turned


def _oracle(grid, ranking="perimeter", rival=None):
    objects = _objects(grid)
    ordered = []
    for obj in objects:
        raw = obj["crop"]
        height, width = len(raw), len(raw[0])
        shape = deepcopy(raw)
        if height > width and rival != "no_rotation":
            shape = _quarter_turn(raw, clockwise=rival != "counterclockwise")
        actual_ranking = ranking
        if rival == "other_setting":
            actual_ranking = RANKINGS[1 - RANKINGS.index(ranking)]
        score = (2 * (height + width) if actual_ranking == "perimeter"
                 else sum(value != 0 for value in shape[0]))
        if rival == "bbox_area":
            score = height * width
        elif rival == "ink":
            score = len(obj["cells"])
        elif rival == "normalized_width":
            score = len(shape[0])
        elif rival == "normalized_height":
            score = len(shape)
        elif rival == "source_top_edge":
            score = sum(value != 0 for value in raw[0])
        elif rival == "normalized_bottom_edge":
            score = sum(value != 0 for value in shape[-1])
        elif rival == "top_span":
            positions = [col for col, value in enumerate(shape[0]) if value != 0]
            score = max(positions) - min(positions) + 1
        top, left = obj["top"], obj["left"]
        key = (-score, top, left)
        if rival == "source_order":
            key = (top, left)
        elif rival == "reverse_source":
            key = (-top, -left)
        elif rival == "ascending":
            key = (score, top, left)
        elif rival == "reverse_ties":
            key = (-score, -top, -left)
        elif rival == "color_ascending":
            key = (obj["color"], top, left)
        elif rival == "color_descending":
            key = (-obj["color"], top, left)
        ordered.append((key, shape))
    ordered.sort(key=lambda item: item[0])
    shapes = [shape for _, shape in ordered]
    height = sum(len(shape) for shape in shapes) + len(shapes) - 1
    width = max(len(shape[0]) for shape in shapes)
    output = [[0] * width for _ in range(height)]
    offset = 0
    for shape in shapes:
        for row, values in enumerate(shape):
            output[offset + row][:len(values)] = values
        offset += len(shape) + 1
    return output


RIVALS = (
    "other_setting", "source_order", "reverse_source", "bbox_area", "ink",
    "normalized_width", "normalized_height", "source_top_edge",
    "normalized_bottom_edge", "top_span", "ascending", "reverse_ties",
    "counterclockwise", "no_rotation", "color_ascending", "color_descending",
)


def _scene(height, width, placed):
    grid = [[0] * width for _ in range(height)]
    for top, left, shape in placed:
        for row, values in enumerate(shape):
            for col, value in enumerate(values):
                grid[top + row][left + col] = value
    return grid


TALL_A = [[2, 0, 0], [2, 2, 0], [2, 2, 0],
          [0, 2, 2], [0, 2, 2], [2, 2, 2]]
TALL_B = [[0, 3, 3], [0, 3, 3], [0, 3, 3], [0, 3, 3], [3, 3, 0]]
WIDE_C = [[0, 7, 7, 0], [7, 7, 7, 7]]


def _block_colors(output):
    colors = []
    in_block = False
    for row in output:
        ink = [value for value in row if value]
        if ink and not in_block:
            colors.append(ink[0])
        in_block = bool(ink)
    return colors


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_default_program_is_exact_selected_canonical_source():
    prototype = _load_prototype()
    from arcpuzzles import Catalog

    selected = Catalog(ROOT)._variants()[TASK][0]["program_solution"]
    assert prototype.program({"ranking": "perimeter"}) == selected


def test_canonical_pairs_agree_with_independent_oracle_and_default(prototype):
    helper_path = ROOT / "shared" / "runtime" / "reviewer_support.py"
    spec = importlib.util.spec_from_file_location("ef03216cf2fa_reviewer_support_test", helper_path)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    pairs = helper.canonical_pairs(TASK, root=ROOT, labeled_only=True)
    assert pairs
    for pair in pairs:
        assert _oracle(pair["input"]) == pair["output"]
        assert prototype.solve(pair["input"]) == pair["output"]


def test_normalize_then_rank_has_literal_causal_output(prototype):
    grid = _scene(10, 12, [(0, 0, TALL_B), (0, 5, WIDE_C), (4, 5, TALL_A)])
    expected = [
        [2, 0, 0, 2, 2, 2], [2, 2, 2, 2, 2, 0], [2, 2, 2, 0, 0, 0],
        [0, 0, 0, 0, 0, 0], [0, 7, 7, 0, 0, 0], [7, 7, 7, 7, 0, 0],
        [0, 0, 0, 0, 0, 0], [3, 0, 0, 0, 0, 0], [3, 3, 3, 3, 3, 0],
        [0, 3, 3, 3, 3, 0],
    ]
    before = deepcopy(grid)
    assert _oracle(grid, "normalized_top_edge") == expected
    assert prototype.solve(grid, ranking="normalized_top_edge") == expected
    assert _block_colors(_oracle(grid, "perimeter")) == [2, 3, 7]
    assert _block_colors(_oracle(grid, "normalized_top_edge", "source_top_edge")) == [3, 7, 2]
    assert grid == before


def test_edge_score_ties_use_source_order_instead_of_perimeter_or_color(prototype):
    wide_d = [[2, 0, 0, 0, 2, 0, 0], [2, 2, 2, 2, 2, 2, 2],
              [0, 0, 0, 2, 0, 2, 0]]
    grid = _scene(10, 15, [(0, 0, WIDE_C), (3, 0, wide_d), (4, 11, TALL_B)])
    expected = _oracle(grid, "normalized_top_edge")
    assert _block_colors(expected) == [7, 2, 3]
    assert prototype.solve(grid, ranking="normalized_top_edge") == expected


def test_canonical_perimeter_ties_use_original_row_major_position(prototype):
    square = [[2, 2, 0], [2, 2, 2], [2, 0, 0]]
    grid = _scene(10, 12, [(0, 0, square), (0, 7, WIDE_C), (4, 0, TALL_B)])
    expected = _oracle(grid)
    assert _block_colors(expected) == [3, 2, 7]
    assert prototype.solve(grid) == expected


@pytest.mark.parametrize("ranking", RANKINGS)
def test_generated_labels_match_independent_oracle(prototype, ranking):
    for seed in (0, 17):
        episode = prototype.generate(seed, {"ranking": ranking}, 3, 4)
        assert episode["program_solution"] == prototype.program({"ranking": ranking})
        for pair in episode["train"] + episode["test"]:
            assert pair["output"] == _oracle(pair["input"], ranking)
            assert 1 <= len(pair["output"]) <= 30
            assert 1 <= len(pair["output"][0]) <= 30
            assert all(type(value) is int and 0 <= value <= 9
                       for row in pair["output"] for value in row)


@pytest.mark.parametrize("demos,queries", [(2, 4), (3, 1), (6, 4)])
def test_demo_and_query_counts_are_independent(prototype, demos, queries):
    episode = prototype.generate(101, {"ranking": "normalized_top_edge"}, demos, queries)
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == queries


def test_invalid_seed_types_and_bounds_are_rejected(prototype):
    for seed in (True, -1, 2 ** 63, "0", 1.5, None):
        with pytest.raises((TypeError, ValueError)):
            prototype.generate(seed, {"ranking": "perimeter"}, 3, 4)
    assert len(prototype.generate(2 ** 63 - 1, {"ranking": "perimeter"}, 2, 1)["test"]) == 1


def test_invalid_demo_counts_are_rejected(prototype):
    for demos in (True, 0, 1, 7, 3.0, "3"):
        with pytest.raises((TypeError, ValueError)):
            prototype.generate(0, {"ranking": "perimeter"}, demos, 4)


def test_invalid_query_counts_are_rejected(prototype):
    for queries in (True, 0, 5, 4.0, "4"):
        with pytest.raises((TypeError, ValueError)):
            prototype.generate(0, {"ranking": "perimeter"}, 3, queries)


def test_unknown_and_malformed_settings_are_rejected(prototype):
    for settings in ({}, {"ranking": "unknown"}, {"ranking": True},
                     {"ranking": "perimeter", "extra": 1}, None):
        with pytest.raises((TypeError, ValueError)):
            prototype.program(settings)
        with pytest.raises((TypeError, ValueError)):
            prototype.generate(0, settings, 3, 4)


def test_episode_generation_is_deterministic(prototype):
    settings = {"ranking": "normalized_top_edge"}
    assert prototype.generate(29, settings, 3, 4) == prototype.generate(29, settings, 3, 4)
    assert settings == {"ranking": "normalized_top_edge"}


def test_input_sampling_is_matched_across_private_settings(prototype):
    canonical = prototype.generate(71, {"ranking": "perimeter"}, 2, 4)
    alternate = prototype.generate(71, {"ranking": "normalized_top_edge"}, 2, 4)
    assert _inputs(canonical) == _inputs(alternate)
    assert any(a["output"] != b["output"]
               for a, b in zip(canonical["train"], alternate["train"]))


def test_first_query_and_demonstrations_are_stable_when_requesting_four_queries(prototype):
    settings = {"ranking": "normalized_top_edge"}
    single = prototype.generate(5, settings, 3, 1)
    multiple = prototype.generate(5, settings, 3, 4)
    assert single["train"] == multiple["train"]
    assert single["test"][0] == multiple["test"][0]


def test_four_queries_are_novel_and_have_distinct_grid_shapes(prototype):
    episode = prototype.generate(5, {"ranking": "perimeter"}, 6, 4)
    inputs = _inputs(episode)
    frozen = [tuple(tuple(row) for row in grid) for grid in inputs]
    assert len(frozen) == len(set(frozen))
    sizes = {(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]}
    assert len(sizes) == 4
    assert (30, 30) in sizes


def test_thirty_by_thirty_query_has_substantive_six_object_content(prototype):
    episode = prototype.generate(17, {"ranking": "normalized_top_edge"}, 2, 4)
    large = [pair for pair in episode["test"]
             if (len(pair["input"]), len(pair["input"][0])) == (30, 30)]
    assert len(large) == 1
    grid = large[0]["input"]
    objects = _objects(grid)
    assert len(objects) == 6
    occupied = [cell for obj in objects for cell in obj["cells"]]
    assert len(occupied) >= 72
    assert max(row for row, _ in occupied) - min(row for row, _ in occupied) >= 26
    assert max(col for _, col in occupied) - min(col for _, col in occupied) >= 26
    assert len({(row // 15, col // 15) for row, col in occupied}) == 4
    assert large[0]["output"] == _oracle(grid, "normalized_top_edge")
    assert len(large[0]["output"]) <= 30


@pytest.mark.parametrize("ranking", RANKINGS)
def test_two_demos_reject_query_relevant_finite_rivals(prototype, ranking):
    for seed in (0, 17, 71):
        episode = prototype.generate(seed, {"ranking": ranking}, 2, 4)
        for rival in RIVALS:
            changes_query = any(_oracle(pair["input"], ranking, rival) != pair["output"]
                                for pair in episode["test"])
            survives_demos = all(_oracle(pair["input"], ranking, rival) == pair["output"]
                                 for pair in episode["train"])
            assert not (changes_query and survives_demos), (seed, ranking, rival)
