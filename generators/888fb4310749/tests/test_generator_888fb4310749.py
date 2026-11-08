from __future__ import annotations

import hashlib
import importlib
import json
import random
from collections import Counter
from pathlib import Path

import pytest


TASK = "888fb4310749"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "data/canonical/puzzles.jsonl"
BASE = ROOT / "data/base/solutions/training/fd4b2b02__888fb4310749.json"


def canonical_row():
    with CANONICAL.open() as handle:
        for line in handle:
            row = json.loads(line)
            if row["task_id"] == TASK:
                return row
    raise AssertionError("canonical row missing")


def canonical_pairs():
    row = canonical_row()
    return row["train"] + row["test"]


def independent_oracle(grid):
    height, width = len(grid), len(grid[0])
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    row0, row1 = min(r for r, _ in cells), max(r for r, _ in cells)
    col0, col1 = min(c for _, c in cells), max(c for _, c in cells)
    block_height, block_width = row1 - row0 + 1, col1 - col0 + 1
    step, color = block_height + block_width, grid[row0][col0]
    output = [row[:] for row in grid]

    def intersects(r, c, h, w):
        return r <= height - 1 and r + h - 1 >= 0 and c <= width - 1 and c + w - 1 >= 0

    def stamp(r, c, h, w, value):
        for rr in range(r, r + h):
            for cc in range(c, c + w):
                if 0 <= rr < height and 0 <= cc < width:
                    output[rr][cc] = value

    for multiple in range(-40, 41):
        for sign in (1, -1):
            diagonal_row = row0 + multiple * step
            diagonal_col = col0 + sign * multiple * step
            rotated_row = diagonal_row + block_height
            rotated_col = diagonal_col + (block_width if sign == 1 else -block_height)
            if intersects(rotated_row, rotated_col, block_width, block_height):
                stamp(rotated_row, rotated_col, block_width, block_height, 9 - color)
    anchors = []
    for multiple in range(-40, 41):
        for sign in (1, -1):
            anchor = row0 + multiple * step, col0 + sign * multiple * step
            if intersects(anchor[0], anchor[1], block_height, block_width) and anchor not in anchors:
                anchors.append(anchor)
    for row, col in anchors:
        stamp(row, col, block_height, block_width, color)
    return output


def frozen(grid):
    return tuple(map(tuple, grid))


def test_all_canonical_pairs_are_exact_and_strict():
    for profile, pair in zip(MODULE.PUBLIC_PROFILES, canonical_pairs()):
        grid = MODULE.generate(11, 17, scene_profile=profile)
        assert grid == pair["input"]
        assert MODULE.rule_mirror(grid) == independent_oracle(grid) == pair["output"]
        assert MODULE.canonical_profile_signature(grid) == profile
        assert MODULE.canonical_family_signature(grid) == profile
        assert MODULE.observe_overrides(grid) == {"scene_profile": profile}
        assert MODULE.self_check(grid) == []


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("profile", MODULE.GENERAL_PROFILES)
def test_every_general_profile_in_every_band(profile, difficulty):
    for seed in range(3):
        grid = MODULE.generate(20_000 + seed, seed * 19, difficulty=difficulty, scene_profile=profile)
        analysis = MODULE._analysis(grid)
        assert analysis["errors"] == []
        assert analysis["scene_profile"] == profile
        assert MODULE.observe_overrides(grid) == {"scene_profile": profile}
        assert MODULE.rule_mirror(grid) == independent_oracle(grid) == analysis["output"]


def test_profiles_are_geometrically_live_and_observable():
    for seed in range(20):
        facts = {profile: MODULE._analysis(MODULE.generate(seed, seed * 7, scene_profile=profile))["facts"] for profile in MODULE.GENERAL_PROFILES}
        assert facts["horizontal_bar"]["block_height"] == 1 < facts["horizontal_bar"]["block_width"]
        assert facts["vertical_bar"]["block_width"] == 1 < facts["vertical_bar"]["block_height"]
        assert facts["square_block"]["block_height"] == facts["square_block"]["block_width"] >= 2
        assert facts["corner_anchor"]["corner_anchor"]
        assert facts["edge_anchor"]["edge_count"] == 1
        assert facts["wide_block"]["block_width"] > facts["wide_block"]["block_height"] and not facts["wide_block"]["edge_count"]
        assert facts["tall_block"]["block_height"] > facts["tall_block"]["block_width"] and not facts["tall_block"]["edge_count"]


def test_all_source_colors_use_exact_nine_minus_complement():
    for color in range(1, 9):
        grid = MODULE._rect_grid(19, 21, 7, 8, 2, 3, color)
        output = MODULE.rule_mirror(grid)
        assert output == independent_oracle(grid)
        assert color in {value for row in output for value in row}
        assert 9 - color in {value for row in output for value in row}


def test_source_stamps_are_applied_after_rotated_stamps():
    for profile in MODULE.GENERAL_PROFILES:
        grid = MODULE.generate(71, len(profile), scene_profile=profile)
        facts = MODULE._analysis(grid)["facts"]
        output = MODULE.rule_mirror(grid)
        for row in range(facts["row0"], facts["row1"] + 1):
            for col in range(facts["col0"], facts["col1"] + 1):
                assert output[row][col] == facts["color"]


