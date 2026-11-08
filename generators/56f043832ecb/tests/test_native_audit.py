"""Focused serialization rejection and finite-rival audit contracts.

Bookkeeping tests use an explicitly fake executor. The boundary-rival regression
and the audit CLI use the live protected Racket evaluator.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest


HOME = Path(__file__).resolve().parents[1]
AUDIT = HOME / "workspace" / "parametric" / "audit.py"


@pytest.fixture(scope="module")
def audit():
    assert AUDIT.is_file(), "The native audit/export implementation must exist"
    spec = importlib.util.spec_from_file_location("_test_hole_area_audit", AUDIT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _episode():
    return {"seed": 0, "settings": {"selection": "all"},
            "program": "(rule! (lambda (g) g))",
            "train": [{"input": [[i]], "output": [[i]]} for i in (1, 2, 3)],
            "test": [{"input": [[i]], "output": [[i]]} for i in (4, 5, 6, 7)]}


@pytest.fixture
def exported(audit, tmp_path):
    path = tmp_path / "turns"
    audit.export_episodes([_episode()], path, source_snapshot={"fixture.py": "0" * 64},
                          racket={"backend": "test", "protected": False})
    return path


def _json(path):
    return json.loads(path.read_text())


def _write(path, value):
    path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")


def _rehash(path):
    """Update transport hashes so malformed semantics cannot hide behind them."""
    manifest = _json(path / "manifest.json")
    for row in manifest["files"]:
        row["sha256"] = hashlib.sha256((path / row["path"]).read_bytes()).hexdigest()
    _write(path / "manifest.json", manifest)


def test_four_exact_single_query_files_and_stable_first_turn(audit, exported):
    result = audit.verify_export(exported)
    assert result["episodes"] == 1 and result["public_files"] == 4
    private = _json(exported / "private" / "episodes.json")
    episode = private["episodes"][0]
    assert len(episode["turn_ids"]) == 4
    for index, content_id in enumerate(episode["turn_ids"]):
        raw = (exported / "public" / f"{content_id}.json").read_bytes()
        assert hashlib.sha256(raw).hexdigest() == content_id
        visible = _json(exported / "public" / f"{content_id}.json")
        assert set(visible) == {"train", "test"}
        assert visible == {"train": episode["train"],
                           "test": [{"input": episode["test"][index]["input"]}]}
    expected = audit.public_challenge_bytes({"train": episode["train"],
                                            "test": episode["test"][:1]})
    assert (exported / "public" / f"{episode['turn_ids'][0]}.json").read_bytes() == expected


@pytest.mark.parametrize("location", ("top", "query", "demonstration"))
def test_rejects_private_field_leaks_even_with_rehashed_files(audit, exported, location):
    path = next((exported / "public").glob("*.json"))
    value = _json(path)
    if location == "top":
        value["settings"] = {"selection": "all"}
    elif location == "query":
        value["test"][0]["output"] = [[9]]
    else:
        value["train"][0]["program"] = "private"
    _write(path, value)
    _rehash(exported)
    with pytest.raises(ValueError):
        audit.verify_export(exported)


@pytest.mark.parametrize("grid", ([[True]], [[0.0]], [[0], [0, 0]], [[]], [[0] * 31]))
def test_rejects_non_arc_private_grids(audit, exported, grid):
    path = exported / "private" / "episodes.json"
    value = _json(path)
    value["episodes"][0]["test"][0]["output"] = grid
    _write(path, value)
    _rehash(exported)
    with pytest.raises(ValueError):
        audit.verify_export(exported)


def test_rejects_query_projection_change_after_rehash(audit, exported):
    path = exported / "private" / "episodes.json"
    value = _json(path)
    value["episodes"][0]["test"][0]["input"] = [[8]]
    _write(path, value)
    _rehash(exported)
    with pytest.raises(ValueError):
        audit.verify_export(exported)


@pytest.mark.parametrize("change", ("missing", "duplicate", "orphan", "count", "program", "file_hash"))
def test_rejects_broken_coverage_inventory_and_hashes(audit, exported, change):
    manifest_path = exported / "manifest.json"
    manifest = _json(manifest_path)
    private_path = exported / "private" / "episodes.json"
    private = _json(private_path)
    episode = private["episodes"][0]
    if change == "missing":
        (exported / "public" / f"{episode['turn_ids'][0]}.json").unlink()
    elif change == "duplicate":
        episode["turn_ids"][1] = episode["turn_ids"][0]
        _write(private_path, private)
        _rehash(exported)
    elif change == "orphan":
        (exported / "public" / ("f" * 64 + ".json")).write_text("{}\n")
    elif change == "count":
        manifest["counts"]["public_files"] = 3
        _write(manifest_path, manifest)
    elif change == "program":
        episode["program"] += " "
        _write(private_path, private)
        _rehash(exported)
    else:
        manifest["files"][0]["sha256"] = "f" * 64
        _write(manifest_path, manifest)
    with pytest.raises(ValueError):
        audit.verify_export(exported)


def test_export_refuses_existing_destination_and_duplicate_visible_turns(audit, exported, tmp_path):
    kwargs = {"source_snapshot": {}, "racket": {"backend": "test", "protected": False}}
    with pytest.raises(ValueError):
        audit.export_episodes([_episode()], exported, **kwargs)
    target = tmp_path / "duplicates"
    with pytest.raises(ValueError):
        audit.export_episodes([_episode(), _episode()], target, **kwargs)
    assert not target.exists()


def test_demo_consistent_query_disagreement_is_an_audit_failure(audit):
    def execute(program, grid):
        return [[9]] if grid == [[6]] else copy.deepcopy(grid)

    result = audit.audit_rivals(_episode(), [{"name": "plausible", "program": "rival",
                                            "description": "test rival"}], execute)
    assert result["passed"] is False
    rival = result["rivals"][0]
    assert rival["status"] == "query_disagreement"
    assert rival["first_refuting_demo"] is None
    assert rival["first_disagreeing_query"] == 2
    assert len(rival["demo_outputs"]) == 3 and len(rival["query_outputs"]) == 4


def test_execution_error_cannot_count_as_refuting_evidence(audit):
    seen = []

    def execute(program, grid):
        seen.append(copy.deepcopy(grid))
        if grid == [[2]]:
            raise RuntimeError("intentional evaluator failure")
        return [[9]]

    result = audit.audit_rivals(_episode(), [{"name": "broken", "program": "rival",
                                            "description": "test rival"}], execute)
    assert result["passed"] is False
    assert result["rivals"][0]["status"] == "execution_error"
    assert result["rivals"][0]["first_refuting_demo"] is None
    assert seen == [[[1]], [[2]], [[3]]]


def test_all_demos_are_evaluated_and_first_refutation_is_retained(audit):
    seen = []

    def execute(program, grid):
        seen.append(grid)
        return [[8]] if grid != [[1]] else [[1]]

    result = audit.audit_rivals(_episode(), [{"name": "wrong", "program": "rival",
                                            "description": "test rival"}], execute)
    rival = result["rivals"][0]
    assert result["passed"] is True and rival["status"] == "refuted"
    assert rival["first_refuting_demo"] == 1
    assert rival["program"] == "rival" and len(rival["demo_outputs"]) == 3
    assert seen == [[[1]], [[2]], [[3]]]


def test_survivor_agreeing_with_all_queries_is_only_finite_consistent(audit):
    result = audit.audit_rivals(_episode(), [{"name": "equivalent_on_batch", "program": "rival",
                                            "description": "test rival"}], lambda p, g: g)
    assert result["passed"] is True
    assert result["rivals"][0]["status"] == "finite_consistent"
    assert len(result["rivals"][0]["query_outputs"]) == 4


def test_evaluator_memoizes_exact_program_and_input_and_returns_copies(audit):
    calls = []

    def execute(program, grid):
        calls.append((program, copy.deepcopy(grid)))
        return grid

    cached = audit.MemoizedEvaluator(execute)
    first = cached("same", [[1]])
    first[0][0] = 9
    assert cached("same", [[1]]) == [[1]]
    assert len(calls) == 1
    assert cached("different", [[1]]) == [[1]]
    assert len(calls) == 2


def test_boundary_rivals_distinguish_interior_and_border_targets(audit):
    """Keep both directions of the observed location shortcut executable."""
    native = audit._load_native()
    variants = [{row["name"]: row["program"] for row in audit.make_rivals(native, setting)}
                for setting in native.SETTINGS]
    assert all("border_only" in rows and "skip_border" in rows for rows in variants)
    grid = [[0] * 9 for _ in range(7)]
    for row, col, color in ((0, 0, 2), (2, 5, 3)):
        for r in range(row, row + 3):
            for c in range(col, col + 3):
                if r in (row, row + 2) or c in (col, col + 2):
                    grid[r][c] = color
    border_expected = copy.deepcopy(grid)
    border_expected[1][1] = 2
    interior_expected = copy.deepcopy(grid)
    interior_expected[3][6] = 3
    with audit._local_imports(audit.RUNTIME, audit.HOME):
        execute, identity, bridge = audit._real_evaluator(audit.RUNTIME)
        try:
            assert identity["backend"] == "racket" and identity["protected"] is True
            for programs in variants:
                assert execute(programs["border_only"], grid) == border_expected
                assert execute(programs["skip_border"], grid) == interior_expected
        finally:
            bridge.close()
