"""Focused semantic regressions for generator c09f9e692978."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
from pathlib import Path
import random

import pytest

ROOT = Path(__file__).resolve().parents[1]
TASK = "c09f9e692978"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
BASE_PATHS = (
    ROOT / "data/base/solutions/training/868de0fa__c09f9e692978.json",
    ROOT / "data/base/solutions/augmented/868de0fa__a22f9af5411f.json",
)


def _canonical_rows():
    rows = []
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                rows.append(row)
    return rows


def _pairs():
    pairs = []
    for row in _canonical_rows():
        pairs.extend(row.get("train") or [])
        pairs.extend(row.get("test") or [])
    return pairs


def _frozen(grid):
    return tuple(tuple(row) for row in grid)


def test_rule_hash_and_selected_authorities_match_canonical_without_losing_comments():
    rows = _canonical_rows()
    assert len(rows) == 2
    source = rows[0]["program_solution"]
    assert all(row["program_solution"] == source for row in rows)
    digest = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
    assert digest == GEN.RULE_HASH == "d74485baf037"
    for path in BASE_PATHS:
        target = json.loads(path.read_text())["racket_target"]
        assert target["target_code"] == source
        assert target["target_code_role"] == "selected_task_rule"
        assert target["raw_code_role"] == "archival_executable_source"
        assert ";;" in target["raw_code"]


def test_every_canonical_pair_is_accepted_and_mirrored_exactly_and_purely():
    pairs = _pairs()
    assert len(pairs) == 12
    for pair in pairs:
        grid = copy.deepcopy(pair["input"])
        snapshot = copy.deepcopy(grid)
        assert GEN.self_check(grid) == []
        assert GEN.strict_canonical_like(grid) == []
        assert GEN.rule_mirror(grid) == pair["output"]
        assert grid == snapshot


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize(
    ("axis", "value"),
    [
        ("grid_h", 10),
        ("grid_h", 22),
        ("grid_w", 10),
        ("grid_w", 22),
        ("n_frames", 2),
        ("n_frames", 5),
        ("parity_profile", "mixed"),
        ("parity_profile", "odd_only"),
        ("parity_profile", "even_only"),
    ],
)
def test_declared_override_boundaries_are_exact_and_observable(axis, value, band):
    grid = GEN.generate(191, 37, difficulty=band, **{axis: value})
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid)[axis] == value


def test_full_small_canvas_boundary_matrix_is_feasible():
    for profile in ("mixed", "odd_only", "even_only"):
        grid = GEN.generate(
            3,
            7,
            difficulty="easy",
            grid_h=10,
            grid_w=10,
            n_frames=5,
            parity_profile=profile,
        )
        assert GEN.self_check(grid) == []
        assert GEN.observe_overrides(grid) == {
            "grid_h": 10,
            "grid_w": 10,
            "n_frames": 5,
            "parity_profile": profile,
        }


def test_unknown_override_is_rejected_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 2, typo_axis=3)


def test_default_noncanonical_samples_refute_height_parity_in_both_directions():
    for band in ("easy", "medium", "hard"):
        grid = GEN.generate(411, 1, difficulty=band)
        facts = GEN._analyze(grid)["facts"]
        assert facts["parity_profile"] == "mixed"
        assert facts["odd_width_even_height"] >= 1
        assert facts["even_width_odd_height"] >= 1
        official = GEN.rule_mirror(grid)
        assert GEN.LESSON_COMPETITORS["height_parity"](grid) != official
        assert GEN.LESSON_COMPETITORS["interior_area_parity"](grid) != official


def test_three_demo_lessons_identify_all_declared_competitors():
    for band in ("easy", "medium", "hard"):
        pairs = []
        for index in range(GEN.EXAMPLES_NEEDED + 1):
            grid = GEN.generate(881, 97 + index, difficulty=band)
            pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
        assert GEN.lesson_identifiable(pairs[: GEN.EXAMPLES_NEEDED], pairs[-1]) == []


def test_self_check_rejects_structural_impostors_without_mutation():
    valid = GEN.generate(17, 1, difficulty="medium")
    cases = {}

    broken = copy.deepcopy(valid)
    frame = GEN._analyze(broken)["facts"]["frames"][0]
    r, c = min(frame["border"])
    broken[r][c] = 0
    cases["broken_border"] = broken

    occupied = copy.deepcopy(valid)
    r, c = GEN._analyze(occupied)["facts"]["frames"][0]["interior"][0]
    occupied[r][c] = 9
    cases["occupied_interior"] = occupied

    reserved = copy.deepcopy(valid)
    frame = GEN._analyze(reserved)["facts"]["frames"][0]
    for r, c in frame["border"]:
        reserved[r][c] = 2
    cases["reserved_border_colour"] = reserved

    cases["single_frame"] = [row[:] for row in valid]
    keep = GEN._analyze(valid)["facts"]["frames"][0]["border"]
    cases["single_frame"] = [
        [value if (r, c) in keep else 0 for c, value in enumerate(row)]
        for r, row in enumerate(valid)
    ]

    for name, grid in cases.items():
        snapshot = copy.deepcopy(grid)
        assert GEN.self_check(grid), name
        assert grid == snapshot

    assert GEN.self_check([])
    assert GEN.self_check([[0, 1], [0]])
    assert GEN.self_check([[True] * 10 for _ in range(10)])


def test_generation_is_deterministic_fresh_mutation_safe_and_rng_independent():
    random.seed(987654321)
    state = random.getstate()
    first = GEN.generate(111, 222, difficulty="hard")
    second = GEN.generate(111, 222, difficulty="hard")
    assert random.getstate() == state
    assert first == second
    assert first is not second and first[0] is not second[0]

    frozen = _frozen(second)
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert _frozen(GEN.generate(111, 222, difficulty="hard")) == frozen

    by_seed = {_frozen(GEN.generate(seed, 17, difficulty="medium")) for seed in range(20)}
    by_index = {_frozen(GEN.generate(17, index, difficulty="medium")) for index in range(20)}
    assert len(by_seed) >= 18
    assert len(by_index) >= 14


def test_rule_mirror_returns_fresh_rows_and_preserves_every_border():
    grid = GEN.generate(92, 1, difficulty="medium")
    analysis = GEN._analyze(grid)
    output = GEN.rule_mirror(grid)
    for frame in analysis["facts"]["frames"]:
        for r, c in frame["border"]:
            assert output[r][c] == grid[r][c]
    snapshot = copy.deepcopy(output)
    output[0][0] = 9 if output[0][0] != 9 else 8
    assert GEN.rule_mirror(grid) == snapshot
