from __future__ import annotations

import copy
import hashlib
import json
import random

import pytest

from arcpuzzles import Catalog
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
)

ROOT = find_root(__file__)
TASK_ID = "72f0b65569a4"
MODULE, GENERATOR_PATH, GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
CATALOG = Catalog(ROOT)


def _canonical_row() -> dict:
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"canonical row missing for {TASK_ID}")


def _canonical_pairs() -> list[dict]:
    return canonical_pairs(TASK_ID, root=ROOT)


def _apply_reference(inputs):
    report = CATALOG.apply(TASK_ID, inputs, reference="canonical")
    assert report["generator_sha256"] == GENERATOR_SHA256
    assert report["executed_rule_hash"] == MODULE.RULE_HASH
    assert report["rule_hash_matches_catalog"]
    assert len(report["results"]) == len(inputs)
    for result in report["results"]:
        assert result["error"] is None, result
        assert result["valid_output"], result
    return [result["output"] for result in report["results"]]


def _normalized_rule_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _frame_and_marks(grid):
    facts, errors = MODULE._analyze(grid)
    assert not errors
    return facts["frame"], set(facts["marks"])


def test_metadata_rule_hash_and_authorities_match() -> None:
    row = _canonical_row()
    canonical = row["program_solution"]
    # Locate the data tree through its public canonical path. Both the library
    # and the staged runtime retain the base authority beside canonical/.
    base_path = (
        canonical_path(ROOT).parent.parent
        / "base/solutions/banks"
        / row["bank"]
        / f"{row['original_id']}__{TASK_ID}.json"
    )
    base = json.loads(base_path.read_text(encoding="utf-8"))
    target = base["racket_target"]
    assert MODULE.VERSION == "3.1.0"
    assert MODULE.EXAMPLES_NEEDED == 3
    assert MODULE.RULE_HASH == "64f526c95424"
    assert MODULE.RULE_HASH == _normalized_rule_hash(canonical)
    assert target["target_code"] == canonical
    assert target["raw_code"] == canonical


def test_all_canonical_inputs_pass_and_rule_is_exact_pure_reentrant() -> None:
    pairs = _canonical_pairs()
    assert len(pairs) == 3
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert MODULE.self_check(pair["input"]) == []
        assert MODULE.strict_canonical_like(pair["input"]) == []
        assert pair["input"] == before

    # One public apply call shares a Racket rule/bridge across the batch. The
    # repeated A/B/A tail detects state leaking between distinct applications.
    # Input purity here is measured at the public Python API boundary; it does
    # not inspect mutation of the separate Racket process's private grid values.
    sequence = pairs + [pairs[0], pairs[1], pairs[0]]
    inputs = [pair["input"] for pair in sequence]
    before = copy.deepcopy(inputs)
    assert _apply_reference(inputs) == [pair["output"] for pair in sequence]
    assert inputs == before


def test_determinism_fresh_returns_and_process_rng_state() -> None:
    state = random.getstate()
    first = MODULE.generate(901, 17, difficulty="hard")
    assert random.getstate() == state
    second = MODULE.generate(901, 17, difficulty="hard")
    assert random.getstate() == state
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert MODULE.generate(901, 17, difficulty="hard") == second


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_exact_axis_boundaries_are_observable(difficulty: str) -> None:
    cases = (
        {"grid_h": 7, "grid_w": 9, "frame_h": 4, "frame_w": 5, "n_marks": 1},
        {"grid_h": 18, "grid_w": 20, "frame_h": 12, "frame_w": 14, "n_marks": 7},
        {"grid_h": 7, "grid_w": 9, "frame_h": 5, "frame_w": 7, "n_marks": 7},
    )
    for index, overrides in enumerate(cases):
        grid = MODULE.generate(
            1800 + index,
            700 + index,
            difficulty=difficulty,
            **overrides,
        )
        assert MODULE.self_check(grid, meta={"overrides": overrides}) == []
        assert MODULE.observe_overrides(grid) == overrides

    with pytest.raises(ValueError, match="cannot fit|one-cell exterior margin"):
        MODULE.generate(1, 2, difficulty=difficulty, grid_h=7, frame_h=12)
    with pytest.raises(ValueError, match="cannot fit|one-cell exterior margin"):
        MODULE.generate(1, 2, difficulty=difficulty, grid_w=9, frame_w=14)
    with pytest.raises(TypeError, match="unknown override"):
        MODULE.generate(1, 2, difficulty=difficulty, texture="warm")


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
@pytest.mark.parametrize("start_index", [0, 1])
def test_sample_index_schedule_exercises_all_semantic_branches(
    difficulty: str, start_index: int
) -> None:
    grids = [
        MODULE.generate(4201, index, difficulty=difficulty)
        for index in range(start_index, start_index + 4)
    ]
    assert all(MODULE.self_check(grid) == [] for grid in grids)
    witnesses = MODULE.SEMANTIC_WITNESSES
    assert all(witnesses["productive_empty_target"](grid) for grid in grids)
    # A three-demonstration/one-query lesson must retain each exceptional
    # branch after any single held-out grid, irrespective of its start parity.
    for name in ("occupied_mirror_pair", "center_axis_mark"):
        assert sum(bool(witnesses[name](grid)) for grid in grids) >= 2, name
    assert any(witnesses["frame_local_not_global_axis"](grid) for grid in grids)


