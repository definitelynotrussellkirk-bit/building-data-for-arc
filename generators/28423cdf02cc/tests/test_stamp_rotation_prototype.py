"""Behavioral checks for the separately proposed episode-level rule variant."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TASK_ID = "28423cdf02cc"
ROOT = find_root(__file__)


@pytest.fixture(scope="module")
def prototype():
    # Task-test snapshots retain the authoring workspace in the repository
    # mirror, separately from the selected generator's legacy execution path.
    path = ROOT / "generators" / TASK_ID / "workspace/parametric/stamp_rotation.py"
    assert path.is_file(), "The requested runnable rotation prototype is missing"
    spec = importlib.util.spec_from_file_location("stamp_rotation_prototype", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def bridge():
    from arc_repl.racket_bridge import RacketBridge
    with RacketBridge() as runtime:
        yield runtime


def test_default_rule_is_exact_canonical_text(prototype):
    rows = [json.loads(line) for line in canonical_path(ROOT).read_text().splitlines()]
    original = next(row["program_solution"] for row in rows if row["task_id"] == TASK_ID)
    assert prototype.materialize_rule(0, root=ROOT) == original


def test_default_racket_rule_reproduces_every_canonical_output(prototype, bridge):
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    outputs = prototype.label_settings([p["input"] for p in pairs], root=ROOT, bridge=bridge)
    assert outputs[0] == [p["output"] for p in pairs]


@pytest.mark.parametrize("turns", [0, 1, 2, 3])
def test_racket_rotation_changes_only_copies_and_matches_explicit_indexing(prototype, bridge, turns):
    generator, _, _ = load_selected_generator(TASK_ID, root=ROOT)
    grid = generator.generate(29, 2, difficulty="hard")
    before = [row[:] for row in grid]
    output = prototype.label_settings([grid], root=ROOT, bridge=bridge)[turns][0]
    template = [row[:3] for row in grid[:3]]
    expected_templates = [
        template,
        [[template[2-c][r] for c in range(3)] for r in range(3)],
        [[template[2-r][2-c] for c in range(3)] for r in range(3)],
        [[template[c][2-r] for c in range(3)] for r in range(3)],
    ]
    stamp = expected_templates[turns]
    expected = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color == 1:
                for pr in range(3):
                    for pc in range(3):
                        expected[r-1+pr][c-1+pc] = stamp[pr][pc]
    assert output == expected
    assert grid == before
    assert [row[:4] for row in output] == [row[:4] for row in grid]


@pytest.mark.parametrize("value", [True, False, -1, 4, 1.5, "1", None])
def test_rule_parameter_rejects_invalid_values(prototype, value):
    with pytest.raises((TypeError, ValueError)):
        prototype.materialize_rule(value, root=ROOT)


def test_finite_setting_checker_detects_hidden_query_ambiguity(prototype):
    a, b, c = [[0]], [[1]], [[2]]
    report = prototype.assess_settings(0, {0: [a, a, a, b], 1: [a, a, a, c]})
    assert report["production"]["ambiguous_settings"] == [1]
    assert not report["production"]["parameter_identified"]
    assert report["rotations"][3]["ambiguous_settings"] == [1]
    assert all(not row["ambiguous_settings"] for row in report["rotations"][:3])


def test_setting_checker_does_not_call_equivalent_settings_identified(prototype):
    a = [[0]]
    report = prototype.assess_settings(0, {0: [a]*4, 1: [a]*4})
    assert report["production"]["ambiguous_settings"] == []
    assert report["production"]["equivalent_settings"] == [1]
    assert not report["production"]["parameter_identified"]


@pytest.mark.parametrize("turns", [0, 1, 2, 3])
def test_complete_episode_is_fixed_rule_identifiable_and_public_safe(prototype, bridge, turns):
    episode = prototype.generate_episode(17, quarter_turns=turns, difficulty="medium",
                                         start_index=3, root=ROOT, bridge=bridge)
    public, private = episode["public"], episode["private"]
    assert set(public) == {"train", "test"}
    assert len(public["train"]) == 3 and len(public["test"]) == 1
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert set(public["test"][0]) == {"input"}
    assert private["parameters"] == {"quarter_turns": turns}
    assert private["sample_indices"] == [3, 4, 5, 6]
    assert private["training_admitted"] is False
    assert private["status"] == "prototype"
    report = private["setting_check"]
    assert report["production"]["parameter_identified"]
    assert all(row["parameter_identified"] for row in report["rotations"])
    inputs = [p["input"] for p in public["train"] + public["test"]]
    all_labels = prototype.label_settings(inputs, root=ROOT, bridge=bridge)
    assert [p["output"] for p in public["train"]] == all_labels[turns][:3]
    assert private["test_outputs"] == all_labels[turns][3:]
    assert all(len({json.dumps(all_labels[t][i]) for t in range(4)}) == 4
               for i in range(4))


def test_seed_selection_is_deterministic_and_inputs_do_not_encode_setting(prototype, bridge):
    first = prototype.generate_episode(23, root=ROOT, bridge=bridge)
    again = prototype.generate_episode(23, root=ROOT, bridge=bridge)
    assert first == again
    alternate = prototype.generate_episode(23, quarter_turns=(first["private"]["parameters"]["quarter_turns"]+1)%4,
                                           root=ROOT, bridge=bridge)
    assert [p["input"] for p in first["public"]["train"]+first["public"]["test"]] == [
        p["input"] for p in alternate["public"]["train"]+alternate["public"]["test"]]
    assert first["public"]["train"][0]["output"] != alternate["public"]["train"][0]["output"]


@pytest.mark.parametrize("kwargs", [{"seed": True}, {"seed": 1.5},
                                    {"seed": 0, "start_index": -1},
                                    {"seed": 0, "start_index": True},
                                    {"seed": 0, "difficulty": "expert"}])
def test_episode_rejects_invalid_controls_before_labeling(prototype, kwargs):
    with pytest.raises((TypeError, ValueError)):
        prototype.generate_episode(**kwargs, root=ROOT)
