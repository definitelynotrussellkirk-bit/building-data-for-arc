from __future__ import annotations

import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest


TASK = "5f8abe24cffe"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/base/solutions/banks/edd0efb19ea0/H86__5f8abe24cffe.json"


def canonical_row():
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            return row
    raise AssertionError("canonical row missing")


def normalize(grid):
    return [[int(value) for value in row] if isinstance(row, str) else list(row) for row in grid]


def canonical_pairs():
    row = canonical_row()
    return row["train"] + [row["test"]]


def independent_transform(grid, code):
    if code == 1:
        return [row[:] for row in grid]
    if code == 2:
        return [list(row) for row in zip(*grid[::-1])]
    if code == 3:
        return [row[::-1] for row in grid[::-1]]
    if code == 4:
        return [list(row) for row in zip(*grid)]
    if code == 5:
        return [row[::-1] for row in grid]
    return grid[::-1]


def independent_frames(grid):
    height, width = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(height) for c in range(width) if grid[r][c] == 1}
    frames = []
    while unseen:
        start = unseen.pop()
        cells = {start}
        frontier = [start]
        while frontier:
            row, col = frontier.pop()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                neighbour = row + dr, col + dc
                if neighbour in unseen:
                    unseen.remove(neighbour)
                    cells.add(neighbour)
                    frontier.append(neighbour)
        row0, row1 = min(r for r, _ in cells), max(r for r, _ in cells)
        col0, col1 = min(c for _, c in cells), max(c for _, c in cells)
        border = {
            (r, c)
            for r in range(row0, row1 + 1)
            for c in range(col0, col1 + 1)
            if r in (row0, row1) or c in (col0, col1)
        }
        if len({row0, row1}) > 1 and len({col0, col1}) > 1 and cells == border:
            frames.append((row0, col0, row1, col1))
    return sorted(frames)


def independent_crop(grid):
    nonzero = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    if not nonzero:
        return []
    row0, row1 = min(r for r, _ in nonzero), max(r for r, _ in nonzero)
    col0, col1 = min(c for _, c in nonzero), max(c for _, c in nonzero)
    return [row[col0 : col1 + 1] for row in grid[row0 : row1 + 1]]


def independent_oracle(grid):
    frames = independent_frames(grid)
    if len(frames) < 3:
        return [[0]], None, []
    panels = []
    for row0, col0, row1, col1 in frames[:3]:
        interior = [row[col0 + 1 : col1] for row in grid[row0 + 1 : row1]]
        panels.append(independent_crop(interior))
    code = next((value for value in range(1, 7) if independent_transform(panels[0], value) == panels[1]), 1)
    return independent_transform(panels[2], code), code, panels


def frozen(grid):
    return tuple(tuple(row) for row in grid)


@pytest.mark.parametrize("index,profile", list(enumerate(MODULE.PUBLIC_PROFILES)))
def test_exact_public_replay(index, profile):
    pair = canonical_pairs()[index]
    expected_input, expected_output = normalize(pair["input"]), normalize(pair["output"])
    grid = MODULE.generate(100 + index, index, scene_profile=profile)
    oracle, code, _ = independent_oracle(grid)
    assert grid == expected_input
    assert MODULE.rule_mirror(grid) == expected_output == oracle
    assert MODULE._analysis(grid)["facts"]["transform_code"] == code
    assert MODULE.canonical_profile_signature(grid) == profile
    assert MODULE.observe_overrides(grid) == {"scene_profile": profile}


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("profile", MODULE.GENERAL_PROFILES)
def test_every_general_profile_in_every_difficulty(profile, difficulty):
    grid = MODULE.generate(20_000 + len(profile), 7, difficulty=difficulty, scene_profile=profile)
    analysis = MODULE._analysis(grid)
    oracle, code, panels = independent_oracle(grid)
    expected_code = int(profile[4:])
    assert analysis["errors"] == []
    assert analysis["scene_profile"] == profile
    assert analysis["facts"]["transform_code"] == code == expected_code
    assert analysis["facts"]["layout"] in {"staircase", "row", "column"}
    assert analysis["output"] == MODULE.rule_mirror(grid) == oracle
    assert all(MODULE._connected_content(panel) for panel in panels)
    assert MODULE.observe_overrides(grid) == {"scene_profile": profile}


@pytest.mark.parametrize("code", range(1, 7))
def test_each_transform_independently_crosses_every_layout(code):
    layouts = set()
    for seed in range(80):
        grid = MODULE.generate(40_000 + code * 100 + seed, seed, difficulty="hard", scene_profile=f"code{code}")
        facts = MODULE._analysis(grid)["facts"]
        assert facts["transform_code"] == code
        assert len(facts["frames"]) == 3
        assert all(3 <= height <= 7 and 3 <= width <= 7 for height, width in facts["frame_shapes"])
        layouts.add(facts["layout"])
        if code != 1:
            c_panel = [list(row) for row in facts["inner"][2]]
            assert MODULE._transform(c_panel, code) != c_panel
    assert layouts == {"staircase", "row", "column"}


