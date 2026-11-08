"""Focused semantic regressions for ARC generator c425a7cc61c7."""
from __future__ import annotations

from collections import Counter
import copy
import hashlib
import importlib
import json
from pathlib import Path
import random
import shutil

import pytest

from arc_repl.racket_bridge import RacketBridge
from scripts.rule_smoke import purity_body, rule_application


ROOT = Path(__file__).resolve().parents[1]
TASK = "c425a7cc61c7"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
BASE_PATH = ROOT / "data/base/solutions/banks/9a1b04175c5a/medium_127_select_legend_object_and_rotate_cw__c425a7cc61c7.json"


def _canonical_row() -> dict:
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise AssertionError(f"missing canonical row for {TASK}")


def _pairs() -> list[dict]:
    row = _canonical_row()
    test = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return [*row["train"], *test]


def _frozen(grid) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def _handcrafted_valid() -> list[list[int]]:
    grid = [[0] * 12 for _ in range(10)]
    grid[0][0] = 4
    for r, c in ((2, 2), (3, 2), (4, 2), (4, 3)):
        grid[r][c] = 4
    for r, c in ((2, 7), (2, 8), (3, 8), (3, 9)):
        grid[r][c] = 6
    for r, c in ((6, 5), (7, 5), (8, 5), (8, 6), (8, 7)):
        grid[r][c] = 8
    assert GEN.self_check(grid) == []
    return grid


def test_rule_authorities_and_hash_match_the_assigned_rule():
    row = _canonical_row()
    canonical = row["program_solution"]
    base = json.loads(BASE_PATH.read_text(encoding="utf-8"))
    assert canonical == base["racket_target"]["target_code"]
    normalized = " ".join(canonical.split())
    assert hashlib.sha256(normalized.encode()).hexdigest()[:12] == GEN.RULE_HASH
    assert GEN.RULE_HASH == "07f3dbff434c"


def test_every_canonical_pair_is_accepted_and_the_validation_mirror_is_exact_and_pure():
    pairs = _pairs()
    assert len(pairs) == 5
    for pair in pairs:
        grid = copy.deepcopy(pair["input"])
        snapshot = copy.deepcopy(grid)
        assert GEN.self_check(grid) == []
        assert GEN.rule_mirror(grid) == pair["output"]
        assert grid == snapshot


@pytest.mark.skipif(shutil.which("racket") is None, reason="racket is not installed")
def test_real_racket_rule_matches_all_pairs_is_input_pure_and_a_b_a_stable():
    source = _canonical_row()["program_solution"]
    pairs = _pairs()
    bridge = RacketBridge()
    try:
        for pair in pairs:
            grid = copy.deepcopy(pair["input"])
            snapshot = copy.deepcopy(grid)
            assert bridge.eval_text(rule_application(source, grid)) == pair["output"]
            assert grid == snapshot
        probe = bridge.eval_text(purity_body(source, pairs[0]["input"], pairs[1]["input"]))
        assert probe == [pairs[0]["output"], pairs[0]["output"], pairs[0]["input"]]
    finally:
        bridge.shutdown()


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize(
    ("axis", "value"),
    [
        ("grid_h", 10),
        ("grid_h", 16),
        ("grid_w", 12),
        ("grid_w", 18),
        ("n_distractors", 1),
        ("n_distractors", 2),
        ("target_cells", 4),
        ("target_cells", 8),
        ("target_profile", "wide"),
        ("target_profile", "tall"),
        ("target_profile", "square"),
        ("target_color", 1),
        ("target_color", 9),
    ],
)
def test_each_declared_axis_boundary_or_mode_is_realized_exactly(axis, value, band):
    grid = GEN.generate(771, 991, difficulty=band, **{axis: value})
    assert GEN.self_check(grid, difficulty=band, meta={"overrides": {axis: value}}) == []
    assert GEN.observe_overrides(grid)[axis] == value


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_linked_override_vectors_are_exact_and_the_only_incompatible_pair_fails_loudly(band):
    vectors = (
        {
            "grid_h": 10,
            "grid_w": 12,
            "n_distractors": 1,
            "target_cells": 4,
            "target_profile": "wide",
            "target_color": 1,
        },
        {
            "grid_h": 16,
            "grid_w": 18,
            "n_distractors": 2,
            "target_cells": 8,
            "target_profile": "square",
            "target_color": 9,
        },
    )
    for overrides in vectors:
        grid = GEN.generate(123, 456, difficulty=band, **overrides)
        assert GEN.self_check(grid) == []
        assert GEN.observe_overrides(grid) == overrides
    with pytest.raises(ValueError, match="incompatible"):
        GEN.generate(1, 2, difficulty=band, target_cells=4, target_profile="square")


