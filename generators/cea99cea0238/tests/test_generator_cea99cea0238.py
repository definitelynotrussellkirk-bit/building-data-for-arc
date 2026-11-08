"""Focused semantic regressions for ARC generator cea99cea0238."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
from pathlib import Path
import random

import pytest


ROOT = Path(__file__).resolve().parents[1]
TASK = "cea99cea0238"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
BASE_PATH = ROOT / "data/base/solutions/banks/5deb8ef303b3/easy_106_fill_row_or_column_spans__cea99cea0238.json"


def _canonical_row() -> dict:
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise AssertionError(f"missing canonical row for {TASK}")


def _pairs() -> list[dict]:
    row = _canonical_row()
    tests = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return [*row["train"], *tests]


def _frozen(grid) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def _lesson(seed: int = 8123, difficulty: str = "medium") -> list[dict]:
    return [
        {
            "input": (grid := GEN.generate(seed, sample_index, difficulty=difficulty)),
            "output": GEN.rule_mirror(grid),
        }
        for sample_index in range(GEN.EXAMPLES_NEEDED + 1)
    ]


def test_rule_authorities_and_hash_match_the_assigned_rule():
    row = _canonical_row()
    canonical = row["program_solution"]
    base = json.loads(BASE_PATH.read_text(encoding="utf-8"))
    assert canonical == base["racket_target"]["target_code"]
    normalized = " ".join(canonical.split())
    assert hashlib.sha256(normalized.encode()).hexdigest()[:12] == GEN.RULE_HASH
    assert GEN.RULE_HASH == "7e8b9ba56afa"


def test_every_canonical_pair_is_accepted_and_python_mirror_is_exact_and_pure():
    pairs = _pairs()
    assert len(pairs) == 5
    for pair in pairs:
        grid = copy.deepcopy(pair["input"])
        snapshot = copy.deepcopy(grid)
        assert GEN.self_check(grid) == []
        assert GEN.rule_mirror(grid) == pair["output"]
        assert grid == snapshot


def test_default_lesson_schedule_teaches_horizontal_vertical_and_crossing():
    lesson = _lesson()
    observed = [GEN.observe_overrides(pair["input"]) for pair in lesson]
    assert observed[0]["orientation_profile"] == "horizontal"
    assert observed[0]["crossing_profile"] == "separated"
    assert observed[1]["orientation_profile"] == "vertical"
    assert observed[1]["crossing_profile"] == "separated"
    assert observed[2]["orientation_profile"] == "mixed"
    assert observed[2]["crossing_profile"] == "crossing"
    assert GEN.lesson_identifiable(lesson[: GEN.EXAMPLES_NEEDED], lesson[-1]) == []


def test_crossing_precedence_is_observable_and_matches_row_major_later_color():
    grid = GEN.generate(811, 2, difficulty="medium")
    analysis = GEN._analyze(grid)
    assert analysis["errors"] == []
    assert analysis["facts"]["crossing_count"] >= 1
    official = GEN._candidate_output("official", grid)
    first_wins = GEN._candidate_output("first_wins", grid)
    assert official == GEN.rule_mirror(grid)
    assert first_wins != official


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize(
    ("axis", "value"),
    [
        ("grid_h", 8),
        ("grid_h", 14),
        ("grid_w", 9),
        ("grid_w", 16),
        ("spans", 2),
        ("spans", 7),
        ("orientation_profile", "horizontal"),
        ("orientation_profile", "vertical"),
        ("orientation_profile", "mixed"),
        ("crossing_profile", "separated"),
        ("crossing_profile", "crossing"),
    ],
)
def test_declared_axis_boundaries_and_modes_are_realized_exactly(axis, value, band):
    overrides = {axis: value}
    if axis == "crossing_profile" and value == "crossing":
        overrides["orientation_profile"] = "mixed"
    if axis == "orientation_profile" and value != "mixed":
        overrides["crossing_profile"] = "separated"
    grid = GEN.generate(771, 991, difficulty=band, **overrides)
    assert GEN.self_check(grid) == []
    observed = GEN.observe_overrides(grid)
    for key, expected in overrides.items():
        assert observed[key] == expected


@pytest.mark.parametrize(
    ("texture", "orientation", "crossing"),
    [
        ("horizontal", "horizontal", "separated"),
        ("vertical", "vertical", "separated"),
        ("mixed", "mixed", "separated"),
        ("crossing", "mixed", "crossing"),
    ],
)
def test_each_helpful_texture_changes_observable_semantics(texture, orientation, crossing):
    grid = GEN.generate(98, 17, difficulty="medium", texture=texture)
    observed = GEN.observe_overrides(grid)
    assert observed["orientation_profile"] == orientation
    assert observed["crossing_profile"] == crossing


def test_incompatible_crossing_controls_fail_loudly():
    with pytest.raises(ValueError, match="requires orientation_profile='mixed'"):
        GEN.generate(
            1,
            2,
            difficulty="medium",
            orientation_profile="horizontal",
            crossing_profile="crossing",
        )
    with pytest.raises(ValueError, match="conflicts"):
        GEN.generate(1, 2, texture="crossing", orientation_profile="vertical")


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
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert _frozen(GEN.generate(111, 222, difficulty="hard")) == frozen

    by_seed = {_frozen(GEN.generate(seed, 17, difficulty="medium")) for seed in range(20)}
    by_index = {_frozen(GEN.generate(17, index, difficulty="medium")) for index in range(20)}
    assert len(by_seed) >= 18
    assert len(by_index) >= 18


def test_self_check_rejects_at_least_four_structural_impostors_without_mutation():
    cases = {
        name: GEN.generate(0, 0, texture=name)
        for name in GEN.DEGENERATE_TEXTURES
    }
    blocked = [[0] * 9 for _ in range(8)]
    blocked[2][1] = blocked[2][7] = 3
    blocked[2][4] = blocked[5][4] = 6
    cases["endpoint_on_other_span"] = blocked

    for name, grid in cases.items():
        snapshot = copy.deepcopy(grid)
        assert GEN.self_check(grid), name
        assert grid == snapshot

    assert len(cases) >= 4
    assert GEN.self_check([])
    assert GEN.self_check([[0, 1], [0]])
    assert GEN.self_check([[True] * 9 for _ in range(8)])


def test_rule_mirror_returns_fresh_rows_and_does_not_alias_input():
    grid = GEN.generate(999, 2, difficulty="easy")
    output = GEN.rule_mirror(grid)
    snapshot = copy.deepcopy(output)
    output[0][0] = 9 if output[0][0] != 9 else 8
    assert GEN.rule_mirror(grid) == snapshot
    assert output is not grid
    assert all(out_row is not in_row for out_row, in_row in zip(output, grid))
