from __future__ import annotations

import json
from pathlib import Path
import sys
import types

import pytest

PARAMETRIC_ROOT = (
    Path(__file__).resolve().parents[1] / "workspace" / "parametric"
)
sys.path.insert(0, str(PARAMETRIC_ROOT))

from compression_family import (
    CANONICAL_PARAMETERS,
    PythonMirrorOracle,
    RacketOracle,
    all_settings,
    build_episode,
    materialize_program,
    python_apply,
    write_episode,
)


def expanded_fixture():
    logical = [[1, 2, 3], [4, 5, 6]]
    row_spans = [2, 3]
    col_spans = [2, 3, 2]
    return [
        [value for value, span in zip(row, col_spans) for _ in range(span)]
        for row, rspan in zip(logical, row_spans)
        for _ in range(rspan)
    ]


def test_six_programs_are_closed_and_distinct():
    programs = [materialize_program(**setting) for setting in all_settings()]
    assert len(programs) == len(set(programs)) == 6
    assert all(program.startswith("(rule! (lambda (g)") for program in programs)
    assert all(program.count("(rule!") == 1 for program in programs)


def test_canonical_member_matches_compression_rule():
    grid = expanded_fixture()
    assert python_apply(grid, **CANONICAL_PARAMETERS) == [[1, 2, 3], [4, 5, 6]]


def test_axes_and_orientation_have_independent_effects():
    grid = expanded_fixture()
    both = python_apply(grid, compression_axes="both", output_orientation="identity")
    rows = python_apply(grid, compression_axes="rows", output_orientation="identity")
    columns = python_apply(grid, compression_axes="columns", output_orientation="identity")
    transpose = python_apply(grid, compression_axes="both", output_orientation="transpose")
    assert both == [[1, 2, 3], [4, 5, 6]]
    assert len(rows) == 2 and len(rows[0]) == 7
    assert len(columns) == 5 and len(columns[0]) == 3
    assert transpose == [[1, 4], [2, 5], [3, 6]]


def test_episode_has_four_distinct_queries_and_no_private_leakage(tmp_path):
    episode = build_episode(
        seed=20261023,
        chosen=CANONICAL_PARAMETERS,
        oracle=PythonMirrorOracle(),
        demo_count=4,
        query_count=4,
    )
    public = episode["public"]
    private = episode["private"]
    assert len(public["train"]) == 4
    assert len(public["test"]) == 4
    assert all(set(item) == {"input"} for item in public["test"])
    keys = {json.dumps(item["input"], sort_keys=True) for item in public["test"]}
    assert len(keys) == 4
    serialized_public = json.dumps(public, sort_keys=True)
    assert "compression_axes" not in serialized_public
    assert "output_orientation" not in serialized_public
    assert "program" not in serialized_public
    assert private["rivals_refuted_by_demos"]
    paths = write_episode(episode, tmp_path)
    exact_visible = json.dumps(public, sort_keys=True, separators=(",", ":"))
    import hashlib
    expected = hashlib.sha256(exact_visible.encode()).hexdigest()
    assert paths["public"].name == f"challenge-{expected[:16]}.json"


def test_racket_programs_match_independent_python_mirror_when_available():
    pytest.importorskip("arc_repl.racket_bridge")
    grid = expanded_fixture()
    with RacketOracle() as oracle:
        for setting in all_settings():
            assert oracle.apply(materialize_program(**setting), grid) == python_apply(grid, **setting)


def test_racket_adapter_uses_packet_bridge_contract(monkeypatch):
    calls = []

    class FakeBridge:
        def __init__(self, prelude_path=None, timeout=10.0):
            calls.append(("init", prelude_path, timeout))

        def eval_text(self, expression):
            calls.append(("eval_text", expression))
            if expression.startswith("(define "):
                return None
            return [[9]]

        def define_grid(self, name, grid):
            calls.append(("define_grid", name, grid))

        def shutdown(self):
            calls.append(("shutdown",))

    bridge_module = types.ModuleType("arc_repl.racket_bridge")
    bridge_module.RacketBridge = FakeBridge
    wrapper_module = types.ModuleType("puzzle_generators.rule_wrap")
    wrapper_module.strip_rule_wrapper = lambda program: "(lambda (g) g)"
    monkeypatch.setitem(sys.modules, "arc_repl.racket_bridge", bridge_module)
    monkeypatch.setitem(sys.modules, "puzzle_generators.rule_wrap", wrapper_module)

    with RacketOracle(timeout_s=3.5) as oracle:
        assert oracle.apply("(rule! (lambda (g) g))", [[1]]) == [[9]]

    assert calls[0] == ("init", None, 3.5)
    assert any(call[0] == "define_grid" and call[2] == [[1]] for call in calls)
    assert calls[-1] == ("shutdown",)