def test_unknown_controls_and_out_of_domain_values_fail_closed():
    with pytest.raises(ValueError, match="unknown difficulty"):
        GEN.generate(0, 0, difficulty="extreme")
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(0, 0, invented_axis=1)
    with pytest.raises(ValueError, match="outside"):
        GEN.generate(0, 0, grid_h=9)
    with pytest.raises(ValueError, match="legal colors"):
        GEN.generate(0, 0, target_color=0)


def test_generation_is_deterministic_fresh_mutation_safe_and_global_rng_independent():
    random.seed(987654321)
    state = random.getstate()
    first = GEN.generate(111, 222, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(111, 222, difficulty="hard")
    assert random.getstate() == state
    assert first == second
    assert first is not second and first[0] is not second[0]

    frozen = _frozen(second)
    first[0][0] = 0
    assert _frozen(GEN.generate(111, 222, difficulty="hard")) == frozen

    by_seed = {_frozen(GEN.generate(seed, 17, difficulty="medium")) for seed in range(20)}
    by_index = {_frozen(GEN.generate(17, index, difficulty="medium")) for index in range(20)}
    assert len(by_seed) >= 18
    assert len(by_index) >= 18


def test_self_check_rejects_structural_impostors_and_never_mutates_them():
    valid = _handcrafted_valid()
    cases: dict[str, list[list[int]]] = {}

    missing_marker = copy.deepcopy(valid)
    missing_marker[0][0] = 0
    cases["missing_marker"] = missing_marker

    no_match = copy.deepcopy(valid)
    no_match[0][0] = 9
    cases["no_match"] = no_match

    duplicate_target = copy.deepcopy(valid)
    for r in range(len(duplicate_target)):
        for c in range(len(duplicate_target[0])):
            if duplicate_target[r][c] == 6:
                duplicate_target[r][c] = 4
    cases["two_target_components"] = duplicate_target

    symmetric = copy.deepcopy(valid)
    for r in range(len(symmetric)):
        for c in range(len(symmetric[0])):
            if symmetric[r][c] == 4 and (r, c) != (0, 0):
                symmetric[r][c] = 0
    for r, c in ((2, 2), (2, 3), (3, 2), (3, 3)):
        symmetric[r][c] = 4
    cases["rotational_noop"] = symmetric

    touching = copy.deepcopy(valid)
    touching[4][4] = 6
    cases["touching_components"] = touching

    cases["full_one_color"] = [[1] * 12 for _ in range(10)]
    cases["solid_2x2"] = [[1, 1], [1, 1]]

    for name, grid in cases.items():
        snapshot = copy.deepcopy(grid)
        assert GEN.self_check(grid), name
        assert grid == snapshot

    assert GEN.self_check([])
    assert GEN.self_check([[0, 1], [0]])
    assert GEN.self_check([[True] * 12 for _ in range(10)])


def test_default_census_is_semantically_clean_diverse_and_blocks_size_and_frequency_shortcuts():
    outputs = set()
    profiles = set()
    colors = set()
    target_boxes = set()
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for offset in range(100):
            seed = 400_000 + 10_000 * band_index + offset
            grid = GEN.generate(seed, seed * 19 + 7, difficulty=band)
            analysis = GEN._analysis(grid)
            assert analysis["errors"] == []
            assert analysis["n_distractors"] == 2
            sizes = sorted(part["size"] for part in analysis["distractor_components"])
            assert analysis["target_cells"] in sizes
            assert analysis["target_cells"] + 1 in sizes

            counts = Counter(value for row in grid for value in row if value)
            assert counts[analysis["target_color"]] == analysis["target_cells"] + 1
            assert sum(count == analysis["target_cells"] + 1 for count in counts.values()) >= 2

            output = GEN.rule_mirror(grid)
            assert output != grid
            outputs.add(_frozen(output))
            profiles.add(analysis["target_profile"])
            colors.add(analysis["target_color"])
            target_boxes.add(analysis["target_bbox"])

    assert profiles == {"wide", "tall", "square"}
    assert colors == set(range(1, 10))
    assert len(outputs) >= 120
    assert len(target_boxes) >= 30


def test_negative_marker_recombination_is_rejected_without_changing_the_source():
    grid = GEN.generate(991, 123, difficulty="medium")
    foreign = copy.deepcopy(grid)
    used = {value for row in foreign for value in row}
    replacement = next(color for color in range(1, 10) if color not in used)
    foreign[0][0] = replacement
    snapshot = copy.deepcopy(foreign)
    assert GEN.self_check(foreign)
    with pytest.raises(ValueError):
        GEN.rule_mirror(foreign)
    assert foreign == snapshot
