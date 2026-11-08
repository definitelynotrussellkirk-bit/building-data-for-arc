"""Native-contract tests for the marker-derived cycle-phase family."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
from reviewer_support import (
    canonical_pairs,
    find_root,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "f891d1ff5dd8"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID / "workspace" / "parametric"
DEFAULT = {"cycle_start": "first_header"}
MARKER = {"cycle_start": "row1_marker"}
SETTINGS = (DEFAULT, MARKER)


def _load(name: str):
    path = HOME / f"{name}.py"
    assert path.is_file(), f"missing native {name}: {path}"
    spec = importlib.util.spec_from_file_location(f"native_{TASK_ID}_{name}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def prototype():
    return _load("prototype")


@pytest.fixture(scope="module")
def adapter():
    return _load("adapter")


@pytest.fixture(scope="module")
def bridge():
    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    with RacketBridge() as live:
        assert live.runtime_identity["backend"] == "racket"
        assert live.runtime_identity["protected"] is True
        yield live


LITERAL_INPUT = [
    [2, 7, 4, 1, 8],
    [5, 5, 5, 5, 4],
    [0, 0, 0, 0, 0],
    [5, 5, 0, 0, 0],
    [0, 0, 0, 5, 5],
    [0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0],
]
CANONICAL_EXPECTED = [
    [2, 7, 4, 1, 8],
    [5, 5, 5, 5, 4],
    [2, 2, 2, 2, 2],
    [7, 7, 7, 7, 7],
    [4, 4, 4, 4, 4],
    [1, 1, 1, 1, 1],
    [8, 8, 8, 8, 8],
]
MARKER_EXPECTED = [
    [2, 7, 4, 1, 8],
    [5, 5, 5, 5, 4],
    [4, 4, 4, 4, 4],
    [1, 1, 1, 1, 1],
    [8, 8, 8, 8, 8],
    [2, 2, 2, 2, 2],
    [7, 7, 7, 7, 7],
]


def test_adapter_exposes_native_api_and_default_is_exact_canonical(adapter, prototype):
    canonical = prototype.canonical_source(root=ROOT)
    assert hashlib.sha256(canonical.encode()).hexdigest() == (
        "0f0bd2e42171cc41e580b5adbbde6c7dcd73b9efdc12ca822b6b99a6b7594363"
    )
    assert callable(adapter.program)
    assert callable(adapter.generate)
    assert adapter.program(DEFAULT) == canonical
    assert adapter.program(MARKER) != canonical


def test_python_solver_uses_header_index_not_marker_column(prototype):
    analysis = prototype.analyze(LITERAL_INPUT)
    assert analysis == {
        "marker_color": 4,
        "marker_column": 4,
        "marker_header_index": 2,
        "decoy_color": 5,
    }
    assert prototype.solve(LITERAL_INPUT, DEFAULT) == CANONICAL_EXPECTED
    assert prototype.solve(LITERAL_INPUT, MARKER) == MARKER_EXPECTED


def test_exact_racket_programs_match_literal_outputs(adapter, prototype, bridge):
    assert prototype.execute_rule(adapter.program(DEFAULT), LITERAL_INPUT, bridge=bridge) == (
        CANONICAL_EXPECTED
    )
    assert prototype.execute_rule(adapter.program(MARKER), LITERAL_INPUT, bridge=bridge) == (
        MARKER_EXPECTED
    )


@pytest.mark.parametrize(
    "settings",
    [
        None,
        {},
        {"cycle_start": "marker"},
        {"cycle_start": True},
        {"cycle_start": "first_header", "extra": 1},
    ],
)
def test_adapter_rejects_missing_unknown_or_untyped_settings(adapter, settings):
    with pytest.raises(ValueError):
        adapter.program(settings)
    with pytest.raises(ValueError):
        adapter.generate(0, settings, 2, 1)


@pytest.mark.parametrize(
    "seed,demos,queries",
    [
        (True, 2, 1),
        (-1, 2, 1),
        (2**63, 2, 1),
        (1.0, 2, 1),
        (0, True, 1),
        (0, 1, 1),
        (0, 7, 1),
        (0, 2.0, 1),
        (0, 2, True),
        (0, 2, 0),
        (0, 2, 5),
        (0, 2, 1.0),
    ],
)
def test_adapter_rejects_nonliteral_or_out_of_range_counts(
    adapter, seed, demos, queries
):
    with pytest.raises(ValueError):
        adapter.generate(seed, DEFAULT, demos, queries)


def _all_inputs(episode):
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def test_inputs_are_setting_neutral_distinct_and_prefix_stable(adapter):
    first = adapter.generate(17, DEFAULT, 2, 4)
    alternate = adapter.generate(17, MARKER, 2, 4)
    assert _all_inputs(first) == _all_inputs(alternate)
    assert len({json.dumps(grid) for grid in _all_inputs(first)}) == 6

    one = adapter.generate(17, DEFAULT, 2, 1)
    six = adapter.generate(17, DEFAULT, 6, 4)
    assert one["train"] == first["train"]
    assert one["test"] == first["test"][:1]
    assert six["train"][:2] == first["train"]
    assert six["test"] == first["test"]


def test_generated_grammar_has_one_row1_marker_and_real_30x30_stress(adapter, prototype):
    episode = adapter.generate(17, MARKER, 6, 4)
    phases = []
    for grid in _all_inputs(episode):
        info = prototype.analyze(grid)
        phases.append(info["marker_header_index"])
        assert info["marker_header_index"] != 0
        assert info["marker_column"] != info["marker_header_index"]
        assert sum(value == info["marker_color"] for value in grid[0]) == 1
        assert sum(value == info["marker_color"] for value in grid[1]) == 1
        assert all(type(value) is int and 0 <= value <= 9 for row in grid for value in row)
    assert len(set(phases[:2])) == 2

    large = episode["test"][3]["input"]
    assert (len(large), len(large[0])) == (30, 30)
    decoy = prototype.analyze(large)["decoy_color"]
    body_positions = [
        (r, c)
        for r, row in enumerate(large[2:], start=2)
        for c, value in enumerate(row)
        if value == decoy
    ]
    assert len(body_positions) >= 120
    assert {r < 16 for r, _ in body_positions} == {False, True}
    assert {c < 15 for _, c in body_positions} == {False, True}
    assert any(r in (2, 29) or c in (0, 29) for r, c in body_positions)


def test_two_demonstrations_identify_the_declared_setting(adapter, prototype):
    for chosen in SETTINGS:
        episode = adapter.generate(0, chosen, 2, 4)
        selected = [pair["output"] for pair in episode["train"]]
        survivors = []
        for candidate in SETTINGS:
            predicted = [prototype.solve(pair["input"], candidate) for pair in episode["train"]]
            if predicted == selected:
                survivors.append(candidate)
        assert survivors == [chosen]


def test_counterfactual_marker_column_is_a_wrong_intermediate(adapter, prototype, bridge):
    episode = adapter.generate(0, MARKER, 2, 4)
    pair = episode["test"][3]
    info = prototype.analyze(pair["input"])
    assert info["marker_header_index"] != info["marker_column"]
    correct = prototype.execute_rule(adapter.program(MARKER), pair["input"], bridge=bridge)
    wrong = prototype.execute_rule(
        prototype.counterfactual_program("marker_column"), pair["input"], bridge=bridge
    )
    assert correct == pair["output"]
    assert wrong != correct
    assert sum(a != b for ra, rb in zip(correct, wrong) for a, b in zip(ra, rb)) >= 30


def test_public_projection_hides_settings_program_future_queries_and_answers(
    adapter, prototype
):
    episode = adapter.generate(17, MARKER, 2, 4)
    public = prototype.public_challenge(episode, query_index=0)
    assert public == {
        "train": episode["train"],
        "test": [{"input": episode["test"][0]["input"]}],
    }
    original = public_challenge_bytes(public)
    assert public_challenge_id(public) == hashlib.sha256(original).hexdigest()

    changed = copy.deepcopy(episode)
    changed["settings"] = DEFAULT
    changed["program_solution"] = "PRIVATE"
    changed["test"][0]["output"] = [[9]]
    changed["test"][1:] = [{"input": [[8]], "output": [[7]]}]
    assert public_challenge_bytes(prototype.public_challenge(changed, query_index=0)) == original
    for invalid in (True, -1, 4, 0.0):
        with pytest.raises(ValueError):
            prototype.public_challenge(episode, query_index=invalid)


def test_canonical_default_replays_all_canonical_pairs(adapter, prototype, bridge):
    source = adapter.program(DEFAULT)
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert pairs
    for pair in pairs:
        assert prototype.execute_rule(source, pair["input"], bridge=bridge) == pair["output"]


def test_reusable_audit_finds_no_harmful_survivor_for_minimum_lessons(bridge):
    audit = _load("audit_native")
    report = audit.run_audit(seeds=[0], demo_counts=[2], queries=4, bridge=bridge)
    assert report["schema"] == "f891d1ff5dd8-marker-phase-audit-v1"
    assert report["episodes"] == 2
    assert report["harmful_survivors"] == []
    assert report["racket_evaluations"] >= 2 * 7 * 6


def test_public_writer_uses_hash_names_and_one_query_only(tmp_path):
    audit = _load("audit_native")
    written = audit.write_public_examples(tmp_path, seeds=[0], demos=2, queries=4)
    assert len(written) == 8
    for row in written:
        path = tmp_path / row["file"]
        assert path.name == row["public_id"] + ".json"
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row["public_id"]
        payload = json.loads(path.read_text())
        assert set(payload) == {"train", "test"}
        assert len(payload["train"]) == 2
        assert len(payload["test"]) == 1
        assert set(payload["test"][0]) == {"input"}
        assert "cycle_start" not in path.read_text()
        assert "program_solution" not in path.read_text()
