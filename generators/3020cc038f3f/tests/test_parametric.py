"""Focused behavioral tests for the native 3020cc038f3f parametric family."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"
REPO = HOME.parents[1]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


prototype = _load("_test_3020cc038f3f_parametric", PARAMETRIC / "prototype.py")
adapter = _load("_test_3020cc038f3f_adapter", PARAMETRIC / "adapter.py")


def _hand_grid(ctrl: int = 3) -> list[list[int]]:
    grid = [[0] * 10 for _ in range(7)]
    grid[0][0] = ctrl
    # Larger color-1 L: normalized {(0,0),(1,0),(2,0),(2,1),(2,2)}.
    for r, c in ((1, 1), (2, 1), (3, 1), (3, 2), (3, 3)):
        grid[r][c] = 1
    # Smaller color-2 corner: normalized {(0,0),(0,1),(1,1)}.
    for r, c in ((1, 6), (1, 7), (2, 7)):
        grid[r][c] = 2
    return grid


def test_program_binding_preserves_exact_canonical_default():
    sys.path.insert(0, str(REPO / "src"))
    from arcpuzzles import Catalog

    record = Catalog(REPO).get(prototype.TASK_ID)
    selected = {
        variant["program_solution"]
        for variant in record["variants"]
        if isinstance(variant.get("program_solution"), str)
    }
    assert len(selected) == 1
    canonical = next(iter(selected))
    assert prototype.program({"preprocess": "identity"}) == canonical
    assert adapter.program({"preprocess": "identity"}) == canonical
    assert prototype.program({"preprocess": "rotate_larger_cw"}) != canonical


@pytest.mark.parametrize(
    "settings,expected",
    [
        (
            {"preprocess": "identity"},
            [[8, 8, 0], [8, 8, 0], [8, 8, 8]],
        ),
        (
            {"preprocess": "rotate_larger_cw"},
            [[8, 8, 8], [8, 8, 0], [8, 0, 0]],
        ),
    ],
)
def test_hand_derived_union_outputs(settings, expected):
    grid = _hand_grid(3)
    original = copy.deepcopy(grid)
    assert prototype.transform(grid, settings) == expected
    assert grid == original


def test_wrong_intermediate_changes_the_hand_fixture_output():
    grid = _hand_grid(3)
    correct = prototype.transform(grid, {"preprocess": "rotate_larger_cw"})
    wrong = prototype.transform_with_selected_color(grid, selected_color=2)
    assert prototype.analyze_input(grid)["larger_color"] == 1
    assert correct != wrong


@pytest.mark.parametrize("demos", range(2, 7))
def test_generation_supports_all_demo_counts_and_four_prefix_stable_queries(demos):
    settings = {"preprocess": "rotate_larger_cw"}
    episode = prototype.generate(17, settings, demos=demos, queries=4)
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == 4
    all_inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
    frozen = [json.dumps(grid, separators=(",", ":")) for grid in all_inputs]
    assert len(frozen) == len(set(frozen))
    assert (len(episode["test"][3]["input"]), len(episode["test"][3]["input"][0])) == (30, 30)

    short_demos = prototype.generate(17, settings, demos=2, queries=4)
    one_query = prototype.generate(17, settings, demos=demos, queries=1)
    assert episode["train"][:2] == short_demos["train"]
    assert episode["test"][0] == one_query["test"][0]


def test_settings_receive_identical_inputs_and_demonstrations_refute_all_rivals():
    identity = prototype.generate(29, {"preprocess": "identity"}, demos=2, queries=4)
    rotated = prototype.generate(29, {"preprocess": "rotate_larger_cw"}, demos=2, queries=4)
    assert [p["input"] for p in identity["train"] + identity["test"]] == [
        p["input"] for p in rotated["train"] + rotated["test"]
    ]
    for setting, episode in (("identity", identity), ("rotate_larger_cw", rotated)):
        certificate = prototype.audit_episode(episode, setting)
        assert certificate["survivors"] == [{"preprocess": setting}]
        assert all(certificate["rival_refutations"].values())


def test_public_turn_exposes_only_visible_training_pairs_and_one_query_input():
    episode = prototype.generate(3, {"preprocess": "identity"}, demos=3, queries=4)
    public = prototype.public_turn(episode, 0)
    assert set(public) == {"train", "test"}
    assert public["train"] == episode["train"]
    assert public["test"] == [{"input": episode["test"][0]["input"]}]
    assert "program_solution" not in public
    assert "settings" not in public
    assert all(set(pair) == {"input"} for pair in public["test"])


def test_request_validation_rejects_bool_counts_unknown_settings_and_out_of_range_seed():
    valid = {"preprocess": "identity"}
    with pytest.raises((TypeError, ValueError)):
        prototype.generate(True, valid, 2, 1)
    with pytest.raises((TypeError, ValueError)):
        prototype.generate(0, valid, True, 1)
    with pytest.raises((TypeError, ValueError)):
        prototype.generate(0, valid, 2, 5)
    with pytest.raises((TypeError, ValueError)):
        prototype.generate(0, {"preprocess": "other"}, 2, 1)
    with pytest.raises((TypeError, ValueError)):
        prototype.generate(0, {"preprocess": "identity", "extra": 1}, 2, 1)


def test_structural_stress_audit_covers_all_settings_counts_and_public_turns():
    audit = _load("_test_3020cc038f3f_audit", PARAMETRIC / "audit.py")
    report = audit.structural_stress(seed_count=3)
    assert report["failures"] == []
    assert report["episodes"] == 3 * 5 * 2
    assert report["matched_input_checks"] == 3 * 5
    assert report["stress_30x30_checks"] == 3 * 5 * 2
    assert report["public_turn_checks"] == 3 * 5 * 2 * 4
