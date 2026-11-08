from __future__ import annotations

import copy
import hashlib
import json
import random
from collections import Counter

import pytest

from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
)


ROOT = find_root(__file__)
gen, _, _ = load_selected_generator("f0f2806877da", root=ROOT)
DATA_ROOT = canonical_path(ROOT).parent.parent
BASE_PATHS = (
    DATA_ROOT / "base/solutions/training/e6de6e8f__f0f2806877da.json",
    DATA_ROOT / "base/solutions/augmented/e6de6e8f__42600214d4ed.json",
)


def _canonical_rows():
    rows = []
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                rows.append(row)
    return rows


def _canonical_pairs():
    return canonical_pairs(gen.TASK_ID, root=ROOT)


def _independent_types(grid):
    gaps = [grid[0][col] == grid[1][col] == 0 for col in range(len(grid[0]))]
    types = []
    col = 0
    while col < len(gaps):
        while col < len(gaps) and gaps[col]:
            col += 1
        if col == len(gaps):
            break
        start = col
        while col + 1 < len(gaps) and not gaps[col + 1]:
            col += 1
        types.append(0 if col == start else 1 if grid[0][start] == 0 else 2)
        col += 1
    return tuple(types)


def _independent_oracle(grid):
    row, col = 1, 3
    cells = []
    for piece_type in _independent_types(grid):
        if piece_type == 0:
            cells.extend(((row, col), (row + 1, col)))
            row += 2
        elif piece_type == 1:
            cells.extend(((row, col - 1), (row, col)))
            row += 1
            col -= 1
        else:
            cells.extend(((row, col), (row, col + 1)))
            row += 1
            col += 1
    output = [[0] * 7 for _ in range(8)]
    output[0][3] = 3
    for r, c in cells:
        if 0 <= r < 8 and 0 <= c < 7:
            output[r][c] = 2
    return output


def _key(grid):
    return tuple(tuple(row) for row in grid)


def test_identity_version_and_rule_hash_pin():
    assert gen.GENERATOR_ID == gen.TASK_ID == "f0f2806877da"
    assert gen.VERSION == "3.0.0"
    assert gen.EXPECTED_OUTPUT_CODOMAIN == 80
    rules = {" ".join(row["program_solution"].split()) for row in _canonical_rows()}
    assert len(rules) == 1
    assert hashlib.sha256(next(iter(rules)).encode()).hexdigest()[:12] == gen.RULE_HASH


def test_both_base_records_match_canonical_rule_and_explain_the_parser():
    rules = {row["program_solution"] for row in _canonical_rows()}
    assert len(rules) == 1
    rule = next(iter(rules))
    expected_primitives = [
        "rows", "cols", "at", "filter", "range", "map", "nth",
        "first", "second", "reduce", "third", "build-grid",
    ]
    for path in BASE_PATHS:
        base = json.loads(path.read_text(encoding="utf-8"))
        target = base["racket_target"]
        assert target["raw_code"] == target["target_code"]
        assert " ".join(target["target_code"].split()) == " ".join(rule.split())
        assert base["primitive_metadata"]["primitive_chain"] == expected_primitives
        description = base["description_target"]
        assert description["target_status"] == "source_written"
        text = description["target_text"]
        assert "zero in both rows" in text
        assert "upper-left cell" in text
        assert "fixed 8x7" in text
        assert "row 1, column 3" in text
        constraints = " ".join(description["negative_constraints"])
        assert "only one of its two cells is zero" in constraints
        assert "every traced path cell is red 2" in constraints


def test_canonical_inventory_has_two_rows_eight_occurrences_and_four_inputs():
    rows = _canonical_rows()
    pairs = _canonical_pairs()
    assert {row["source"] for row in rows} == {"training", "augmented"}
    assert len(rows) == 2
    assert len(pairs) == 8
    assert len({_key(pair["input"]) for pair in pairs}) == 4
    assert {gen.canonical_profile_signature(pair["input"]) for pair in pairs} == set(gen.PUBLIC_PROFILES)