def test_edge_and_corner_profiles_create_clipped_boundary_stamps():
    for profile in ("corner_anchor", "edge_anchor"):
        for seed in range(20):
            grid = MODULE.generate(seed, seed * 13, scene_profile=profile)
            output = MODULE.rule_mirror(grid)
            facts = MODULE._analysis(grid)["facts"]
            assert facts["edge_count"]
            assert any(output[0][col] or output[-1][col] for col in range(len(output[0]))) or any(row[0] or row[-1] for row in output)
            assert output == independent_oracle(grid)


def test_public_nuisances_are_band_aware_and_nonliteral():
    literals = {frozen(pair["input"]) for pair in canonical_pairs()}
    for profile in MODULE.PUBLIC_PROFILES:
        for difficulty, low, high in (("easy", 10, 15), ("medium", 16, 22), ("hard", 23, 30)):
            scenes = [MODULE._public_nuisance(profile, difficulty, random.Random(seed)) for seed in range(40)]
            assert all(MODULE.canonical_family_signature(grid) == profile for grid in scenes)
            assert all(frozen(grid) not in literals for grid in scenes)
            assert all(low <= len(grid) <= high and low <= len(grid[0]) <= high for grid in scenes)
            assert len({frozen(grid) for grid in scenes}) >= 38


def test_broad_rule_accepts_bbox_semantics_while_training_gate_rejects_sparse_input():
    grid = [[0] * 12 for _ in range(11)]
    grid[2][3] = 4
    grid[6][8] = 4
    assert MODULE.rule_mirror(grid) == independent_oracle(grid)
    assert MODULE.self_check(grid)
    for block_height, block_width in ((1, 1), (2, 2), (1, 4)):
        minimal = MODULE._rect_grid(12, 12, 4, 4, block_height, block_width, 4)
        assert MODULE.rule_mirror(minimal) == independent_oracle(minimal)
        assert MODULE.self_check(minimal)


def test_default_distribution_is_complete_diverse_and_nontrivial():
    for difficulty in ("easy", "medium", "hard"):
        grids = [MODULE.generate(40_000 + seed, seed * 23, difficulty=difficulty) for seed in range(1400)]
        analyses = [MODULE._analysis(grid) for grid in grids]
        profiles = Counter(item["scene_profile"] for item in analyses)
        outputs = [MODULE.rule_mirror(grid) for grid in grids]
        colors = {item["facts"]["color"] for item in analyses}
        assert set(profiles) == set(MODULE.SCENE_PROFILES)
        assert all(count >= 30 for count in profiles.values())
        assert colors == set(range(1, 9))
        assert len({frozen(grid) for grid in grids}) >= 1380
        assert len({frozen(grid) for grid in outputs}) >= 1380
        assert all(grid != output for grid, output in zip(grids, outputs))


@pytest.mark.parametrize(
    "grid",
    [
        [],
        [[]],
        [[0] * 5 for _ in range(4)],
        [[False] * 5 for _ in range(5)],
        [[10] * 5 for _ in range(5)],
        [[0] * 5 for _ in range(5)],
        [[9] + [0] * 4 for _ in range(5)],
        [[2] * 5 for _ in range(5)],
    ],
)
def test_malformed_or_uncalibrated_inputs_fail_closed(grid):
    assert MODULE.self_check(grid)


def test_structural_mutations_fail_closed():
    grid = MODULE.generate(91, 7, scene_profile="wide_block")
    facts = MODULE._analysis(grid)["facts"]
    hole = [row[:] for row in grid]
    hole[facts["row0"]][facts["col0"]] = 0
    assert MODULE.self_check(hole)
    mixed = [row[:] for row in grid]
    mixed[facts["row1"]][facts["col1"]] = 8 if facts["color"] != 8 else 7
    assert MODULE.self_check(mixed)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"scene_profile": "unknown"},
        {"texture": "no_rect"},
        {"grid_h": 16},
        {"rect_size": "2x3"},
        {"color": 3},
        {"difficulty": "expert"},
    ],
)
def test_unknown_controls_fail_closed(kwargs):
    with pytest.raises(ValueError):
        MODULE.generate(1, 0, **kwargs)


def test_determinism_fresh_returns_and_global_rng_isolation():
    random.seed(9157)
    state = random.getstate()
    first = MODULE.generate(101, 13, difficulty="hard", scene_profile="corner_anchor")
    assert random.getstate() == state
    second = MODULE.generate(101, 13, difficulty="hard", scene_profile="corner_anchor")
    assert first == second and first is not second and first[0] is not second[0]
    first[0][0] = 9
    assert MODULE.generate(101, 13, difficulty="hard", scene_profile="corner_anchor") == second


def test_axis_contract_is_literal_minimal_and_fully_observable():
    assert set(MODULE.AXES) == {"scene_profile"}
    assert tuple(MODULE.AXES["scene_profile"]["valid"].split("|")) == MODULE.SCENE_PROFILES
    assert MODULE.HELPFUL_TEXTURES == MODULE.DEGENERATE_TEXTURES == ()


def test_rule_hash_base_sources_and_rare_primitive_authority():
    source = canonical_row()["program_solution"]
    digest = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
    assert MODULE.RULE_HASH == digest == "2e44fadee3f2"
    base = json.loads(BASE.read_text())
    assert base["racket_target"]["raw_code"] == source
    assert base["racket_target"]["target_code"] == source
    prelude = (ROOT / "arc_repl/racket_prelude/arc-prelude.rkt").read_text()
    helpers = (ROOT / "arc_repl/racket_prelude/bank-helpers.rkt").read_text()
    assert "(define (positions-of g pred)" in prelude
    assert "(define (sgn x)" in helpers
