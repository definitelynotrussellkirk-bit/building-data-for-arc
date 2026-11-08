"""Focused tests for the proposed episode-level mirror-mode prototype."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest
from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "d5a059b0f3a6"
ROOT = find_root(__file__)
PROTOTYPE_PATH = (
    ROOT
    / "generators"
    / TASK_ID
    / "workspace"
    / "parametric"
    / "prototype.py"
)
VERIFY_PATH = PROTOTYPE_PATH.with_name("verify.py")


def _load_prototype():
    spec = importlib.util.spec_from_file_location(
        f"{TASK_ID}_parametric_prototype", PROTOTYPE_PATH
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_verify():
    spec = importlib.util.spec_from_file_location(
        f"{TASK_ID}_parametric_verify_tests", VERIFY_PATH
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row["program_solution"]
    raise RuntimeError("canonical program not found")


def _inputs(episode):
    return [
        pair["input"]
        for split in ("train", "test")
        for pair in episode[split]
    ]


def _outputs(episode):
    return [
        pair["output"]
        for split in ("train", "test")
        for pair in episode[split]
    ]


def test_default_setting_keeps_exact_canonical_program_and_labels():
    prototype = _load_prototype()
    generator, _, _ = load_selected_generator(TASK_ID, root=ROOT)
    assert prototype.DEFAULT_SETTING == "single_axis"
    assert prototype.program_for("single_axis") == _canonical_program()

    episode = prototype.build_episode(
        20261023,
        setting="single_axis",
        n_train=3,
        n_test=4,
    )
    assert len(episode["train"]) == 3
    assert len(episode["test"]) == 4
    for pair in episode["train"] + episode["test"]:
        assert pair["output"] == generator.solve_python(pair["input"])


def test_both_settings_use_same_unique_inputs_and_change_every_label():
    prototype = _load_prototype()
    canonical = prototype.build_episode(
        20261023,
        setting="single_axis",
        n_train=3,
        n_test=4,
    )
    expanded = prototype.build_episode(
        20261023,
        setting="both_axes",
        n_train=3,
        n_test=4,
    )
    assert _inputs(canonical) == _inputs(expanded)
    assert len({prototype.grid_digest(grid) for grid in _inputs(canonical)}) == 7
    assert all(
        left != right
        for left, right in zip(_outputs(canonical), _outputs(expanded))
    )
    assert canonical["parameter"] == {prototype.PARAMETER_NAME: "single_axis"}
    assert expanded["parameter"] == {prototype.PARAMETER_NAME: "both_axes"}
    assert prototype.episode_errors(canonical) == []
    assert prototype.episode_errors(expanded) == []


def test_hidden_setting_is_fixed_and_demos_refute_the_other_setting():
    prototype = _load_prototype()
    for setting in prototype.ALLOWED_SETTINGS:
        episode = prototype.build_episode(
            99173,
            setting=setting,
            n_train=3,
            n_test=4,
        )
        rival = next(value for value in prototype.ALLOWED_SETTINGS if value != setting)
        assert all(pair["setting"] == setting for pair in episode["train"] + episode["test"])
        assert any(
            prototype.solve_setting(pair["input"], rival) != pair["output"]
            for pair in episode["train"]
        )
        assert all(
            prototype.solve_setting(pair["input"], rival) != pair["output"]
            for pair in episode["test"]
        )


def test_public_export_is_answer_free_and_identifier_uses_visible_content_only():
    prototype = _load_prototype()
    episode = prototype.build_episode(
        20261023,
        setting="both_axes",
        n_train=3,
        n_test=4,
    )
    challenge = prototype.public_challenge(episode)
    assert set(challenge) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in challenge["train"])
    assert all(set(pair) == {"input"} for pair in challenge["test"])
    serialized = json.dumps(challenge, sort_keys=True)
    for forbidden in (
        prototype.PARAMETER_NAME,
        "both_axes",
        "single_axis",
        "rule!",
        "sampling",
        "seed",
    ):
        assert forbidden not in serialized

    identifier = prototype.public_identifier(challenge)
    private_changed = deepcopy(episode)
    private_changed["parameter"][prototype.PARAMETER_NAME] = "single_axis"
    private_changed["program"] = "private replacement"
    for pair in private_changed["test"]:
        pair["output"] = [[9]]
    assert prototype.public_identifier(
        prototype.public_challenge(private_changed)
    ) == identifier

    visible_changed = deepcopy(challenge)
    visible_changed["test"][0]["input"][0][0] = (
        9 if visible_changed["test"][0]["input"][0][0] != 9 else 8
    )
    assert prototype.public_identifier(visible_changed) != identifier
    assert identifier.startswith("challenge-") and identifier.endswith(".json")


def test_public_materialization_order_depends_only_on_visible_filenames(
    monkeypatch,
    tmp_path,
):
    prototype = _load_prototype()
    verifier = _load_verify()
    episodes = {
        setting: prototype.build_episode(
            20261023,
            setting=setting,
            n_train=prototype.DEFAULT_N_TRAIN,
            n_test=prototype.DEFAULT_N_TEST,
        )
        for setting in prototype.ALLOWED_SETTINGS
    }
    programs = {
        setting: prototype.program_for(setting)
        for setting in prototype.ALLOWED_SETTINGS
    }

    public_writes = []
    original_write_text = Path.write_text

    def recording_write_text(path, *args, **kwargs):
        relative = path.relative_to(tmp_path)
        if relative.parts[:2] == ("public", "challenges"):
            public_writes.append(relative.name)
        return original_write_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", recording_write_text)
    monkeypatch.setattr(
        prototype,
        "ALLOWED_SETTINGS",
        tuple(reversed(prototype.ALLOWED_SETTINGS)),
    )

    verifier._materialize(
        artifact_dir=tmp_path,
        seed=20261023,
        prototype=prototype,
        programs=programs,
        episodes=episodes,
        generator_sha256=episodes[prototype.DEFAULT_SETTING]["generator_sha256"],
    )

    assert public_writes == sorted(public_writes)


def test_episode_builder_is_deterministic_fresh_and_validates_controls():
    prototype = _load_prototype()
    first = prototype.build_episode(77, setting="single_axis")
    second = prototype.build_episode(77, setting="single_axis")
    assert first == second
    assert first is not second
    assert first["train"][0]["input"] is not second["train"][0]["input"]
    first["train"][0]["input"][0][0] = 9
    assert first != second

    for bad_seed in (True, 1.0, "1", None):
        with pytest.raises((TypeError, ValueError)):
            prototype.build_episode(bad_seed, setting="single_axis")
    for bad_count in (True, 0, -1, 1.5, "4"):
        with pytest.raises((TypeError, ValueError)):
            prototype.build_episode(1, setting="single_axis", n_test=bad_count)
    for bad_setting in (None, True, 1, "diagonal_only"):
        with pytest.raises((TypeError, ValueError)):
            prototype.build_episode(1, setting=bad_setting)
