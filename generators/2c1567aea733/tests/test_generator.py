"""Portable regression and teaching-contract tests for ``2c1567aea733``."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root


TASK_ID = "2c1567aea733"
ROOT = find_root(__file__)
TASK_HOME = ROOT / "generators" / TASK_ID


def _load_generator():
    source = Path(
        os.environ.get("GENERATOR_UNDER_TEST", TASK_HOME / "generator.py")
    )
    spec = importlib.util.spec_from_file_location("review_2c1567aea733", source)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()
PAIRS = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
BANDS = (None, "easy", "medium", "hard")
PROFILES = ("copied_rectangles", "copied_irregular", "mixed_shapes")


def _cells_by_color(grid):
    result = {}
    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if value:
                result.setdefault(value, set()).add((row_index, col_index))
    return result


def _normalize(cells):
    top = min(row for row, _ in cells)
    left = min(col for _, col in cells)
    return frozenset((row - top, col - left) for row, col in cells)


def _bbox_shape(cells):
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return max(rows) - min(rows) + 1, max(cols) - min(cols) + 1


def _is_rectangle(cells):
    height, width = _bbox_shape(cells)
    return len(cells) == height * width


def _component_count(cells):
    unseen = set(cells)
    count = 0
    while unseen:
        count += 1
        stack = [unseen.pop()]
        while stack:
            row, col = stack.pop()
            for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    stack.append(neighbor)
    return count


def _oracle(grid, target_top=None):
    """Independent implementation of the selected per-color top-alignment rule."""
    height, width = len(grid), len(grid[0])
    by_color = _cells_by_color(grid)
    if 1 not in by_color:
        raise ValueError("missing blue anchor")
    if target_top is None:
        target_top = min(row for row, _ in by_color[1])
    output = [[0 for _ in range(width)] for _ in range(height)]
    for color, cells in by_color.items():
        color_top = min(row for row, _ in cells)
        shift = target_top - color_top
        for row, col in cells:
            new_row = row + shift
            if 0 <= new_row < height:
                output[new_row][col] = color
    return output


def _median_top_rival(grid):
    """Ignore blue and align every color to the median starting top row."""
    tops = sorted(
        min(row for row, _ in cells)
        for cells in _cells_by_color(grid).values()
    )
    return _oracle(grid, target_top=tops[len(tops) // 2])


def _canonical_size_rank_rival(grid):
    """Use canonical grid height to choose a vertical rank, never color 1."""
    tops = sorted(
        min(row for row, _ in cells)
        for cells in _cells_by_color(grid).values()
    )
    target_top = tops[-1] if len(grid) >= 10 else tops[len(tops) // 2]
    return _oracle(grid, target_top=target_top)


def _blue_rank(grid):
    tops = {
        color: min(row for row, _ in cells)
        for color, cells in _cells_by_color(grid).items()
    }
    return sorted(tops.values()).index(tops[1])


def _profile_of(grid):
    shapes = [_normalize(cells) for cells in _cells_by_color(grid).values()]
    if len(set(shapes)) == 1:
        return "copied_rectangles" if _is_rectangle(next(iter(_cells_by_color(grid).values()))) else "copied_irregular"
    return "mixed_shapes"


def _pinned_seed(band, index):
    digest = hashlib.sha256(
        f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
    ).hexdigest()
    return int(digest[:12], 16)


def test_authority_pin_and_public_contract_are_honest():
    assert GEN.RULE_HASH == "837d7987242d"
    assert GEN.VERSION == "2.1.0"
    assert GEN.EXAMPLES_NEEDED == 3
    assert GEN.MIN_STRICT_FRAC == 1.0
    assert set(GEN.AXES) == {"grid_h", "grid_w", "scene_profile"}
    assert tuple(GEN.SCENE_PROFILES) == PROFILES
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert GEN.HELPFUL_TEXTURES == ()
    assert GEN.DEGENERATE_TEXTURES == ()
    assert GEN.LAWFUL_DEGENERATE_TEXTURES == ()


def test_all_canonical_pairs_are_owned_and_match_an_independent_oracle():
    assert len(PAIRS) == 4
    for pair in PAIRS:
        original = deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert _oracle(pair["input"]) == pair["output"]
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_size_conditioned_vertical_rank_is_a_real_canonical_shortcut():
    # The 10x10 training example uses the lowest-starting object as target; both
    # 5x10 examples use the median-starting object. This cue-free rule fits all
    # demonstrations but fails the 10x10 query, where blue is median instead.
    assert [_blue_rank(pair["input"]) for pair in PAIRS[:3]] == [2, 1, 1]
    assert _blue_rank(PAIRS[3]["input"]) == 1
    for pair in PAIRS[:3]:
        assert _canonical_size_rank_rival(pair["input"]) == pair["output"]
    assert _canonical_size_rank_rival(PAIRS[3]["input"]) != PAIRS[3]["output"]


def test_retained_size_rank_counterexample_is_emitted_and_refutes_the_rival():
    record = json.loads(
        (TASK_HOME / "counterexamples" / "canonical_size_rank.json").read_text()
    )
    recipe = record["recipe"]
    grid = GEN.generate(
        recipe["seed"],
        recipe["sample_index"],
        difficulty=recipe["difficulty"],
        **recipe["overrides"],
    )
    assert grid == record["input"]
    assert GEN.rule_mirror(grid) == record["intended_output"]
    assert GEN.SEMANTIC_RIVALS[record["rival"]](grid) == record["rival_output"]
    assert record["intended_output"] != record["rival_output"]


@pytest.mark.parametrize("difficulty", BANDS)
@pytest.mark.parametrize("height,width", [(5, 10), (12, 15)])
@pytest.mark.parametrize("scene_profile", PROFILES)
def test_every_declared_override_is_exact_observable_and_constructive(
    difficulty, height, width, scene_profile
):
    grid = GEN.generate(
        917,
        13,
        difficulty=difficulty,
        grid_h=height,
        grid_w=width,
        scene_profile=scene_profile,
    )
    assert (len(grid), len(grid[0])) == (height, width)
    assert {value for row in grid for value in row} == {0, 1, 2, 4}
    assert GEN.self_check(grid, difficulty=difficulty) == []
    assert GEN.strict_canonical_like(grid) == []
    assert GEN.observe_overrides(grid) == {
        "grid_h": height,
        "grid_w": width,
        "scene_profile": scene_profile,
    }
    assert _profile_of(grid) == scene_profile
    assert GEN.rule_mirror(grid) == _oracle(grid)
    assert grid == GEN.generate(
        917,
        13,
        difficulty=difficulty,
        grid_h=height,
        grid_w=width,
        scene_profile=scene_profile,
    )


def test_copied_irregular_profile_reproduces_the_canonical_detached_tail_family():
    for seed in range(12):
        grid = GEN.generate(seed, seed + 3, grid_h=10, grid_w=10, scene_profile="copied_irregular")
        by_color = _cells_by_color(grid)
        shapes = {_normalize(cells) for cells in by_color.values()}
        assert len(shapes) == 1
        assert all(not _is_rectangle(cells) for cells in by_color.values())
        assert all(_component_count(cells) == 2 for cells in by_color.values())
        assert all(len(cells) == 5 for cells in by_color.values())
        output = GEN.rule_mirror(grid)
        assert {_normalize(cells) for cells in _cells_by_color(output).values()} == shapes


def test_mixed_shapes_profile_defeats_bottom_alignment_and_component_shortcuts():
    for seed in range(12):
        grid = GEN.generate(seed + 50, seed, grid_h=10, grid_w=10, scene_profile="mixed_shapes")
        by_color = _cells_by_color(grid)
        normalized = [_normalize(cells) for cells in by_color.values()]
        heights = {_bbox_shape(cells)[0] for cells in by_color.values()}
        assert len(set(normalized)) == 3
        assert len(heights) >= 2
        assert any(_component_count(cells) == 2 for cells in by_color.values())
        intended = _oracle(grid)
        blue_bottom = max(row for row, _ in by_color[1])
        bottom_aligned = [[0] * len(grid[0]) for _ in grid]
        for color, cells in by_color.items():
            shift = blue_bottom - max(row for row, _ in cells)
            for row, col in cells:
                bottom_aligned[row + shift][col] = color
        assert intended != bottom_aligned


def test_anchor_schedule_refutes_rank_shortcuts_in_every_three_demo_window():
    expected_cycle = (0, 1, 2, 0)
    for difficulty in ("easy", "medium", "hard"):
        for scene_profile in PROFILES:
            for start in range(6):
                grids = [
                    GEN.generate(
                        3000,
                        start + offset,
                        difficulty=difficulty,
                        grid_h=10,
                        grid_w=10,
                        scene_profile=scene_profile,
                    )
                    for offset in range(4)
                ]
                ranks = [_blue_rank(grid) for grid in grids]
                assert ranks == [
                    expected_cycle[(start + offset) % len(expected_cycle)]
                    for offset in range(4)
                ]
                assert set(ranks) == {0, 1, 2}
                for query_index in range(4):
                    demo_ranks = [rank for index, rank in enumerate(ranks) if index != query_index]
                    assert 0 in demo_ranks
                    assert len(set(demo_ranks)) >= 2
                for grid in grids:
                    by_color = _cells_by_color(grid)
                    tops = {
                        color: min(row for row, _ in cells)
                        for color, cells in by_color.items()
                    }
                    output = GEN.rule_mirror(grid)
                    out_tops = {
                        color: min(row for row, _ in cells)
                        for color, cells in _cells_by_color(output).items()
                    }
                    assert set(out_tops.values()) == {tops[1]}
                    assert output != grid


@pytest.mark.parametrize(
    "args,kwargs",
    [
        ((True, 0), {}),
        ((1.0, 0), {}),
        (("1", 0), {}),
        ((1, True), {}),
        ((1, -1), {}),
        ((1, 1.0), {}),
        ((1, 0), {"difficulty": True}),
        ((1, 0), {"difficulty": "extreme"}),
        ((1, 0), {"unknown_axis": 1}),
        ((1, 0), {"grid_h": 4}),
        ((1, 0), {"grid_h": 13}),
        ((1, 0), {"grid_h": 5.0}),
        ((1, 0), {"grid_h": "5"}),
        ((1, 0), {"grid_w": 9}),
        ((1, 0), {"grid_w": 16}),
        ((1, 0), {"grid_w": True}),
        ((1, 0), {"scene_profile": "unknown"}),
        ((1, 0), {"scene_profile": 1}),
    ],
)
def test_invalid_call_arguments_and_overrides_fail_loudly(args, kwargs):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(*args, **kwargs)


def test_profile_floor_has_exact_support_in_every_band():
    canonical_profiles = {(5, 10, 4), (10, 10, 4)}
    for band in ("easy", "medium", "hard"):
        hits = 0
        envelope = 0
        for index in range(20):
            seed = _pinned_seed(band, index)
            sample_index = seed % 7919 + index
            grid = GEN.generate(seed, sample_index, difficulty=band)
            profile = (
                len(grid),
                len(grid[0]),
                len({value for row in grid for value in row}),
            )
            hits += profile in canonical_profiles
            envelope += 5 <= profile[0] <= 10 and profile[1] == 10 and profile[2] == 4
        assert hits >= 1, (band, hits)
        assert envelope >= 5, (band, envelope)


def test_semantic_contract_names_real_rivals_and_every_lesson_refutes_them():
    assert set(GEN.SEMANTIC_WITNESSES) == {
        "visible_motion",
        "blue_between_extremes",
        "blue_not_median",
        "blue_topmost",
    }
    assert set(GEN.SEMANTIC_RIVALS) == {
        "identity",
        "align_to_highest",
        "align_to_lowest",
        "align_to_median",
        "canonical_size_rank",
    }
    assert GEN.WITNESS_RIVALS == {
        "visible_motion": ["identity"],
        "blue_between_extremes": ["align_to_highest", "align_to_lowest"],
        "blue_not_median": ["align_to_median"],
        "blue_topmost": ["canonical_size_rank"],
    }
    for band in ("easy", "medium", "hard"):
        for start in range(6):
            pairs = []
            for offset in range(4):
                grid = GEN.generate(7000, start + offset, difficulty=band)
                pairs.append({"input": grid, "output": _oracle(grid)})
            ranks = [_blue_rank(pair["input"]) for pair in pairs]
            assert set(ranks) == {0, 1, 2}
            assert any(GEN.SEMANTIC_WITNESSES["blue_between_extremes"](pair["input"]) for pair in pairs)
            assert any(GEN.SEMANTIC_WITNESSES["blue_not_median"](pair["input"]) for pair in pairs)
            for query_index, query in enumerate(pairs):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                for rival in GEN.SEMANTIC_RIVALS.values():
                    assert any(rival(pair["input"]) != pair["output"] for pair in demos)
                assert GEN.lesson_identifiable(demos, query) == []
