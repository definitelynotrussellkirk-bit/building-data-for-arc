"""Focused semantic tests for the 9b6d928388be keyed-hole generator."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from collections import Counter
from pathlib import Path

import pytest
from reviewer_support import canonical_path, find_root


gen = importlib.import_module(
    "puzzle_generators.per_puzzle.9b6d928388be.generator"
)

ROOT = find_root(__file__)
CANONICAL = canonical_path(ROOT)
BASE = (
    ROOT
    / "shared/data/base/solutions/banks/d994e8798bff/hard_p03__9b6d928388be.json"
)


def _canonical_row():
    rows = [
        json.loads(line)
        for line in CANONICAL.read_text().splitlines()
        if json.loads(line).get("task_id") == gen.TASK_ID
    ]
    assert len(rows) == 1
    return rows[0]


def _canonical_pairs():
    row = _canonical_row()
    return row["train"] + row["test"]


def _key(grid):
    return tuple(map(tuple, grid))


def _independent_components(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            seen.add((row, col))
            stack = [(row, col)]
            cells = set()
            while stack:
                point = stack.pop()
                cells.add(point)
                r, c = point
                for neighbor in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                    nr, nc = neighbor
                    if (
                        0 <= nr < height and 0 <= nc < width
                        and neighbor not in seen and grid[nr][nc] == color
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            result.append((color, cells))
    return result


def _independent_bbox(cells):
    return (
        min(row for row, _ in cells), max(row for row, _ in cells),
        min(col for _, col in cells), max(col for _, col in cells),
    )


def _independent_border(bbox):
    top, bottom, left, right = bbox
    return {
        (row, col)
        for row in range(top, bottom + 1)
        for col in range(left, right + 1)
        if row in (top, bottom) or col in (left, right)
    }


def _independent_holes(cells):
    top, bottom, left, right = _independent_bbox(cells)
    free = {
        (row, col)
        for row in range(top, bottom + 1)
        for col in range(left, right + 1)
        if (row, col) not in cells
    }
    seen = set()
    holes = 0
    for start in free:
        if start in seen:
            continue
        seen.add(start)
        stack = [start]
        touches = False
        while stack:
            row, col = stack.pop()
            touches |= row in (top, bottom) or col in (left, right)
            for neighbor in ((row + 1, col), (row - 1, col),
                             (row, col + 1), (row, col - 1)):
                if neighbor in free and neighbor not in seen:
                    seen.add(neighbor)
                    stack.append(neighbor)
        holes += int(not touches)
    return holes


def _independent_floor_half(value):
    return value // 2


def _independent_oracle(grid):
    """Reimplement the executable rule without any generator helper."""
    frame_boxes = []
    for color, cells in _independent_components(grid):
        bbox = _independent_bbox(cells)
        if color == 5 and cells == _independent_border(bbox):
            frame_boxes.append(bbox)
    frame_boxes.sort()
    temp = copy.deepcopy(grid)
    for top, bottom, left, right in frame_boxes:
        for row, col in _independent_border((top, bottom, left, right)):
            temp[row][col] = 0
        temp[top - 1][(left + right) // 2] = 0
    loose = _independent_components(temp)
    output = [[0] * len(grid[0]) for _ in grid]
    for bbox in frame_boxes:
        for row, col in _independent_border(bbox):
            output[row][col] = 5
    for top, bottom, left, right in frame_boxes:
        key_col = (left + right) // 2
        key = grid[top - 1][key_col]
        output[top - 1][key_col] = key
        candidates = [entry for entry in loose if _independent_holes(entry[1]) == key - 1]
        color, cells = max(candidates, key=lambda entry: len(entry[1]))
        obj_top, obj_bottom, obj_left, obj_right = _independent_bbox(cells)
        crop_height = obj_bottom - obj_top + 1
        crop_width = obj_right - obj_left + 1
        paste_top = top + 1 + _independent_floor_half(
            bottom - top - 1 - crop_height
        )
        paste_left = left + 1 + _independent_floor_half(
            right - left - 1 - crop_width
        )
        for row, col in cells:
            output[paste_top + row - obj_top][paste_left + col - obj_left] = color
    return output


def test_identity_rule_hash_and_catalog_dimensions():
    assert gen.GENERATOR_ID == gen.TASK_ID == "9b6d928388be"
    assert gen.VERSION == "4.0.0"
    assert gen.RULE_HASH == "71c56654a6ea"
    assert gen.PATTERN_COUNTS == (256, 256, 78)
    assert (gen.LAYOUT_COUNT, gen.KEY_COUNT, gen.PALETTE_COUNT) == (128, 6, 100)
    assert gen.SCENE_COUNT == 392_586_854_400
    normalized = " ".join(_canonical_row()["program_solution"].split())
    assert hashlib.sha256(normalized.encode()).hexdigest()[:12] == gen.RULE_HASH


def test_canonical_inventory_is_one_row_four_unique_occurrences():
    row = _canonical_row()
    pairs = _canonical_pairs()
    assert row["source"] == "bank:d994e8798bff"
    assert len(row["train"]) == 3 and len(row["test"]) == 1
    assert len(pairs) == len({_key(pair["input"]) for pair in pairs}) == 4
    assert {gen.canonical_profile_signature(pair["input"]) for pair in pairs} == set(
        gen.PUBLIC_PROFILES
    )


@pytest.mark.parametrize("pair", _canonical_pairs())
def test_every_canonical_pair_matches_two_independent_executors(pair):
    original = copy.deepcopy(pair["input"])
    assert _independent_oracle(pair["input"]) == pair["output"]
    assert gen.rule_mirror(pair["input"]) == pair["output"]
    assert gen.self_check(pair["input"]) == []
    assert pair["input"] == original


@pytest.mark.parametrize("index", range(4))
def test_public_profiles_reconstruct_exact_canonical_inputs(index):
    pair = _canonical_pairs()[index]
    public = gen._public_grid(index)
    assert public == pair["input"]
    assert gen._grid_from_code(gen._public_code(index)) == public
    assert gen.observe_overrides(public) == {"scene_code": gen._public_code(index)}
    assert gen.rule_mirror(public) == pair["output"]


def test_topology_banks_are_unique_connected_and_exact():
    for holes, bank in enumerate(gen.PATTERN_BANKS):
        assert len(bank) == len(set(bank)) == gen.PATTERN_COUNTS[holes]
        assert all(gen._connected(pattern) for pattern in bank)
        assert all(gen._pattern_holes(pattern) == holes for pattern in bank)
    assert len(gen.GRAY_ZERO_PATTERNS) == len(set(gen.GRAY_ZERO_PATTERNS)) == 256
    assert all(gen._connected(pattern) for pattern in gen.GRAY_ZERO_PATTERNS)
    assert all(gen._pattern_holes(pattern) == 0 for pattern in gen.GRAY_ZERO_PATTERNS)
    assert not any(gen._rect_outline_pattern(pattern) for pattern in gen.GRAY_ZERO_PATTERNS)


def test_palette_bank_is_complete_and_gray_role_is_safe():
    assert len(gen.PALETTES) == len(set(gen.PALETTES)) == 100
    assert all(len(set(palette)) == 3 for palette in gen.PALETTES)
    assert all(set(palette) <= {4, 5, 6, 7, 8, 9} for palette in gen.PALETTES)
    assert all(palette[1] != 5 for palette in gen.PALETTES)
    assert any(palette[0] == 5 for palette in gen.PALETTES)
    assert any(palette[2] == 5 for palette in gen.PALETTES)


@pytest.mark.parametrize(
    "code",
    (0, 1, 77, 78, 19_967, 19_968, 1_000_003, 392_586_854_399),
)
def test_scene_codes_round_trip_exactly(code):
    decoded = gen._decode_scene(code)
    assert gen._encode_scene(*decoded) == code
    grid = gen._grid_from_code(code)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == {"scene_code": code}
    assert gen.rule_mirror(grid) == _independent_oracle(grid)


@pytest.mark.parametrize("band", (None, "easy", "medium", "hard"))
def test_natural_1000_sample_lanes_are_unique_balanced_and_valid(band):
    grids = [gen.generate(17, index, difficulty=band) for index in range(1000)]
    outputs = [gen.rule_mirror(grid) for grid in grids]
    assert len({_key(grid) for grid in grids}) == 1000
    assert len({_key(grid) for grid in outputs}) == 1000
    assert all(gen.self_check(grid) == [] for grid in grids)
    facts = [gen._analysis(grid)["facts"] for grid in grids]
    assert {fact["layout_family"] for fact in facts} == {
        "size_15x24", "size_15x25", "size_16x24", "size_16x25"
    }
    assert len({fact["layout_index"] for fact in facts}) >= 120
    assert set(fact["keys"] for fact in facts) == set(gen.KEY_PERMUTATIONS)
    assert len({fact["palette"] for fact in facts}) >= 95
    assert all(fact["component_count"] == 9 for fact in facts)


def test_difficulty_bands_shift_shape_complexity():
    scores = {}
    for band in ("easy", "medium", "hard"):
        total = 0
        for index in range(500):
            grid = gen.generate(81, index, difficulty=band)
            facts = gen._analysis(grid)["facts"]
            palette = facts["palette"]
            indexes = facts["pattern_indexes"]
            zero_bank = gen.GRAY_ZERO_PATTERNS if palette[0] == 5 else gen.ZERO_PATTERNS
            patterns = (
                zero_bank[indexes[0]], gen.ONE_PATTERNS[indexes[1]],
                gen.TWO_PATTERNS[indexes[2]],
            )
            total += sum(
                len(pattern) * len(pattern[0]) - sum(map(sum, pattern))
                for pattern in patterns
            )
        scores[band] = total / 500
    assert scores["easy"] < scores["medium"] < scores["hard"]


@pytest.mark.parametrize(
    "counter",
    (
        lambda index: (90_000 + index, 0),
        lambda index: (90_000, index),
        lambda index: (90_000 + index, 90_000 + index),
    ),
)
def test_seed_only_sample_only_and_joint_streams_do_not_collapse(counter):
    inputs = set()
    outputs = set()
    families = set()
    keys = set()
    for index in range(600):
        seed, sample_index = counter(index)
        grid = gen.generate(seed, sample_index, difficulty="medium")
        facts = gen._analysis(grid)["facts"]
        inputs.add(_key(grid))
        outputs.add(_key(gen.rule_mirror(grid)))
        families.add(facts["layout_family"])
        keys.add(facts["keys"])
    assert len(inputs) == len(outputs) == 600
    assert families == {"size_15x24", "size_15x25", "size_16x24", "size_16x25"}
    assert keys == set(gen.KEY_PERMUTATIONS)


def test_multi_pair_episode_schedule_is_unique():
    inputs = set()
    outputs = set()
    for episode in range(50):
        for local_index in range(8):
            grid = gen.generate(93_000 + episode, local_index)
            inputs.add(_key(grid))
            outputs.add(_key(gen.rule_mirror(grid)))
    assert len(inputs) == len(outputs) == 400


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    first = gen.generate(5, 77)
    second = gen.generate(5, 77)
    assert first == second and first is not second and first[0] is not second[0]
    assert gen.generate(5, 77) != gen.generate(6, 77)
    assert gen.generate(5, 77) != gen.generate(5, 78)
    before = random.getstate()
    gen.generate(11, 13, difficulty="hard")
    assert random.getstate() == before


def test_rule_mirror_is_input_pure():
    for code in (0, gen._public_code(3), gen.SCENE_COUNT - 1):
        grid = gen._grid_from_code(code)
        original = copy.deepcopy(grid)
        assert gen.rule_mirror(grid) == _independent_oracle(grid)
        assert grid == original


@pytest.mark.parametrize(
    "mutator",
    (
        lambda grid: grid.__setitem__(0, grid[0][:-1]),
        lambda grid: grid[1].__setitem__(14, 0),
        lambda grid: grid[1].__setitem__(14, 2),
        lambda grid: grid[2].__setitem__(12, 0),
        lambda grid: grid[0].__setitem__(0, 4),
        lambda grid: grid[2].__setitem__(1, 3),
    ),
)
def test_structural_mutations_are_rejected(mutator):
    grid = gen._public_grid(0)
    mutator(grid)
    assert gen.self_check(grid)


@pytest.mark.parametrize("bad", (-1, gen.SCENE_COUNT, 1.5, True, "3"))
def test_invalid_scene_code_overrides_fail_loudly(bad):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, scene_code=bad)


def test_unknown_override_and_difficulty_fail_loudly():
    with pytest.raises(ValueError):
        gen.generate(0, 0, mystery=1)
    with pytest.raises(ValueError):
        gen.generate(0, 0, difficulty="extreme")


def test_packaged_base_and_canonical_are_synchronized():
    # The portable review packet intentionally omits the mutable custom-bank
    # index and derived stale-source ledger.  Bind the test to the two packaged
    # authorities instead: canonical JSONL and the immutable base solution.
    canonical = _canonical_row()
    rule = canonical["program_solution"]
    base = json.loads(BASE.read_text())
    assert base["racket_target"]["raw_code"] == rule
    assert base["racket_target"]["target_code"] == rule
    description = base["description_target"]
    assert description["source"] == "canonical.written_solution"
    assert description["target_status"] == "source_written"
    assert len(description["solution_steps"]) == 5
    assert len(description["negative_constraints"]) == 4
    assert "k-1 enclosed holes" in description["solution_steps"][3]


def test_forced_scene_outputs_are_nontrivial_and_nonconstant():
    outputs = []
    for index in range(4):
        grid = gen._public_grid(index)
        output = gen.rule_mirror(grid)
        assert output != grid
        assert {1, 2, 3, 5} <= {value for row in output for value in row}
        outputs.append(_key(output))
    assert len(set(outputs)) == 4
