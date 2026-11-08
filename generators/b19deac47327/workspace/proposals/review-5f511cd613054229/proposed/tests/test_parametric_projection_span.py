"""Prototype-only tests for a fixed-per-episode projection span.

These tests cover the task-local proposed extension only. They neither change
nor approve the selected canonical Racket rule; exact Racket execution is
retained separately under ``WORK/checks/parametric/``.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from reviewer_support import canonical_path, find_root, load_selected_generator


PROTOTYPE_PATH = (
    Path(__file__).resolve().parents[1]
    / "workspace"
    / "parametric"
    / "prototype.py"
)
ROOT = find_root(__file__)


def _prototype():
    assert PROTOTYPE_PATH.is_file(), (
        "projection-span prototype is missing; expected " f"{PROTOTYPE_PATH}"
    )
    spec = importlib.util.spec_from_file_location(
        "border_projection_span_prototype", PROTOTYPE_PATH
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_source() -> str:
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("task_id") == "b19deac47327":
            return row["program_solution"]
    raise AssertionError("selected canonical source not found")


def _horizontal_witness() -> list[list[int]]:
    grid = [[0] * 9 for _ in range(11)]
    grid[0] = [2] * 9
    grid[-1] = [4] * 9
    grid[3][2] = 1
    grid[4][4] = 1
    grid[6][4] = 1
    grid[7][6] = 1
    return grid


def _vertical_witness() -> list[list[int]]:
    grid = [[0] * 11 for _ in range(9)]
    for row in grid:
        row[0] = 8
        row[-1] = 3
    grid[2][3] = 1
    grid[4][4] = 1
    grid[4][6] = 1
    grid[6][7] = 1
    return grid


def test_parameter_contract_and_episode_selection_are_strict():
    prototype = _prototype()
    assert prototype.ALLOWED_PROJECTION_SPANS == (1, 2)
    assert prototype.DEFAULT_PROJECTION_SPAN == 1
    assert prototype.choose_projection_span(20) == 1
    assert prototype.choose_projection_span(21) == 2
    assert prototype.choose_projection_span(22) == 1
    for invalid in (True, False, 1.0, "1", None):
        with pytest.raises(TypeError):
            prototype.choose_projection_span(invalid)
    for invalid in (True, False, 0, 3, 1.0, "2", None):
        with pytest.raises((TypeError, ValueError)):
            prototype.validate_projection_span(invalid)


def test_span_one_racket_is_byte_exact_canonical_and_hash_pinned():
    prototype = _prototype()
    module, _source_path, _source_sha = load_selected_generator(
        prototype.TASK_ID, root=ROOT
    )
    span_one = prototype.racket_source(1, root=ROOT)
    assert span_one == _canonical_source()
    assert prototype.normalized_hash(span_one) == module.RULE_HASH == "2b2e46dd36cc"


def test_span_two_extends_the_same_direction_and_color_on_both_axes():
    prototype = _prototype()
    assert prototype.racket_source(2, root=ROOT) != prototype.racket_source(1, root=ROOT)

    horizontal = _horizontal_witness()
    h_one = prototype.python_transform(horizontal, 1)
    h_two = prototype.python_transform(horizontal, 2)
    assert h_one[2][2] == 2 and h_one[8][6] == 4
    assert h_one[1][2] == 0 and h_one[9][6] == 0
    assert h_two[2][2] == 2 and h_two[1][2] == 2
    assert h_two[8][6] == 4 and h_two[9][6] == 4

    vertical = _vertical_witness()
    v_one = prototype.python_transform(vertical, 1)
    v_two = prototype.python_transform(vertical, 2)
    assert v_one[2][2] == 8 and v_one[6][8] == 3
    assert v_one[2][1] == 0 and v_one[6][9] == 0
    assert v_two[2][2] == 8 and v_two[2][1] == 8
    assert v_two[6][8] == 3 and v_two[6][9] == 3


def test_sampler_is_deterministic_lawful_and_preserves_family_roles():
    prototype = _prototype()
    orientations = set()
    for seed in range(4):
        for pair_index in range(4):
            first = prototype.sample_input(seed, pair_index)
            second = prototype.sample_input(seed, pair_index)
            assert first == second
            facts = prototype.validate_input(first)
            orientations.add(facts["orientation"])
            assert facts["projection_span_capacity"] >= 2
            assert facts["first_count"] > 0 and facts["second_count"] > 0
            assert len(facts["markers"]) >= 6
            assert set(facts["palette"]) == {
                0,
                1,
                facts["edge_a"],
                facts["edge_b"],
            }
    assert orientations == {"horizontal", "vertical"}


def test_episode_uses_one_span_and_every_pair_refutes_the_other_setting():
    prototype = _prototype()
    for span in prototype.ALLOWED_PROJECTION_SPANS:
        episode = prototype.build_episode(root=ROOT, seed=40 + span, projection_span=span)
        assert episode["parameter"] == {"projection_span": span}
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 1
        alternative = 2 if span == 1 else 1
        pairs = [*episode["train"], *episode["test"]]
        assert {pair["orientation"] for pair in pairs} == {"horizontal", "vertical"}
        for pair in pairs:
            assert pair["output"] == prototype.python_transform(pair["input"], span)
            assert pair["output"] != prototype.python_transform(
                pair["input"], alternative
            )


def test_public_challenge_hides_parameter_reference_and_query_answer():
    prototype = _prototype()
    public = prototype.public_challenge(
        prototype.build_episode(root=ROOT, seed=41, projection_span=2)
    )
    payload = json.dumps(public, sort_keys=True)
    assert "parameter" not in public
    assert "projection_span" not in payload
    assert "racket" not in payload.lower()
    assert all("output" in pair for pair in public["train"])
    assert public["test"] and all("output" not in pair for pair in public["test"])


def test_retained_racket_files_equal_materialized_sources():
    prototype = _prototype()
    for span in prototype.ALLOWED_PROJECTION_SPANS:
        path = prototype.rule_path(span)
        assert path.read_text(encoding="utf-8") == prototype.racket_source(
            span, root=ROOT
        )
