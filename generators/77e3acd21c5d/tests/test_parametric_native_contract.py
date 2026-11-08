"""Native promotion contract and count-neutral curriculum for tie policies."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "77e3acd21c5d"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID
PARAMETRIC = HOME / "workspace" / "parametric"


def load(name: str):
    path = PARAMETRIC / name
    spec = importlib.util.spec_from_file_location(f"native_{TASK_ID}_{path.stem}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def input_keys(episode):
    return [json.dumps(pair["input"], separators=(",", ":"))
            for pair in episode["train"] + episode["test"]]


def test_native_adapter_keeps_exact_canonical_default_and_nine_programs():
    prototype = load("prototype.py")
    adapter = load("adapter.py")
    promotion = json.loads((PARAMETRIC / "promotion.json").read_text())

    assert promotion["limits"] == {"demos": [2, 6], "queries": [1, 4]}
    assert promotion["default"] == {"row_ties": "both", "column_ties": "both"}
    programs = {
        adapter.program({"row_ties": row, "column_ties": column})
        for row in prototype.VALUES
        for column in prototype.VALUES
    }
    assert len(programs) == 9
    assert adapter.program(promotion["default"]) == prototype.canonical_program()
    assert (PARAMETRIC / "canonical.rkt").read_text() == prototype.canonical_program()


def test_counts_are_independent_prefix_stable_and_all_inputs_are_novel():
    adapter = load("adapter.py")
    settings = {"row_ties": "low", "column_ties": "high"}
    small = adapter.generate(20261025, settings, 2, 1)
    large = adapter.generate(20261025, settings, 6, 4)

    assert small["train"] == large["train"][:2]
    assert small["test"] == large["test"][:1]
    assert len(large["train"]) == 6 and len(large["test"]) == 4
    assert len(set(input_keys(large))) == 10
    assert any(len(pair["input"]) == 30 and len(pair["input"][0]) == 30
               for pair in large["test"])


@pytest.mark.parametrize("demos", [2, 3, 6])
@pytest.mark.parametrize("queries", [1, 4])
def test_all_supported_count_boundaries_generate_strict_integer_grids(demos, queries):
    adapter = load("adapter.py")
    episode = adapter.generate(
        91, {"row_ties": "high", "column_ties": "low"}, demos, queries
    )
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == queries
    for pair in episode["train"] + episode["test"]:
        for grid in (pair["input"], pair["output"]):
            assert grid and grid[0]
            assert all(type(cell) is int and 0 <= cell <= 9 for row in grid for cell in row)


@pytest.mark.parametrize("bad_demos,bad_queries", [
    (1, 4), (7, 4), (True, 4), (3, 0), (3, 5), (3, True),
])
def test_unsupported_counts_fail_closed(bad_demos, bad_queries):
    adapter = load("adapter.py")
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(
            0, {"row_ties": "both", "column_ties": "both"},
            bad_demos, bad_queries,
        )


def test_inputs_are_setting_neutral_and_first_two_demos_identify_every_setting():
    prototype = load("prototype.py")
    adapter = load("adapter.py")
    episodes = {}
    signatures = {}
    for parameters in prototype.ALL_PARAMETERS:
        settings = parameters.as_dict()
        episode = adapter.generate(777, settings, 2, 4)
        episodes[parameters.key] = episode
        signatures[parameters.key] = tuple(
            prototype.object_sha256(pair["output"]) for pair in episode["train"]
        )
    first_inputs = input_keys(next(iter(episodes.values())))
    assert all(input_keys(episode) == first_inputs for episode in episodes.values())
    assert len(set(signatures.values())) == len(prototype.ALL_PARAMETERS) == 9


def test_python_mirror_preserves_all_canonical_default_labels():
    prototype = load("prototype.py")
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert [prototype.python_mirror(pair["input"], prototype.DEFAULT) for pair in pairs] == [
        pair["output"] for pair in pairs
    ]


def test_public_projection_hides_settings_answers_and_future_queries():
    prototype = load("prototype.py")
    adapter = load("adapter.py")
    episode = adapter.generate(
        125, {"row_ties": "low", "column_ties": "high"}, 3, 4
    )
    first = prototype.public_challenge(episode, revealed_queries=1)
    full = prototype.public_challenge(episode, revealed_queries=4)
    assert first["train"] == full["train"]
    assert first["test"] == full["test"][:1]
    assert all(set(pair) == {"input"} for pair in full["test"])
    serialized = json.dumps(full, sort_keys=True)
    for secret in ("row_ties", "column_ties", "low", "high", "program_solution"):
        assert secret not in serialized


def test_reusable_lesson_audit_finds_no_declared_teaching_holes():
    audit = load("audit_lessons.py")
    report = audit.audit(seed_start=5, seed_count=1)
    assert report["status"] == "pass"
    assert report["summary"]["episodes"] == 1 * 9 * 5
    assert report["summary"]["harmful_rival_survivors"] == 0
    assert report["summary"]["exact_30x30_pairs"] == 1 * 9 * 5
