"""Prototype-only checks; canonical generator admission is a separate review."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import random

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "9971f3a5882c"
ROOT = find_root(__file__)


def _prototype():
    path = ROOT / "generators" / TASK_ID / "workspace/parametric/prototype.py"
    assert path.is_file(), "the requested isolated parametric prototype is missing"
    spec = importlib.util.spec_from_file_location("parametric_9971f3a5882c", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.Prototype(root=ROOT)


@pytest.fixture(scope="module")
def family():
    with _prototype() as instance:
        yield instance


def test_default_program_and_racket_outputs_preserve_canonical_authority():
    generator, _, _ = load_selected_generator(TASK_ID, root=ROOT)
    with _prototype() as family:
        assert family.program() == family.canonical_program
        normalized = hashlib.sha256(" ".join(family.program().split()).encode()).hexdigest()[:12]
        assert normalized == generator.RULE_HASH
        pairs = canonical_pairs(TASK_ID, root=ROOT)
        assert len(pairs) == 8
        for pair in pairs:
            assert family.apply(pair["input"]) == pair["output"]


@pytest.mark.parametrize("invalid", [True, 0, "outermost", ""])
def test_unknown_rule_settings_are_rejected(family, invalid):
    with pytest.raises(ValueError, match="marker_selection"):
        family.make_episode(2026, marker_selection=invalid)


def test_seed_selection_is_bounded_replayable_and_independent_of_global_rng(family):
    random.seed(98123)
    state = random.getstate()
    settings = [family.select_parameters(seed) for seed in range(64)]
    assert {item["marker_selection"] for item in settings} == {"nearest", "farthest"}
    assert settings == [family.select_parameters(seed) for seed in range(64)]
    assert random.getstate() == state
    with pytest.raises(ValueError, match="seed"):
        family.make_episode(True)


@pytest.mark.parametrize("setting", ["nearest", "farthest"])
def test_one_setting_governs_a_deterministic_complete_episode(family, setting):
    first = family.make_episode(19073, marker_selection=setting)
    second = family.make_episode(19073, marker_selection=setting)
    assert first == second
    assert first is not second
    assert first["parameters"] == {"marker_selection": setting}
    assert len(first["train"]) == 3 and len(first["test"]) == 1
    assert first["reference"]["racket_text"] == family.program(setting)
    for split in ("train", "test"):
        for pair in first[split]:
            assert pair["output"] == family.apply(pair["input"], setting)
    first["train"][0]["input"][0][0] = 9
    assert first != second


def test_all_four_extrema_and_marker_collisions_execute_as_declared(family):
    # This hand-built lawful grid deliberately covers double top/bottom cues,
    # which the selected generator's named double-marker profiles do not draw.
    grid = [[0] * 9 for _ in range(9)]
    for row in range(3, 6):
        for column in range(3, 6):
            if row in (3, 5) or column in (3, 5):
                grid[row][column] = 3
    markers = [(0, 4), (1, 4), (7, 4), (8, 4), (4, 0), (4, 1), (4, 7), (4, 8)]
    for row, column in markers:
        grid[row][column] = 6
    assert family.generator.self_check(grid) == []
    outputs = {}
    for setting, low, high in (("nearest", 2, 6), ("farthest", 1, 7)):
        expected = [[0] * 9 for _ in range(9)]
        for row in range(low, high + 1):
            for column in range(low, high + 1):
                if row in (low, high) or column in (low, high):
                    expected[row][column] = 3
        for row, column in markers:
            expected[row][column] = 6
        outputs[setting] = family.apply(grid, setting)
        assert outputs[setting] == expected
    assert outputs["nearest"] != outputs["farthest"]


@pytest.mark.parametrize("setting, bounds", [("nearest", (2, 7, 2, 9)), ("farthest", (1, 8, 1, 10))])
def test_internal_line_coordinates_stay_fixed_while_boundaries_move(family, setting, bounds):
    grid = [[0] * 12 for _ in range(10)]
    for row in range(3, 7):
        for column in range(3, 9):
            if row in (3, 5, 6) or column in (3, 6, 8):
                grid[row][column] = 3
    markers = [(0, 6), (1, 6), (8, 6), (9, 6), (5, 0), (5, 1), (5, 10), (5, 11)]
    for row, column in markers:
        grid[row][column] = 6
    r0, r1, c0, c1 = bounds
    expected = [[0] * 12 for _ in range(10)]
    for row in range(r0, r1 + 1):
        for column in range(c0, c1 + 1):
            if row in (r0, 5, r1) or column in (c0, 6, c1):
                expected[row][column] = 3
    for row, column in markers:
        expected[row][column] = 6
    assert family.apply(grid, setting) == expected


@pytest.mark.parametrize("setting", ["nearest", "farthest"])
def test_demonstrations_refute_the_wrong_setting_before_query_requires_it(family, setting):
    episode = family.make_episode(19073, marker_selection=setting)
    audit = family.audit_episode(episode)
    rival = "farthest" if setting == "nearest" else "nearest"
    assert audit["status"] == "no_ambiguity_found"
    assert audit["settings"][setting]["status"] == "survived_all"
    assert audit["settings"][rival]["status"] == "refuted_by_demonstrations"
    assert audit["settings"][rival]["mismatching_demo_positions"]
    assert audit["settings"][rival]["mismatching_query_positions"] == [0]


def test_intentional_diagnostic_is_harmfully_ambiguous(family):
    episode = family.make_episode(2718, marker_selection="nearest", mode="ambiguous_diagnostic")
    audit = family.audit_episode(episode)
    assert episode["mode"] == "ambiguous_diagnostic"
    assert audit["status"] == "ambiguous"
    rival = audit["settings"]["farthest"]
    assert rival["status"] == "harmful_ambiguity"
    assert rival["mismatching_demo_positions"] == []
    assert rival["mismatching_query_positions"] == [0]


def test_answer_equivalent_surviving_setting_is_not_harmful_ambiguity(family):
    episode = family.make_episode(2718, marker_selection="nearest", mode="equivalent_control")
    audit = family.audit_episode(episode)
    assert audit["status"] == "no_ambiguity_found"
    assert {item["status"] for item in audit["settings"].values()} == {"survived_all"}


def test_audit_rejects_labels_inconsistent_with_both_declared_settings(family):
    episode = family.make_episode(2718, marker_selection="nearest", mode="equivalent_control")
    episode["train"][0]["output"][0][0] = 9
    with pytest.raises(ValueError, match="no declared setting"):
        family.audit_episode(episode)


def test_public_challenge_is_an_allowlist_without_rule_or_query_labels(family):
    episode = family.make_episode(19073, marker_selection="farthest")
    episode["accidental_private_metadata"] = "nearest farthest secret"
    challenge = family.public_challenge(episode)
    assert set(challenge) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in challenge["train"])
    assert all(set(pair) == {"input"} for pair in challenge["test"])
    serialized = json.dumps(challenge)
    assert all(word not in serialized for word in ("parameters", "reference", "racket", "seed", "nearest", "farthest", "secret"))
    challenge["train"][0]["input"][0][0] = 9
    assert challenge["train"][0]["input"] != episode["train"][0]["input"]


def test_private_verification_replays_and_rejects_stale_sources_or_tampered_labels(family):
    episode = family.make_episode(42, marker_selection="farthest")
    assert family.verify_episode(episode)["status"] == "verified"
    changed = deepcopy(episode)
    key = next(iter(changed["source_bindings"]))
    changed["source_bindings"][key] = "0" * 64
    with pytest.raises(ValueError, match="source binding"):
        family.verify_episode(changed)
    changed = deepcopy(episode)
    changed["reference"]["racket_text"] = family.program("nearest")
    with pytest.raises(ValueError, match="reference"):
        family.verify_episode(changed)
    changed = deepcopy(episode)
    changed["test"][0]["output"][0][0] = 9
    with pytest.raises(ValueError, match="replay"):
        family.verify_episode(changed)
