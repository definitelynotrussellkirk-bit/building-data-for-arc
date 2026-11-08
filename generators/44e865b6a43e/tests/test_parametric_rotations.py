"""Prototype-scope tests; these do not approve or replace the canonical generator."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
from unittest.mock import patch

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, find_root

ROOT = find_root(__file__)
PROTOTYPE_PATH = ROOT / "generators/44e865b6a43e/workspace/parametric/prototype.py"
SPEC = importlib.util.spec_from_file_location("parametric_rotations_44e865b6a43e", PROTOTYPE_PATH)
prototype = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(prototype)


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge(timeout=20.0, max_calls_before_restart=128) as running:
        yield running


@pytest.fixture(scope="module")
def episodes(bridge):
    return [prototype.build_episode(seed, bridge)
            for _, seed in sorted(prototype.representative_seeds().items())]


def observed_bars(grid):
    """Independent test readout using bottom colors and column counts."""
    colors = grid[-1][1::2]
    heights = [sum(row[column] != 7 for row in grid)
               for column in range(1, len(grid[0]), 2)]
    return colors, heights


def test_signed_rotations_are_independent_live_racket(bridge):
    grid = prototype.draw_bars([2, 8, 5, 1], [1, 3, 3, 6], 7)
    before = deepcopy(grid)
    expected_colors = {-1: [8, 5, 1, 2], 0: [2, 8, 5, 1], 1: [1, 2, 8, 5]}
    expected_heights = {-1: [3, 3, 6, 1], 0: [1, 3, 3, 6], 1: [6, 1, 3, 3]}
    outputs = set()
    for parameters in prototype.settings():
        output = prototype.apply_racket(bridge, prototype.racket_program(parameters), grid)
        colors, heights = observed_bars(output)
        assert colors == expected_colors[parameters["color_shift"]]
        assert heights == expected_heights[parameters["height_shift"]]
        assert all(row[col] == 7 for row in output for col in range(0, len(row), 2))
        outputs.add(tuple(map(tuple, output)))
        if parameters == {"color_shift": 0, "height_shift": 0}:
            assert output == grid
    assert len(outputs) == 9
    assert grid == before


def test_episode_draws_rule_once_and_replays_deterministically(bridge):
    state = random.getstate()
    with patch.object(prototype, "choose_parameters", wraps=prototype.choose_parameters) as choose:
        first = prototype.build_episode(7, bridge)
        choose.assert_called_once_with(7)
    second = prototype.build_episode(7, bridge)
    assert first == second
    assert random.getstate() == state
    assert first["parameters"] == prototype.choose_parameters(7)
    assert first["racket_program"] == prototype.racket_program(first["parameters"])
    assert first["racket_sha256"] == prototype.sha256(first["racket_program"])


def test_all_nine_episode_settings_are_identified_by_demonstrations(episodes):
    assert {prototype.setting_key(item["parameters"]) for item in episodes} == {
        prototype.setting_key(parameters) for parameters in prototype.settings()}
    for episode in episodes:
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 1
        selected_key = prototype.setting_key(episode["parameters"])
        pairs = episode["train"] + episode["test"]
        for pair_index, pair in enumerate(pairs):
            predictions = episode["racket_predictions"][pair_index]
            assert len(predictions) == 9
            assert pair["output"] == predictions[selected_key]
            # This uses the same episode-level parameters on demonstrations AND query.
            colors, heights = observed_bars(pair["input"])
            color_shift = episode["parameters"]["color_shift"]
            height_shift = episode["parameters"]["height_shift"]
            output_colors, output_heights = observed_bars(pair["output"])
            assert output_colors == colors[-color_shift:] + colors[:-color_shift] if color_shift else output_colors == colors
            assert output_heights == heights[-height_shift:] + heights[:-height_shift] if height_shift else output_heights == heights
        assert len(episode["parameter_competitors"]) == 8
        for competitor in episode["parameter_competitors"]:
            rival_key = prototype.setting_key(competitor["parameters"])
            actual_refutations = [index for index, pair in enumerate(episode["train"])
                                  if episode["racket_predictions"][index][rival_key] != pair["output"]]
            assert actual_refutations
            assert competitor["refuted_on_demonstrations"] == actual_refutations
            assert competitor["status"] == "refuted"


def test_public_challenges_have_only_demonstrations_and_unanswered_queries(episodes):
    for episode in episodes:
        public = prototype.public_challenge(episode)
        assert set(public) == {"train", "test"}
        assert all(set(pair) == {"input", "output"} for pair in public["train"])
        assert all(set(pair) == {"input"} for pair in public["test"])
        assert public["train"] == episode["train"]
        assert public["test"][0]["input"] == episode["test"][0]["input"]
        before = deepcopy(episode)
        public["train"][0]["input"][0][0] = 6
        public["train"][0]["output"][0][0] = 6
        public["test"][0]["input"][0][0] = 6
        assert episode == before


def test_sampler_preserves_variable_and_repeated_height_grammar():
    counts, heights_seen, repeated, saw_black = set(), set(), False, False
    for seed in range(40):
        for pair_index in range(4):
            grid = prototype.build_input(seed, pair_index)
            assert grid == prototype.build_input(seed, pair_index)
            facts = prototype.profile(grid)
            colors, heights = observed_bars(grid)
            counts.add(len(colors))
            heights_seen.update(heights)
            saw_black |= 0 in colors
            assert 3 <= len(colors) <= 5
            assert len(set(colors)) == len(colors)
            assert 7 not in colors
            assert len({tuple(heights), tuple(heights[1:] + heights[:1]),
                        tuple(heights[-1:] + heights[:-1])}) == 3
            if pair_index == 1:
                assert len(set(heights)) < len(heights)
                repeated = True
            assert facts["heights"] == heights
    assert counts == {3, 4, 5}
    assert repeated and saw_black
    assert {1, 6, 11} <= heights_seen


def test_canonical_setting_matches_all_four_canonical_examples_live_racket(bridge):
    pairs = canonical_pairs(prototype.TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == 4
    for pair in pairs:
        result = prototype.apply_racket(
            bridge, prototype.racket_program(prototype.CANONICAL_PARAMETERS), pair["input"])
        assert result == pair["output"]


@pytest.mark.parametrize("parameters", [
    {}, {"color_shift": 1}, {"color_shift": 1, "height_shift": -1, "extra": 0},
    {"color_shift": True, "height_shift": -1}, {"color_shift": 2, "height_shift": 0},
    {"color_shift": 0, "height_shift": -2}, {"color_shift": 1.0, "height_shift": -1},
])
def test_parameter_contract_rejects_unsupported_settings(parameters):
    with pytest.raises(ValueError):
        prototype.racket_program(parameters)


@pytest.mark.parametrize("seed", [True, 1.5, "1", None])
def test_episode_seed_requires_literal_integer(seed):
    with pytest.raises(TypeError):
        prototype.choose_parameters(seed)


def test_two_bar_shortcuts_and_ambiguous_equal_heights_are_outside_prototype():
    with pytest.raises(ValueError):
        prototype.draw_bars([1, 2], [2, 3], 7)
    with pytest.raises(ValueError):
        prototype.draw_bars([1, 2, 3], [3, 3, 3], 7)


def test_evidence_serialization_keeps_runtime_identity_and_labels_private(tmp_path):
    out = tmp_path / "episode-evidence"
    result = prototype.run_evidence(out, [7])
    summary = json.loads((out / "private/summary.json").read_text())
    assert result == summary
    assert summary["runtime_identity"]["backend"] == "racket"
    assert summary["runtime_identity"]["protected"] is True
    assert summary["episode_count"] == 1
    assert summary["racket_evaluations"] == 53
    assert summary["canonical_pairs_checked"] == 4
    episode_record = summary["episodes"][0]
    public = json.loads((out / episode_record["public_path"]).read_text())
    private = json.loads((out / episode_record["private_path"]).read_text())
    assert public == prototype.public_challenge(private)
    assert "output" not in public["test"][0]
    assert "output" in private["test"][0]
    assert set(public) == {"train", "test"}
    for key, expected_hash in summary["rule_sha256"].items():
        program_bytes = (out / "private/rules" / (key + ".rkt")).read_bytes()
        assert prototype.sha256(program_bytes) == expected_hash
    for relative, expected_hash in summary["source_sha256"].items():
        assert prototype.sha256((ROOT / relative).read_bytes()) == expected_hash
    with pytest.raises(FileExistsError):
        prototype.run_evidence(out, [7])


def test_public_filename_depends_only_on_inputs_not_hidden_rule_or_position(tmp_path, bridge):
    original = prototype.build_episode(4, bridge)
    distractor = prototype.build_episode(7, bridge)
    changed = deepcopy(original)
    changed["seed"] = 9
    changed["parameters"] = prototype.choose_parameters(9)
    changed["racket_program"] = prototype.racket_program(changed["parameters"])
    changed["racket_sha256"] = prototype.sha256(changed["racket_program"])
    changed_key = prototype.setting_key(changed["parameters"])
    # Reuse the exact live-Racket predictions already executed on these inputs.
    for index, pair in enumerate(changed["train"] + changed["test"]):
        pair["output"] = deepcopy(changed["racket_predictions"][index][changed_key])
    changed["parameter_competitors"] = [
        {"parameters": item, "refuted_on_demonstrations": [0, 1, 2],
         "query_differs": True, "status": "refuted"}
        for item in prototype.settings() if item != changed["parameters"]
    ]
    assert original["parameters"] != changed["parameters"]
    for before, after in zip(original["train"] + original["test"],
                             changed["train"] + changed["test"]):
        assert before["input"] == after["input"]
        assert before["output"] != after["output"]

    with patch.object(prototype, "build_episode", side_effect=[original, distractor]):
        first = prototype.run_evidence(tmp_path / "first", [4, 7])
    with patch.object(prototype, "build_episode", side_effect=[distractor, changed]):
        second = prototype.run_evidence(tmp_path / "second", [7, 9])
    first_path = first["episodes"][0]["public_path"]
    second_path = second["episodes"][1]["public_path"]
    assert first_path == second_path, "public filenames expose emission rank / hidden setting"
    inputs_only = {split: [pair["input"] for pair in original[split]]
                   for split in ("train", "test")}
    canonical_bytes = (json.dumps(inputs_only, sort_keys=True, separators=(",", ":")) + "\n").encode()
    expected_digest = hashlib.sha256(canonical_bytes).hexdigest()
    assert first_path == f"public/challenge-{expected_digest}.json"
    assert len({item["public_path"] for item in first["episodes"]}) == 2
    assert len({item["public_path"] for item in second["episodes"]}) == 2
    first_public = json.loads((tmp_path / "first" / first_path).read_text())
    second_public = json.loads((tmp_path / "second" / second_path).read_text())
    assert first_public["train"] != second_public["train"]
    assert first_public["test"] == second_public["test"]
    # Two differently labeled rules on identical inputs must not overwrite one another.
    with patch.object(prototype, "build_episode", side_effect=[original, changed]):
        with pytest.raises(ValueError, match="duplicate input-derived public filename"):
            prototype.run_evidence(tmp_path / "duplicate-inputs", [4, 9])

