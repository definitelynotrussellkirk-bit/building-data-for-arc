"""Regression cases for optional declared-rival lesson scoring.

The shared suite supplies its established synthetic-generator helpers. Labels
below belong to a transparent doubling fixture; no Racket call is mocked as a
successful reference execution, and no corpus generator participates.
"""
from __future__ import annotations

import pytest

from test_generator_semantic_gate import (
    TASK, _canonical_file, _gen_module, _install, gsg,
)


def _declared_only_double(grid):
    return [[value * 2 for value in row] for row in grid]


def _declared_only_add_one(grid):
    return [[value + 1 if value else 0 for value in row] for row in grid]


def _declared_only_lesson():
    inputs = [
        [[1, 0], [0, 0]], [[0, 1], [0, 0]],
        [[0, 0], [1, 0]], [[0, 0], [0, 1]],
    ]
    query = [[2, 0], [0, 0]]
    return {
        "index": 0, "band": "easy", "seed": 17, "sample_index": 22,
        "replay": "band=easy seed=17 sample_index=22",
        "demos": [{"input": grid, "output": _declared_only_double(grid)} for grid in inputs],
        "query": {"input": query, "output": _declared_only_double(query)},
    }


def _declared_only_fixture(monkeypatch, tmp_path, **attrs):
    lesson = _declared_only_lesson()
    first = lesson["demos"][0]
    _canonical_file(monkeypatch, tmp_path, [(first["input"], first["output"])])
    _install(monkeypatch, _gen_module(EXAMPLES_NEEDED=4, **attrs))
    calls = []

    def materialize(*args, **kwargs):
        calls.append(kwargs)
        return [lesson], []

    monkeypatch.setattr(gsg, "materialize_lessons", materialize)
    return calls


@pytest.mark.parametrize("declaration", ["LESSON_COMPETITORS", "CANONICAL_SHORTCUTS"])
@pytest.mark.parametrize("strict_hook", [False, True])
def test_declared_query_changing_rival_is_scored_without_lesson_hook(
        monkeypatch, tmp_path, declaration, strict_hook):
    attrs = {declaration: {"adds_one": _declared_only_add_one}}
    if strict_hook:
        attrs["strict_canonical_like"] = lambda grid: []
    calls = _declared_only_fixture(monkeypatch, tmp_path, **attrs)
    audit = gsg.audit_task(TASK, per_band=2, lessons=1, require_contract=True)

    assert audit["lessons"] is not None, "declared rivals were never lesson-scored"
    assert audit["status"] == "FAIL"
    assert not audit["hooks_declared"]["lesson_identifiable"]
    stats = audit["lessons"]
    assert stats["assessment_basis"] == "declared_rivals"
    assert stats["hook_declared"] is False
    assert stats["hook_errors"] == 0
    assert stats["unidentifiable"] == 1
    assert stats["per_band"]["easy"]["unidentifiable"] == 1
    example = stats["unidentifiable_examples"][0]
    assert example["survivors"] == ["adds_one"]
    assert example["replay"] == "band=easy seed=17 sample_index=22"
    assert calls[0]["n_demos"] == 4
    assert not any("could not NAME" in note for note in audit["notes"])
    if declaration == "CANONICAL_SHORTCUTS":
        assert stats["auto_scored_canonical_shortcuts"] == ["adds_one"]
        assert audit["canonical_ambiguity"]["ambiguous_declared"] == ["adds_one"]


def test_hookless_answer_equivalent_and_demo_refuted_rivals_are_not_ambiguity(
        monkeypatch, tmp_path):
    _declared_only_fixture(monkeypatch, tmp_path, LESSON_COMPETITORS={
        "doubles": _declared_only_double, "always_zero": lambda grid: [[0]],
    })
    audit = gsg.audit_task(TASK, per_band=2, lessons=1, require_contract=True)
    assert audit["status"] == "PASS"
    stats = audit["lessons"]
    assert stats["identifiable"] == 1
    assert stats["unidentifiable"] == 0
    assert stats["competitor_survived_all_counts"] == {"doubles": 1}
    assert stats["competitor_survivor_counts"] == {"doubles": 1}
    assert stats["survivors_on_identifiable_lessons"] == []
    assert "without detected declared-rival ambiguity" in gsg._summary_line(audit)
    assert any("lesson_identifiable absent" in note for note in audit["notes"])


def test_hookless_competitor_error_is_counted_without_a_hook_error(monkeypatch, tmp_path):
    def broken(grid):
        raise ValueError("fixture rival failure")

    _declared_only_fixture(monkeypatch, tmp_path, LESSON_COMPETITORS={"broken": broken})
    audit = gsg.audit_task(TASK, per_band=2, lessons=1)
    assert audit["status"] == "WARN"
    assert audit["lessons"]["competitor_errors"] == 1
    assert audit["lessons"]["hook_errors"] == 0
    assert any("fixture rival failure" in warning for warning in audit["warnings"])
    assert gsg.main([TASK, "--per-band", "2", "--lessons", "1", "--strict"]) == 1


def test_hookless_materialization_failure_is_not_a_pass(monkeypatch, tmp_path):
    _declared_only_fixture(monkeypatch, tmp_path, LESSON_COMPETITORS={"doubles": _declared_only_double})
    monkeypatch.setattr(gsg, "materialize_lessons", lambda *a, **kw: ([], ["fixture rejection"]))
    audit = gsg.audit_task(TASK, per_band=2, lessons=1)
    assert audit["status"] == "FAIL"
    assert audit["lessons"]["materialized"] == 0
    assert any("ZERO of 1 lessons materialized" in error for error in audit["errors"])
    assert not any("lesson_identifiable declared" in error for error in audit["errors"])


@pytest.mark.parametrize("attrs", [
    {}, {"LESSON_COMPETITORS": {}}, {"CANONICAL_SHORTCUTS": {}},
    {"SEMANTIC_RIVALS": {"doubles": _declared_only_double}},
])
def test_no_lesson_contract_preserves_legacy_advisory(monkeypatch, attrs):
    _install(monkeypatch, _gen_module(**attrs))

    def unexpected_materialization(*args, **kwargs):
        pytest.fail("a module with no lesson contract was materialized")

    monkeypatch.setattr(gsg, "materialize_lessons", unexpected_materialization)
    audit = gsg.audit_task(TASK, per_band=2, lessons=1)
    assert audit["status"] == "NO_CONTRACT"
    assert audit["errors"] == []
    assert audit["lessons"] is None
    required = gsg.audit_task(TASK, per_band=2, lessons=1, require_contract=True)
    assert required["status"] == "FAIL"


@pytest.mark.parametrize("declaration", ["LESSON_COMPETITORS", "CANONICAL_SHORTCUTS"])
def test_malformed_lesson_declaration_remains_a_failure(monkeypatch, declaration):
    _install(monkeypatch, _gen_module(**{declaration: {"not_callable": None}}))
    audit = gsg.audit_task(TASK, per_band=2, lessons=1)
    assert audit["status"] == "FAIL"
    assert audit["lessons"] is None
    assert any(declaration in error for error in audit["errors"])