def test_first_match_precedence_selects_identity_for_symmetric_equal_panels():
    symmetric = [[2, 2], [2, 2]]
    assert all(MODULE._transform(symmetric, code) == symmetric for code in range(1, 7))
    assert MODULE._first_transform(symmetric, symmetric) == 1


def test_crop_to_content_removes_frame_padding_before_inference():
    witnessed = False
    for seed in range(100):
        grid = MODULE.generate(50_000 + seed, seed, scene_profile="code2")
        facts = MODULE._analysis(grid)["facts"]
        for frame_shape, inner_shape in zip(facts["frame_shapes"], facts["inner_shapes"]):
            if frame_shape[0] - 2 > inner_shape[0] or frame_shape[1] - 2 > inner_shape[1]:
                witnessed = True
                break
        if witnessed:
            break
    assert witnessed


def test_identity_is_a_valid_analogy_not_a_ruleless_degenerate():
    grid = MODULE.generate(61, 2, scene_profile="code1")
    facts = MODULE._analysis(grid)["facts"]
    query = [list(row) for row in facts["inner"][2]]
    assert facts["transform_code"] == 1
    assert MODULE.rule_mirror(grid) == query
    assert MODULE.rule_mirror(grid) != grid


def test_determinism_fresh_returns_and_global_rng_independence():
    random.seed(991)
    state = random.getstate()
    first = MODULE.generate(73, 6, difficulty="medium", scene_profile="code6")
    assert random.getstate() == state
    second = MODULE.generate(73, 6, difficulty="medium", scene_profile="code6")
    assert first == second and first is not second and first[0] is not second[0]
    first[0][0] = 9
    assert MODULE.generate(73, 6, difficulty="medium", scene_profile="code6") == second


def test_generated_pool_has_high_scene_output_and_shape_diversity():
    grids = [MODULE.generate(seed, seed + 3) for seed in range(200)]
    outputs = [MODULE.rule_mirror(grid) for grid in grids]
    assert len({frozen(grid) for grid in grids}) >= 185
    assert len({frozen(output) for output in outputs}) >= 175
    assert len({(len(grid), len(grid[0])) for grid in grids}) >= 35
    assert len({(len(output), len(output[0])) for output in outputs}) >= 12


@pytest.mark.parametrize(
    "grid",
    [
        [],
        [[]],
        [[0] * 3 for _ in range(2)],
        [[0] * 31 for _ in range(3)],
        [[0] * 3 for _ in range(31)],
        [[0] * 4 for _ in range(3)] + [[0] * 3],
        [[False] * 3 for _ in range(3)],
        [[10] * 3 for _ in range(3)],
    ],
)
def test_malformed_grids_fail_closed(grid):
    assert MODULE.self_check(grid)
    with pytest.raises(ValueError):
        MODULE.rule_mirror(grid)


def test_valid_grid_without_three_frames_uses_canonical_fallback_but_fails_training_check():
    blank = [[0] * 5 for _ in range(5)]
    assert MODULE.rule_mirror(blank) == [[0]]
    assert MODULE.self_check(blank)


def test_semantic_mutations_fail_closed():
    grid = MODULE.generate(89, 9, scene_profile="code4")
    facts = MODULE._analysis(grid)["facts"]

    broken_frame = [row[:] for row in grid]
    row0, col0, _, _ = facts["frames"][0]
    broken_frame[row0][col0] = 0
    assert MODULE.self_check(broken_frame)

    empty_c = [row[:] for row in grid]
    row0, col0, row1, col1 = facts["frames"][2]
    for row in range(row0 + 1, row1):
        for col in range(col0 + 1, col1):
            empty_c[row][col] = 0
    assert MODULE.self_check(empty_c)

    outside = [row[:] for row in grid]
    location = next((r, c) for r, row in enumerate(outside) for c, value in enumerate(row) if value == 0)
    outside[location[0]][location[1]] = 9
    assert MODULE.self_check(outside)

    wrong_palette = [row[:] for row in grid]
    row0, col0, row1, col1 = facts["frames"][2]
    location = next((r, c) for r in range(row0 + 1, row1) for c in range(col0 + 1, col1) if wrong_palette[r][c] != 0)
    wrong_palette[location[0]][location[1]] = 1
    assert MODULE.self_check(wrong_palette)


@pytest.mark.parametrize("kwargs", [{"scene_profile": "unknown"}, {"texture": "identity_transform"}, {"difficulty": "expert"}])
def test_unknown_controls_fail_closed(kwargs):
    with pytest.raises(ValueError):
        MODULE.generate(1, 0, **kwargs)


def test_axis_contract_is_literal_and_minimal():
    assert set(MODULE.AXES) == {"scene_profile"}
    assert tuple(MODULE.AXES["scene_profile"]["valid"].split("|")) == MODULE.SCENE_PROFILES
    assert MODULE.HELPFUL_TEXTURES == MODULE.DEGENERATE_TEXTURES == ()


def test_rule_hash_and_base_sources_are_exactly_synchronized():
    source = canonical_row()["program_solution"]
    digest = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
    assert MODULE.RULE_HASH == digest == "634d31594fbf"
    base = json.loads(BASE.read_text())
    assert base["racket_target"]["raw_code"] == source
    assert base["racket_target"]["target_code"] == source
