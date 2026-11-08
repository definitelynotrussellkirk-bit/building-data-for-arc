"""Prototype scope only: quarter turns about matched outside-piece markers."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator


TASK_ID = "fa3550d200a0"
ROOT = find_root(__file__)
GENERATOR, GENERATOR_PATH, _GENERATOR_SHA = load_selected_generator(TASK_ID, root=ROOT)
PROTOTYPE_PATH = ROOT / f"generators/{TASK_ID}/workspace/parametric/prototype.py"


def test_parametric_prototype_is_available():
    assert PROTOTYPE_PATH.is_file(), "quarter-turn prototype has not been implemented"


@pytest.fixture(scope="module")
def proto():
    spec = importlib.util.spec_from_file_location("quarter_turns_fa3550d200a0", PROTOTYPE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def builder(proto):
    with proto.EpisodeBuilder(root=ROOT) as live:
        yield live


def _canonical_program():
    with canonical_path(ROOT).open(encoding="utf-8") as stream:
        programs = {
            row["program_solution"] for row in map(json.loads, stream)
            if row.get("task_id") == TASK_ID
        }
    assert len(programs) == 1
    return programs.pop()


def _hand_scene():
    grid = [[0] * 20 for _ in range(20)]
    for row in range(4, 13):
        for col in range(1, 10):
            grid[row][col] = 8
    grid[6][3] = 3
    grid[9][6] = 4
    for row, col, color in (
        (2, 14, 3), (2, 15, 2), (2, 16, 2), (3, 14, 2),
        (8, 14, 4), (9, 15, 2), (10, 16, 2),
        (15, 14, 6), (15, 15, 2), (15, 16, 2),
    ):
        grid[row][col] = color
    return grid


def test_setting_zero_is_exact_canonical_and_runs_all_canonical_labels(builder):
    assert builder.programs[0] == _canonical_program()
    for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True):
        assert builder.execute(0, pair["input"]) == pair["output"]


@pytest.mark.parametrize("turns,payload", [
    (0, ((2, 3), (2, 4), (3, 2), (6, 6), (7, 7))),
    (1, ((3, 2), (4, 2), (2, 1), (6, 4), (7, 3))),
    (2, ((2, 1), (2, 0), (1, 2), (4, 4), (3, 3))),
    (3, ((1, 2), (0, 2), (2, 3), (4, 6), (3, 7))),
])
def test_racket_rotates_about_marker_and_ignores_unmatched_piece(builder, turns, payload):
    grid = _hand_scene()
    assert GENERATOR.self_check(grid) == []
    expected = [[8] * 9 for _ in range(9)]
    expected[2][2], expected[5][5] = 3, 4
    for row, col in payload:
        expected[row][col] = 2
    assert builder.execute(turns, grid) == expected


def test_geometry_gate_excludes_inputs_clipped_only_by_alternative_turns(proto):
    grid = _hand_scene()
    assert proto.rotation_domain_errors(grid, GENERATOR) == []
    grid[6][3], grid[4][1] = 8, 3
    assert GENERATOR.self_check(grid) == []
    errors = proto.rotation_domain_errors(grid, GENERATOR)
    assert any("outside canvas" in error for error in errors)


@pytest.mark.parametrize("turns", [0, 1, 2, 3])
def test_demo_identification_precedes_four_distinct_query_labels(builder, turns):
    episode = builder.generate(73, quarter_turns=turns, demos=2, queries=4)
    assert len(episode["train"]) == 2
    assert len(episode["test"]) == 4
    assert episode["meta"]["quarter_turns"] == turns
    pairs = episode["train"] + episode["test"]
    assert len({json.dumps(pair["input"]) for pair in pairs}) == 6
    assert episode["meta"]["demo_survivors"] == [turns]
    for rival in (set(range(4)) - {turns}):
        assert any(
            builder.execute(rival, pair["input"]) != pair["output"]
            for pair in episode["train"]
        )
    for pair in pairs:
        assert builder.execute(turns, pair["input"]) == pair["output"]
    trace = episode["meta"]["sampling"]["attempts"]
    first_query = next(index for index, row in enumerate(trace) if row["phase"] == "query")
    assert all(row["phase"] == "demo" for row in trace[:first_query])
    assert all(row["phase"] == "query" for row in trace[first_query:])
    assert all(check["demo_consistent_settings"] == [turns]
               for check in episode["meta"]["query_lesson_checks"])


def test_query_count_cannot_change_demonstrations_or_first_query(builder):
    one = builder.generate(17, quarter_turns=1, demos=2, queries=1)
    four = builder.generate(17, quarter_turns=1, demos=2, queries=4)
    assert one["train"] == four["train"]
    assert one["test"] == four["test"][:1]


def test_public_projection_omits_rule_parameter_seed_and_query_labels(proto, builder):
    episode = builder.generate(31, quarter_turns=2, demos=1, queries=4)
    public = proto.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    untouched = copy.deepcopy(episode)
    public["train"][0]["input"][0][0] = 9
    assert episode == untouched


def test_finite_attempt_budget_fails_loudly_and_retains_attempts(proto, builder):
    with pytest.raises(proto.SamplingExhausted, match="exhausted") as failure:
        builder.generate(17, quarter_turns=0, demos=2, queries=4, max_attempts=1)
    record = failure.value.record
    assert record["max_attempts"] == 1
    assert len(record["attempts"]) == 1
    assert record["accepted_demos"] < 2
    assert record["accepted_queries"] == 0


@pytest.mark.parametrize("invalid", [True, False, -1, 4, 1.0, "1"])
def test_invalid_parameter_never_silently_coerces(builder, invalid):
    with pytest.raises((TypeError, ValueError)):
        builder.generate(17, quarter_turns=invalid)


def test_seed_draw_is_reproducible_and_settings_cover_bounded_domain(proto):
    values = [proto.choose_parameter(seed) for seed in range(40)]
    assert values == [proto.choose_parameter(seed) for seed in range(40)]
    assert set(values) == {0, 1, 2, 3}