def test_three_demo_materialized_lesson_is_identifiable() -> None:
    instance = CATALOG.generate(
        TASK_ID,
        count=1,
        seed=77123,
        sample_index=0,
        n_train=3,
        n_test=1,
        allow_unapproved=True,
    )[0]
    assert instance["provenance"]["generator_sha256"] == GENERATOR_SHA256
    assert len(instance["train"]) == 3
    assert len(instance["test"]) == 1
    assert MODULE.lesson_identifiable(instance["train"], instance["test"][0]) == []


def test_self_check_rejects_targeted_impostors() -> None:
    valid = MODULE.generate(
        53,
        2,
        difficulty="medium",
        grid_h=12,
        grid_w=15,
        frame_h=7,
        frame_w=9,
        n_marks=4,
    )
    assert MODULE.self_check(valid) == []
    (r1, c1, r2, c2), marks = _frame_and_marks(valid)

    broken_frame = copy.deepcopy(valid)
    broken_frame[r1][c1 + 1] = 0
    assert any("broken" in message for message in MODULE.self_check(broken_frame))

    blue_interior = copy.deepcopy(valid)
    blue_interior[r1 + 1][c1 + 1] = 1
    assert any("off the frame border" in message for message in MODULE.self_check(blue_interior))

    mark_outside = copy.deepcopy(valid)
    row, col = next(iter(marks))
    mark_outside[row][col] = 0
    mark_outside[0][0] = 4
    assert any("outside" in message for message in MODULE.self_check(mark_outside))

    no_productive = MODULE.generate(
        91,
        2,
        difficulty="easy",
        grid_h=9,
        grid_w=11,
        frame_h=5,
        frame_w=5,
        n_marks=1,
    )
    (nr1, nc1, nr2, nc2), only_marks = _frame_and_marks(no_productive)
    only_row, only_col = next(iter(only_marks))
    no_productive[only_row][only_col] = 0
    no_productive[nr1 + 1][(nc1 + nc2) // 2] = 4
    assert any("empty off-axis mirror" in message for message in MODULE.self_check(no_productive))

    wrong_palette = copy.deepcopy(valid)
    wrong_palette[0][0] = 7
    assert any("colors" in message for message in MODULE.self_check(wrong_palette))


def test_negative_recombinations_distinguish_distribution_from_oracle_domain() -> None:
    valid = MODULE.generate(
        101,
        0,
        difficulty="hard",
        grid_h=18,
        grid_w=20,
        frame_h=4,
        frame_w=5,
        n_marks=2,
    )

    # A second complete frame is outside this one-frame teaching grammar, but
    # the canonical rule intentionally iterates over every frame and executes.
    multiple_frames = copy.deepcopy(valid)
    for row in range(12, 16):
        for col in range(14, 19):
            if row in (12, 15) or col in (14, 18):
                multiple_frames[row][col] = 1
    multiple_frames[13][15] = 4
    assert MODULE.self_check(multiple_frames)

    # Removing every yellow mark makes the answer-bearing feature absent from
    # every remaining scene part. The lesson grammar rejects it; the permissive
    # Racket oracle still executes and returns the unchanged frame scene.
    no_marks = copy.deepcopy(valid)
    for row in range(len(no_marks)):
        for col in range(len(no_marks[0])):
            if no_marks[row][col] == 4:
                no_marks[row][col] = 0
    assert MODULE.self_check(no_marks)

    inputs = [multiple_frames, no_marks]
    before = copy.deepcopy(inputs)
    multi_output, no_marks_output = _apply_reference(inputs)
    assert isinstance(multi_output, list) and multi_output
    assert no_marks_output == no_marks
    assert inputs == before
