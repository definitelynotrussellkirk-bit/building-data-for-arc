"""Focused contracts for the native rotation/component parametric family."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import find_root

TASK_ID = "9db8deba5903"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID / "workspace" / "parametric"
MODES = ("canonical", "largest_tiled_component")

FIXTURE_INPUT = [
    [8, 0, 0, 0, 1, 1],
    [0, 0, 0, 0, 1, 1],
    [0, 0, 1, 1, 0, 0],
    [0, 0, 1, 0, 8, 0],
    [1, 0, 0, 0, 0, 0],
    [1, 0, 0, 0, 0, 8],
]
FIXTURE_CANONICAL = [
    [8, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 8],
    [0, 0, 0, 0, 1, 1, 1, 1, 0, 8, 0, 0],
    [0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0],
    [0, 0, 1, 0, 8, 0, 0, 0, 1, 1, 0, 0],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [1, 0, 0, 0, 0, 8, 8, 0, 0, 0, 1, 1],
    [8, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 8],
    [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
    [0, 8, 0, 1, 0, 0, 0, 0, 1, 1, 0, 0],
    [0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 0, 0],
    [1, 1, 0, 0, 0, 0, 0, 0, 8, 0, 1, 1],
    [1, 1, 0, 0, 0, 8, 8, 0, 0, 0, 1, 1],
]
FIXTURE_RELAY = [
    [8, 0, 0, 0, 9, 9, 9, 9, 0, 0, 0, 8],
    [0, 0, 0, 0, 9, 9, 9, 9, 0, 8, 0, 0],
    [0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0],
    [0, 0, 1, 0, 8, 0, 0, 0, 1, 1, 0, 0],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [1, 0, 0, 0, 0, 8, 8, 0, 0, 0, 1, 1],
    [8, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 8],
    [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
    [0, 8, 0, 1, 0, 0, 0, 0, 1, 1, 0, 0],
    [0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 0, 0],
    [1, 1, 0, 0, 0, 0, 0, 0, 8, 0, 1, 1],
    [1, 1, 0, 0, 0, 8, 8, 0, 0, 0, 1, 1],
]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _prototype():
    return _load("rotation_component_parametric_prototype_tests", HOME / "prototype.py")


def _adapter():
    return _load("rotation_component_parametric_adapter_tests", HOME / "adapter.py")


def _canonical_program() -> str:
    rows = [
        json.loads(line)
        for line in (ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl")
        .read_text()
        .splitlines()
    ]
    programs = {
        row["program_solution"]
        for row in rows
        if row.get("task_id") == TASK_ID and row.get("program_solution")
    }
    assert len(programs) == 1
    return next(iter(programs))


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_native_entrypoints_and_contract_exist():
    assert (HOME / "adapter.py").is_file()
    assert (HOME / "prototype.py").is_file()
    contract = json.loads((HOME / "promotion.json").read_text())
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"mode": list(MODES)},
        "default": {"mode": "canonical"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "resources": [
            f"generators/{TASK_ID}/workspace/parametric/prototype.py",
            f"generators/{TASK_ID}/workspace/parametric/rules/canonical.rkt",
            f"generators/{TASK_ID}/workspace/parametric/rules/largest_tiled_component.rkt",
        ],
    }


def test_default_program_is_byte_exact_canonical():
    adapter = _adapter()
    assert adapter.program({"mode": "canonical"}) == _canonical_program()
    assert (HOME / "rules" / "canonical.rkt").read_text() == _canonical_program()
    assert adapter.program({"mode": "largest_tiled_component"}) != _canonical_program()


def test_literal_fixture_defines_the_two_stage_semantics():
    prototype = _prototype()
    assert prototype.tile_rotations(FIXTURE_INPUT) == FIXTURE_CANONICAL
    assert prototype.solve(FIXTURE_INPUT, "canonical") == FIXTURE_CANONICAL
    assert prototype.solve(FIXTURE_INPUT, "largest_tiled_component") == FIXTURE_RELAY
    facts = prototype.analyze(FIXTURE_INPUT)
    assert facts["component_sizes"] == [8, 4, 4, 4, 3, 3, 3, 3, 2, 2]
    assert facts["winner_size"] == 8
    assert facts["winner_cells"] == [
        [0, 4], [0, 5], [0, 6], [0, 7],
        [1, 4], [1, 5], [1, 6], [1, 7],
    ]


@pytest.mark.parametrize("seed", [0, 17, 91])
def test_inputs_match_across_modes_and_prefixes_are_stable(seed):
    adapter = _adapter()
    full = {
        mode: adapter.generate(seed, {"mode": mode}, demos=6, queries=4)
        for mode in MODES
    }
    assert _inputs(full[MODES[0]]) == _inputs(full[MODES[1]])
    assert len({json.dumps(grid) for grid in _inputs(full[MODES[0]])}) == 10
    for mode, baseline in full.items():
        for demos in range(2, 7):
            for queries in range(1, 5):
                episode = adapter.generate(seed, {"mode": mode}, demos=demos, queries=queries)
                assert episode["train"] == baseline["train"][:demos]
                assert episode["test"] == baseline["test"][:queries]
                assert episode["program_solution"] == adapter.program({"mode": mode})


@pytest.mark.parametrize("seed", [0, 17, 91])
@pytest.mark.parametrize("mode", MODES)
def test_first_two_demos_identify_mode_and_reject_declared_rivals(seed, mode):
    prototype = _prototype()
    adapter = _adapter()
    episode = adapter.generate(seed, {"mode": mode}, demos=2, queries=4)
    survivors = [
        candidate
        for candidate in MODES
        if all(prototype.solve(pair["input"], candidate) == pair["output"]
               for pair in episode["train"])
    ]
    assert survivors == [mode]
    for name, rival in prototype.audit_rivals(mode).items():
        assert any(rival(pair["input"]) != pair["output"] for pair in episode["train"]), name
        assert any(rival(pair["input"]) != pair["output"] for pair in episode["test"]), name


def test_wrong_intermediate_changes_the_final_answer():
    prototype = _prototype()
    intended = prototype.solve(FIXTURE_INPUT, "largest_tiled_component")
    wrong = prototype.solve_with_repeat_identity_intermediate(FIXTURE_INPUT)
    assert wrong != intended
    assert sum(cell == 9 for row in intended for cell in row) == 8
    assert sum(cell == 9 for row in wrong for cell in row) == 4


def test_fourth_query_is_a_substantive_30_by_30_output():
    adapter = _adapter()
    prototype = _prototype()
    episode = adapter.generate(20261024, {"mode": "largest_tiled_component"}, demos=3, queries=4)
    pair = episode["test"][3]
    assert (len(pair["input"]), len(pair["input"][0])) == (15, 15)
    assert (len(pair["output"]), len(pair["output"][0])) == (30, 30)
    occupied = {(r, c) for r, row in enumerate(pair["input"]) for c, value in enumerate(row) if value}
    assert len(occupied) >= 35
    assert len({r for r, _ in occupied}) >= 10
    assert len({c for _, c in occupied}) >= 10
    assert any(r in (0, 14) or c in (0, 14) for r, c in occupied)
    facts = prototype.analyze(pair["input"])
    assert facts["winner_size"] == 8
    assert facts["seam_component_sizes"][:2] == [8, 4]


@pytest.mark.parametrize(
    "settings",
    [None, {}, [], {"mode": True}, {"mode": "unknown"}, {"mode": "canonical", "extra": 1}],
)
def test_invalid_settings_reject(settings):
    adapter = _adapter()
    with pytest.raises((TypeError, ValueError)):
        adapter.program(settings)
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(0, settings, demos=3, queries=4)


@pytest.mark.parametrize(
    "seed,demos,queries",
    [
        (True, 3, 4), (-1, 3, 4), (2**63, 3, 4),
        (0, True, 4), (0, 1, 4), (0, 7, 4),
        (0, 3, True), (0, 3, 0), (0, 3, 5),
    ],
)
def test_invalid_request_controls_reject(seed, demos, queries):
    adapter = _adapter()
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(seed, {"mode": "canonical"}, demos=demos, queries=queries)


def test_public_projection_and_identifier_ignore_private_fields_and_answers():
    prototype = _prototype()
    episode = prototype.generate_episode(77, mode="largest_tiled_component", demos=3, queries=4)
    public = prototype.public_projection(episode)
    assert public == {
        "train": episode["train"],
        "test": [{"input": pair["input"]} for pair in episode["test"]],
    }
    identifier = prototype.public_challenge_id(episode)
    altered = copy.deepcopy(episode)
    altered["settings"] = {"mode": "canonical"}
    altered["program_solution"] = "private change"
    for pair in altered["test"]:
        pair["output"] = [[9]]
    assert prototype.public_projection(altered) == public
    assert prototype.public_challenge_id(altered) == identifier
