"""Contract and adversarial tests for the selector-color/selector-area family."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes


TASK_ID = "346480121fcb"
COLOR = {"selection_mode": "color"}
AREA = {"selection_mode": "area"}
SETTINGS = (COLOR, AREA)


def _root() -> Path:
    return find_root(__file__)


def _load(name: str):
    path = _root() / "generators" / TASK_ID / "workspace" / "parametric" / name
    assert path.is_file(), f"missing parametric implementation: {path}"
    spec = importlib.util.spec_from_file_location(f"_test_{TASK_ID}_{path.stem}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    rows = []
    with canonical_path(_root()).open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                rows.append(row)
    assert len(rows) == 1
    return rows[0]["program_solution"]


def _inputs(episode: dict) -> list[list[list[int]]]:
    return [pair["input"] for pair in [*episode["train"], *episode["test"]]]


def test_default_program_is_exact_canonical_and_area_program_is_distinct():
    prototype = _load("prototype.py")
    assert prototype.program(COLOR) == _canonical_program()
    assert prototype.program(AREA) != _canonical_program()
    assert "obj-size" in prototype.program(AREA)
    with pytest.raises(ValueError, match="exactly"):
        prototype.program({})
    with pytest.raises(ValueError, match="selection_mode"):
        prototype.program({"selection_mode": "rank"})


def test_hand_scene_selects_different_intermediate_before_same_transform():
    prototype = _load("prototype.py")
    grid = [
        [4, 0, 0, 0, 0, 0, 0, 0, 0, 2],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 4, 4, 0, 0, 0, 6, 6, 0, 0],
        [0, 4, 0, 0, 0, 0, 6, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 6, 0, 0, 0],
        [0, 0, 0, 7, 7, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 7, 0, 0, 0, 0, 0],
    ]
    analysis = prototype.analyze_input(grid)
    assert analysis["selector"] == 4
    assert analysis["key"] == 2
    assert analysis["color_candidate"]["color"] == 4
    assert analysis["color_candidate"]["size"] == 3
    assert analysis["area_candidate"]["color"] == 6
    assert analysis["area_candidate"]["size"] == 4
    assert prototype.apply_python(grid, COLOR) != prototype.apply_python(grid, AREA)


def test_two_demos_identify_both_settings_with_matched_inputs_and_key_evidence():
    prototype = _load("prototype.py")
    episodes = [prototype.generate_episode(44, settings, demos=2, queries=4) for settings in SETTINGS]
    assert _inputs(episodes[0]) == _inputs(episodes[1])
    demo_keys = [prototype.analyze_input(pair["input"])["key"] for pair in episodes[0]["train"]]
    assert len(set(demo_keys)) == 2
    assert all(key in {2, 3, 4, 5} for key in demo_keys)
    query_keys = {prototype.analyze_input(pair["input"])["key"] for pair in episodes[0]["test"]}
    assert query_keys <= set(demo_keys)
    for settings, episode in zip(SETTINGS, episodes):
        assert prototype.teaching_survivors(episode) == [settings]
        for pair in episode["train"]:
            profile = prototype.analyze_input(pair["input"])
            assert profile["color_candidate"]["index"] != profile["area_candidate"]["index"]
            assert prototype.apply_without_transform(pair["input"], settings) != pair["output"]


def test_minimum_demos_distinguish_every_transform_code_on_each_candidate():
    prototype = _load("prototype.py")
    for seed in range(32):
        episode = prototype.generate_episode(seed, COLOR, demos=2, queries=4)
        for pair in episode["train"]:
            profile = prototype.analyze_input(pair["input"])
            for candidate_name in ("color_candidate", "area_candidate"):
                crop = prototype._crop(pair["input"], profile[candidate_name]["bbox"])
                transformed = {
                    json.dumps(prototype._crop_to_content(prototype._transform(crop, key)), separators=(",", ":"))
                    for key in range(1, 6)
                }
                assert len(transformed) == 5


def test_query_prefixes_are_independent_of_counts_and_include_substantive_30x30():
    prototype = _load("prototype.py")
    one = prototype.generate_episode(91, AREA, demos=2, queries=1)
    four = prototype.generate_episode(91, AREA, demos=2, queries=4)
    six = prototype.generate_episode(91, AREA, demos=6, queries=4)
    assert one["train"] == four["train"]
    assert one["test"] == four["test"][:1]
    assert four["test"] == six["test"]
    assert [(len(pair["input"]), len(pair["input"][0])) for pair in four["test"]] == [
        (18, 24),
        (22, 28),
        (30, 30),
        (17, 30),
    ]
    large = four["test"][2]["input"]
    profile = prototype.analyze_input(large)
    assert len(profile["objects"]) >= 8
    occupied = [(r, c) for r, row in enumerate(large[1:], start=1) for c, value in enumerate(row) if value]
    assert len(occupied) >= 35
    assert min(r for r, _ in occupied) == 1
    assert max(r for r, _ in occupied) == 29
    assert min(c for _, c in occupied) == 0
    assert max(c for _, c in occupied) == 29
    keys = {json.dumps(grid, separators=(",", ":")) for grid in _inputs(four)}
    assert len(keys) == len(_inputs(four))


def test_count_boundaries_determinism_and_setting_neutral_inputs():
    prototype = _load("prototype.py")
    for demos in (2, 6):
        for queries in (1, 4):
            first = prototype.generate_episode(1234, COLOR, demos=demos, queries=queries)
            second = prototype.generate_episode(1234, COLOR, demos=demos, queries=queries)
            alternate = prototype.generate_episode(1234, AREA, demos=demos, queries=queries)
            assert first == second
            assert _inputs(first) == _inputs(alternate)
            assert len(first["train"]) == demos
            assert len(first["test"]) == queries
    for kwargs in (
        {"demos": 1, "queries": 4},
        {"demos": 7, "queries": 4},
        {"demos": 3, "queries": 0},
        {"demos": 3, "queries": 5},
    ):
        with pytest.raises(ValueError):
            prototype.generate_episode(0, COLOR, **kwargs)
    with pytest.raises(ValueError):
        prototype.generate_episode(True, COLOR, demos=3, queries=4)


def test_public_first_turn_is_prefix_stable_and_private_fields_are_absent():
    prototype = _load("prototype.py")
    one = prototype.generate_episode(777, AREA, demos=3, queries=1)
    four = prototype.generate_episode(777, AREA, demos=3, queries=4)
    visible_one = prototype.public_turn(one, 0)
    visible_four = prototype.public_turn(four, 0)
    assert public_challenge_bytes(visible_one) == public_challenge_bytes(visible_four)
    assert set(visible_four) == {"train", "test"}
    assert len(visible_four["test"]) == 1
    assert set(visible_four["test"][0]) == {"input"}
    raw = public_challenge_bytes(visible_four)
    assert prototype.public_turn_id(four, 0) == hashlib.sha256(raw).hexdigest()
    for forbidden in (b"selection_mode", b"program", b"query_count", b"answer", b"source_index"):
        assert forbidden not in raw
    with pytest.raises(IndexError):
        prototype.public_turn(one, 1)


def test_episode_validator_rejects_forgery_duplicates_and_bool_cells():
    prototype = _load("prototype.py")
    episode = prototype.generate_episode(912, COLOR, demos=2, queries=4)

    duplicate = copy.deepcopy(episode)
    duplicate["test"][0]["input"] = copy.deepcopy(duplicate["train"][0]["input"])
    assert any("duplicates" in error for error in prototype.episode_errors(duplicate))

    malformed = copy.deepcopy(episode)
    malformed["train"][0]["input"][1][1] = True
    assert any("exact integer" in error for error in prototype.episode_errors(malformed))

    boolean_output = copy.deepcopy(episode)
    replaced = False
    for row in boolean_output["train"][0]["output"]:
        for index, value in enumerate(row):
            if value == 0:
                row[index] = False
                replaced = True
                break
        if replaced:
            break
    assert replaced
    assert any(
        "output" in error and "exact integer" in error
        for error in prototype.episode_errors(boolean_output)
    )

    forged = copy.deepcopy(episode)
    forged["train"][0]["output"] = [[9]]
    assert any("output" in error for error in prototype.episode_errors(forged))

    wrong_program = copy.deepcopy(episode)
    wrong_program["program"] = prototype.program(AREA)
    assert any("program" in error for error in prototype.episode_errors(wrong_program))


def test_promotion_contract_and_adapter_are_native_and_bounded():
    contract_path = _root() / "generators" / TASK_ID / "workspace" / "parametric" / "promotion.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"selection_mode": ["color", "area"]},
        "default": COLOR,
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "qualification_demos": 2,
        "resources": [
            f"generators/{TASK_ID}/workspace/parametric/prototype.py",
            f"generators/{TASK_ID}/workspace/parametric/canonical.rkt",
            f"generators/{TASK_ID}/workspace/parametric/select_by_area.rkt",
        ],
    }
    adapter = _load("adapter.py")
    generated = adapter.generate(5, AREA, 2, 4)
    assert set(generated) == {"train", "test", "program_solution"}
    assert generated["program_solution"] == adapter.program(AREA)


def test_bounded_adversarial_probe_rejects_shortcuts_and_certificate_attacks():
    probe = _load("adversarial_probe.py")
    report = probe.run(seed_start=0, seed_count=32)
    assert report["status"] == "passed"
    assert report["episodes_checked"] == 64
    assert report["minimum_demo_count"] == 2
    assert all(value == 0 for value in report["rival_full_lesson_survivals"].values())
    assert all(report["certificate_attacks"].values())
    assert report["certificate_attacks"]["boolean_output_rejected"] is True
    assert report["crossed_controls"]["candidate_scan_order_both_directions"] is True
    assert report["crossed_controls"]["candidate_size_relation_both_directions"] is True
    assert report["crossed_controls"]["candidate_color_rank_both_directions"] is True