@pytest.mark.parametrize("pair", _canonical_pairs())
def test_every_canonical_occurrence_matches_independent_oracle(pair):
    original = copy.deepcopy(pair["input"])
    assert _independent_oracle(pair["input"]) == pair["output"]
    assert gen.rule_mirror(pair["input"]) == pair["output"]
    assert pair["input"] == original
    assert gen.self_check(pair["input"]) == []


def test_exhaustive_grammar_counts_and_uniqueness():
    assert len(gen.TYPE_SEQUENCES) == 80
    assert len(gen.ENCODINGS) == 16970
    assert len(set(gen.ENCODINGS)) == 16970
    assert len(gen.PUBLIC_CODES) == 1500
    assert len(gen.GENERAL_CODES) == 15470
    assert set(gen.PUBLIC_CODES).isdisjoint(gen.GENERAL_CODES)
    assert set(gen.PUBLIC_CURRICULUM) == set(gen.PUBLIC_CODES)
    assert set(gen.GENERAL_CURRICULUM) == set(gen.GENERAL_CODES)


def test_every_exhaustive_encoding_is_valid_and_observable():
    for code, encoding in enumerate(gen.ENCODINGS):
        grid = [list(row) for row in encoding]
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid) == {"encoding_code": code}
        assert gen.rule_mirror(grid) == _independent_oracle(grid)


@pytest.mark.parametrize("code", [0, 1, 2, 8485, 16968, 16969])
def test_explicit_encoding_codes_are_exact(code):
    grid = gen.generate(1000 + code, code, encoding_code=code)
    assert _key(grid) == gen.ENCODINGS[code]
    assert gen.observe_overrides(grid) == {"encoding_code": code}


def test_all_eighty_type_sequences_and_outputs_are_reachable():
    seen_types = set()
    outputs = set()
    for code, types in enumerate(gen.ENCODING_TYPES):
        seen_types.add(types)
        outputs.add(_key(gen.rule_mirror([list(row) for row in gen.ENCODINGS[code]])))
    assert seen_types == set(gen.TYPE_SEQUENCES)
    assert len(outputs) == gen.EXPECTED_OUTPUT_CODOMAIN


