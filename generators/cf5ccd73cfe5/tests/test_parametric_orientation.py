"""Focused prototype scope, separate from canonical generator repair checks."""
from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("task_orientation", HOME / "workspace/parametric/orientation.py")
p = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(p)


@pytest.fixture(scope="module")
def bridge():
    from arc_repl.racket_bridge import RacketBridge
    with RacketBridge() as live:
        yield live


@pytest.fixture(scope="module")
def episodes(bridge):
    return {s: p.build_episode(17, bridge, s) for s in p.SETTINGS}


def test_default_program_is_exact_canonical_and_matches_all_eight_pairs(bridge):
    rows = p.canonical_rows()
    assert p.program() == rows[0]["program_solution"]
    assert p.program() == p.program("identity")
    count = 0
    for row in rows:
        assert row["program_solution"] == p.program()
        for split in ("train", "test"):
            for pair in row.get(split, []):
                assert p.execute(bridge, p.program(), pair["input"]) == pair["output"]
                count += 1
    assert count == 8


def test_program_edits_are_exactly_one_membership_change():
    original = p.program()
    for setting in p.SETTINGS[1:]:
        text = p.program(setting)
        row = "(- marker-h 1 mr)" if setting in ("flip_ud", "rot180") else "mr"
        col = "(- marker-w 1 mc)" if setting in ("flip_lr", "rot180") else "mc"
        assert text == original.replace(p.LOOKUP, f"(hash-has-key? marker-set (list {row} {col}))")
    with pytest.raises(ValueError, match="unsupported orientation"):
        p.program("rot90")


@pytest.mark.parametrize("setting", p.SETTINGS)
def test_all_settings_have_identifiable_racket_labeled_episodes(episodes, setting):
    public, private = episodes[setting]
    assert len(public["train"]) == 3 and len(public["test"]) == 1
    assert private["parameters"] == {"orientation": setting}
    assert private["seed"] == 17
    for pair, source in zip(public["train"], private["accepted"]):
        assert pair == {"input": source["input"], "output": source["outputs"][setting]}
        assert not p.equal_groups(source["outputs"])
    assert private["query_outputs"] == [private["accepted"][3]["outputs"][setting]]
    assert set(private["rivals"]) == set(p.SETTINGS) - {setting}
    for rival in private["rivals"].values():
        assert rival == {"demo_mismatches": [0, 1, 2], "query_differs": [True]}


def test_public_challenge_is_exactly_demo_pairs_and_query_inputs(episodes):
    for public, private in episodes.values():
        assert set(public) == {"train", "test"}
        assert all(set(pair) == {"input", "output"} for pair in public["train"])
        assert all(set(pair) == {"input"} for pair in public["test"])
        text = json.dumps(public)
        assert all(secret not in text for secret in ("orientation", "program", "seed", "query_outputs", "rivals"))
        assert private["public_sha256"] == p.public_challenge_id(public)


def test_episode_is_deterministic_and_hidden_rule_is_selected_once(bridge, episodes):
    chosen = p.choose_orientation(17)
    assert p.build_episode(17, bridge) == episodes[chosen]
    assert {p.choose_orientation(seed) for seed in range(40)} == set(p.SETTINGS)
    for private in (private for _, private in episodes.values()):
        for rejection in private["rejections"]:
            assert rejection["reason"] in {"orientation ambiguity", "shortcut teaching", "duplicate input"}
            if rejection["reason"] == "orientation ambiguity":
                assert rejection["equal_groups"]


def test_symmetric_markers_and_exhausted_budget_are_honestly_rejected(bridge, monkeypatch):
    grid = p.symmetry_fixture()
    assert p.generator().self_check(grid) == []
    outputs = p.outputs_for(bridge, grid)
    assert p.equal_groups(outputs) == [["identity", "rot180"], ["flip_lr", "flip_ud"]]
    class SymmetricGenerator:
        generate = staticmethod(lambda seed, index: grid)
        self_check = staticmethod(lambda grid: [])
    monkeypatch.setattr(p, "generator", lambda: SymmetricGenerator)
    with pytest.raises(p.EpisodeSamplingError) as error:
        p.build_episode(17, bridge, max_attempts=2)
    assert len(error.value.details["rejections"]) == 2
    assert error.value.details["attempts"] == 2
    with pytest.raises(p.EpisodeSamplingError):
        p.build_episode(17, bridge, max_attempts=0)


def test_alternatives_reflect_scaled_shape_preserve_frame_and_unequal_axes(bridge):
    grid = p.symmetry_fixture()
    # Make a nonsquare, asymmetric 3x2 marker; scale_h=1 and scale_w=3.
    for r in range(7, 10):
        for c in range(1, 4):
            grid[r][c] = 0
    for r, c in ((7, 1), (8, 1), (9, 2)):
        grid[r][c] = 2
    facts, errors = p.generator()._analyze(grid)
    assert not errors
    assert (facts["marker_h"], facts["marker_w"], facts["scale_h"], facts["scale_w"]) == (3, 2, 1, 3)
    outputs = p.outputs_for(bridge, grid)
    assert not p.equal_groups(outputs)
    identity = outputs["identity"]
    assert outputs["flip_lr"] == [row[::-1] for row in identity]
    assert outputs["flip_ud"] == identity[::-1]
    assert outputs["rot180"] == [row[::-1] for row in identity[::-1]]
    for result in outputs.values():
        assert len(result) == 5 and len(result[0]) == 8
        assert result[0] == result[-1] == [1] * 8
        assert all(row[0] == row[-1] == 1 for row in result)


def test_all_settings_on_four_query_rotations_execute_with_correct_axes(bridge, episodes):
    query = episodes["identity"][0]["test"][0]["input"]
    checks = p.rotation_checks(bridge, query)
    assert len(checks) == 16
    assert all(check["passed"] for check in checks)


def test_public_filenames_are_opaque_content_ids_independent_of_setting_order(episodes):
    names = {setting: p.public_filename(17, episodes[setting][0]) for setting in p.SETTINGS}
    reversed_names = {setting: p.public_filename(17, episodes[setting][0]) for setting in reversed(p.SETTINGS)}
    assert names == reversed_names
    assert len(set(names.values())) == 4
    for setting, name in names.items():
        assert re.fullmatch(r"[0-9a-f]{64}\.json", name)
        assert setting not in name
        assert name != f"episode-{p.SETTINGS.index(setting):03d}.json"
        assert p.public_filename(18, episodes[setting][0]) == name