def test_first_144_natural_probe_pairs_cover_three_quarters_of_output_codomain():
    outputs = {
        _key(gen.rule_mirror(gen.generate(index // 6, index, difficulty="medium")))
        for index in range(144)
    }
    assert len(outputs) >= 60


def test_linter_seed_pattern_covers_more_than_one_third_of_pair_outputs():
    outputs = {
        _key(gen.rule_mirror(gen.generate(episode * 101, sample_index)))
        for episode in range(24)
        for sample_index in range(6)
    }
    assert len(outputs) >= 51


def test_diversity_probe_seed_pattern_has_unique_inputs_and_broad_paths():
    grids = [
        gen.generate(1 + episode * 101, sample_index)
        for episode in range(50)
        for sample_index in range(6)
    ]
    assert len({_key(grid) for grid in grids}) == 300
    assert len({_independent_types(grid) for grid in grids}) >= 70


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_equal_counter_stream_has_5000_unique_inputs_and_exact_public_rate(difficulty):
    grids = [gen.generate(index, index, difficulty=difficulty) for index in range(5000)]
    assert len({_key(grid) for grid in grids}) == 5000
    assert sum(gen.canonical_family_signature(grid) is not None for grid in grids) == 1000
    profiles = Counter(gen.canonical_family_signature(grid) for grid in grids)
    assert [profiles[profile] for profile in gen.PUBLIC_PROFILES] == [244, 244, 268, 244]


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_fixed_seed_stream_has_5000_unique_inputs_and_exact_public_rate(difficulty):
    grids = [gen.generate(7000, index, difficulty=difficulty) for index in range(5000)]
    assert len({_key(grid) for grid in grids}) == 5000
    assert sum(gen.canonical_family_signature(grid) is not None for grid in grids) == 1000
    profiles = Counter(gen.canonical_family_signature(grid) for grid in grids)
    assert [profiles[profile] for profile in gen.PUBLIC_PROFILES] == [244, 244, 268, 244]


def test_four_band_health_stream_is_globally_unique():
    grids = []
    for band_index, difficulty in enumerate((None, "easy", "medium", "hard")):
        for index in range(1000):
            grids.append(gen.generate(band_index * 100000 + index, index, difficulty=difficulty))
    assert len({_key(grid) for grid in grids}) == 4000


def test_generated_distribution_matches_official_shape_palette_and_density():
    for index in range(400):
        grid = gen.generate(index, index, difficulty="medium")
        assert (len(grid), len(grid[0])) == (2, 12)
        assert {value for row in grid for value in row} == {0, 2}
        assert 12 <= sum(value == 2 for row in grid for value in row) <= 16
        facts = gen._analysis(grid)["facts"]
        assert len(facts["pieces"]) == 5
        assert facts["types"].count(gen.STRAIGHT) == 2


def test_piece_pattern_banks_cover_nonfunctional_cell_variation():
    assert {kind: len(bank) for kind, bank in gen.PIECE_PATTERNS.items()} == {0: 3, 1: 3, 2: 6}
    for kind, bank in gen.PIECE_PATTERNS.items():
        for pattern in bank:
            top, bottom, _ = pattern
            grid = [list(top), list(bottom)]
            assert _independent_types(grid) == (kind,)


def test_official_family_is_decoded_sequence_not_exact_pixel_memorization():
    for profile, types in zip(gen.PUBLIC_PROFILES, gen.PUBLIC_TYPES):
        codes = [code for code in gen.PUBLIC_CODES if gen.ENCODING_TYPES[code] == types]
        variants = [gen.ENCODINGS[code] for code in codes]
        assert len(variants) > 50
        assert len({sum(value != 0 for row in grid for value in row) for grid in variants}) >= 2
        assert all(gen.canonical_family_signature([list(row) for row in grid]) == profile for grid in variants)


def test_determinism_fresh_returns_and_global_rng_isolation():
    random.seed(77124)
    state = random.getstate()
    first = gen.generate(8000, 23, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(8000, 23, difficulty="hard")
    assert first == second
    assert first is not second
    first[0][0] = 0 if first[0][0] else 2
    assert gen.generate(8000, 23, difficulty="hard") == second


@pytest.mark.parametrize("bad", [
    [],
    [[]],
    [[0] * 12],
    [[0] * 11, [0] * 11],
    [[0] * 13, [0] * 13],
    [[False] * 12, [False] * 12],
    [[3] * 12, [3] * 12],
    [[10] * 12, [10] * 12],
])
def test_structurally_invalid_grids_fail_closed(bad):
    assert gen.self_check(bad)


@pytest.mark.parametrize("bad", [
    [[0] * 12, [0] * 12],
    [[2] * 12, [2] * 12],
    [[0] * 12, [2] + [0] * 11],
    [[2, 2] + [0] * 10, [2, 2] + [0] * 10],
    [[2 if col % 2 == 0 else 0 for col in range(12)]] * 2,
])
def test_semantic_impostors_fail_closed(bad):
    assert gen.self_check(bad)


def test_density_below_calibrated_floor_fails_closed():
    grid = [list(row) for row in gen.ENCODINGS[0]]
    removed = False
    for row in range(2):
        for col in range(12):
            if grid[row][col] == 2:
                candidate = copy.deepcopy(grid)
                candidate[row][col] = 0
                if _independent_types(candidate) == _independent_types(grid):
                    grid = candidate
                    removed = True
                    if sum(value == 2 for values in grid for value in values) < 12:
                        break
        if sum(value == 2 for values in grid for value in values) < 12:
            break
    assert removed
    assert gen.self_check(grid)


@pytest.mark.parametrize("overrides", [
    {"encoding_code": -1},
    {"encoding_code": len(gen.ENCODINGS)},
    {"unknown": 1},
])
def test_invalid_controls_raise(overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(9000, 0, **overrides)


def test_unknown_difficulty_raises():
    with pytest.raises(ValueError):
        gen.generate(9001, 0, difficulty="extreme")


def test_rule_mirror_rejects_blank_and_preserves_input():
    blank = [[0] * 12 for _ in range(2)]
    with pytest.raises(ValueError):
        gen.rule_mirror(blank)
    grid = gen.generate(9002, 0)
    original = copy.deepcopy(grid)
    gen.rule_mirror(grid)
    assert grid == original
