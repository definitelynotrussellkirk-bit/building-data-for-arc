"""Focused tests for the proposed episode-level identity-corner prototype."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest
from reviewer_support import canonical_path, find_root


TASK_ID = "90640e0e6314"
ROOT = find_root(__file__)
PARAMETRIC_DIR = ROOT / "generators" / TASK_ID / "workspace" / "parametric"
PROTOTYPE_PATH = PARAMETRIC_DIR / "prototype.py"
VERIFIER_PATH = PARAMETRIC_DIR / "verify.py"


def _load_prototype():
    spec = importlib.util.spec_from_file_location(
        f"{TASK_ID}_identity_corner_prototype", PROTOTYPE_PATH
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_verifier():
    spec = importlib.util.spec_from_file_location(
        f"{TASK_ID}_identity_corner_verifier", VERIFIER_PATH
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
    raise AssertionError("canonical program missing")


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


def test_corner_mapping_matches_hand_derived_literal_outputs():
    """Catches swapped row/column reversal branches for any identity corner."""
    prototype = _load_prototype()
    grid = [
        [0, 1, 2],
        [3, 0, 1],
        [2, 3, 0],
    ]
    expected = {
        "top_left": [
            [0, 1, 2, 2, 1, 0],
            [3, 0, 1, 1, 0, 3],
            [2, 3, 0, 0, 3, 2],
            [2, 3, 0, 0, 3, 2],
            [3, 0, 1, 1, 0, 3],
            [0, 1, 2, 2, 1, 0],
        ],
        "top_right": [
            [2, 1, 0, 0, 1, 2],
            [1, 0, 3, 3, 0, 1],
            [0, 3, 2, 2, 3, 0],
            [0, 3, 2, 2, 3, 0],
            [1, 0, 3, 3, 0, 1],
            [2, 1, 0, 0, 1, 2],
        ],
        "bottom_left": [
            [2, 3, 0, 0, 3, 2],
            [3, 0, 1, 1, 0, 3],
            [0, 1, 2, 2, 1, 0],
            [0, 1, 2, 2, 1, 0],
            [3, 0, 1, 1, 0, 3],
            [2, 3, 0, 0, 3, 2],
        ],
        "bottom_right": [
            [0, 3, 2, 2, 3, 0],
            [1, 0, 3, 3, 0, 1],
            [2, 1, 0, 0, 1, 2],
            [2, 1, 0, 0, 1, 2],
            [1, 0, 3, 3, 0, 1],
            [0, 3, 2, 2, 3, 0],
        ],
    }

    assert prototype.PARAMETER_NAME == "identity_corner"
    assert prototype.ALLOWED_SETTINGS == tuple(expected)
    assert prototype.DEFAULT_SETTING == "bottom_right"
    for setting, literal in expected.items():
        assert prototype.solve_setting(grid, setting) == literal


def test_default_setting_keeps_exact_canonical_program():
    """Catches accidental replacement or normalization of canonical authority."""
    prototype = _load_prototype()
    assert prototype.program_for("bottom_right") == _canonical_program()
    assert len({prototype.program_for(s) for s in prototype.ALLOWED_SETTINGS}) == 4


def test_all_settings_share_inputs_and_change_every_label():
    """Catches setting-dependent sampling and collapsed corner semantics."""
    prototype = _load_prototype()
    episodes = {
        setting: prototype.build_episode(
            20261023,
            setting=setting,
            n_train=3,
            n_test=4,
        )
        for setting in prototype.ALLOWED_SETTINGS
    }
    reference_inputs = _inputs(episodes[prototype.DEFAULT_SETTING])
    assert len(reference_inputs) == 7
    assert len({prototype.grid_digest(grid) for grid in reference_inputs}) == 7

    for setting, episode in episodes.items():
        assert _inputs(episode) == reference_inputs, setting
        assert episode["parameter"] == {prototype.PARAMETER_NAME: setting}
        assert prototype.episode_errors(episode) == []

    for pair_index in range(7):
        labels = [
            _outputs(episodes[setting])[pair_index]
            for setting in prototype.ALLOWED_SETTINGS
        ]
        assert len({prototype.grid_digest(label) for label in labels}) == 4


def test_fixed_setting_demos_refute_every_rival_and_four_queries_are_sensitive():
    """Catches parameter drift or an episode whose demos do not identify its rule."""
    prototype = _load_prototype()
    episodes = {
        setting: prototype.build_episode(99173, setting=setting)
        for setting in prototype.ALLOWED_SETTINGS
    }
    for setting, episode in episodes.items():
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 4
        assert all(
            pair["setting"] == setting
            for pair in episode["train"] + episode["test"]
        )
        for rival in prototype.ALLOWED_SETTINGS:
            if rival == setting:
                continue
            assert any(
                left["output"] != right["output"]
                for left, right in zip(
                    episode["train"], episodes[rival]["train"]
                )
            )
            assert all(
                left["output"] != right["output"]
                for left, right in zip(
                    episode["test"], episodes[rival]["test"]
                )
            )


def test_seed_selected_setting_is_deterministic_and_fixed_for_the_episode():
    """Catches default-setting resampling or a seed chooser ignored by the builder."""
    prototype = _load_prototype()
    observed = set()
    for seed in (0, 1, 2, 20261023):
        expected = prototype.choose_setting(seed)
        first = prototype.build_episode(seed)
        second = prototype.build_episode(seed)
        observed.add(expected)
        assert first == second
        assert first["parameter"] == {prototype.PARAMETER_NAME: expected}
        assert all(
            pair["setting"] == expected
            for pair in first["train"] + first["test"]
        )
    assert observed <= set(prototype.ALLOWED_SETTINGS)
    assert len({prototype.choose_setting(seed) for seed in range(128)}) == 4


def test_public_projection_and_identifier_depend_only_on_visible_content():
    """Catches private setting, program, seed, or query-answer leakage into public IDs."""
    prototype = _load_prototype()
    episode = prototype.build_episode(20261023, setting="top_left")
    challenge = prototype.public_challenge(episode)

    assert set(challenge) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in challenge["train"])
    assert all(set(pair) == {"input"} for pair in challenge["test"])
    serialized = json.dumps(challenge, sort_keys=True)
    for forbidden in (
        prototype.PARAMETER_NAME,
        "top_left",
        "bottom_right",
        "program",
        "sampling",
        "seed",
        "rule!",
    ):
        assert forbidden not in serialized

    identifier = prototype.public_identifier(challenge)
    private_changed = deepcopy(episode)
    private_changed["parameter"][prototype.PARAMETER_NAME] = "bottom_right"
    private_changed["program"] = "private replacement"
    private_changed["seed"] = 7
    for pair in private_changed["test"]:
        pair["output"] = [[9]]
    assert prototype.public_identifier(
        prototype.public_challenge(private_changed)
    ) == identifier

    visible_changed = deepcopy(challenge)
    old = visible_changed["test"][0]["input"][0][0]
    visible_changed["test"][0]["input"][0][0] = 9 if old != 9 else 8
    assert prototype.public_identifier(visible_changed) != identifier
    assert identifier.startswith("challenge-") and identifier.endswith(".json")
    assert len(identifier) == len("challenge-") + 64 + len(".json")


def test_episode_builder_is_deterministic_fresh_and_split_count_stable():
    """Catches shared mutable returns or demo/query stream coupling."""
    prototype = _load_prototype()
    first = prototype.build_episode(77, setting="bottom_right")
    second = prototype.build_episode(77, setting="bottom_right")
    assert first == second
    assert first is not second
    assert first["train"][0]["input"] is not second["train"][0]["input"]
    first["train"][0]["input"][0][0] = (first["train"][0]["input"][0][0] + 1) % 10
    assert first != second

    fewer_demos = prototype.build_episode(
        77, setting="bottom_right", n_train=1, n_test=4
    )
    more_queries = prototype.build_episode(
        77, setting="bottom_right", n_train=3, n_test=6
    )
    assert _inputs(second)[3:] == _inputs(fewer_demos)[1:]
    assert _inputs(second)[:3] == _inputs(more_queries)[:3]
    assert len(more_queries["test"]) == 6


def test_invalid_controls_are_rejected_without_bool_coercion():
    """Catches permissive coercions that create unstable episode identities."""
    prototype = _load_prototype()
    for bad_seed in (True, -1, 1.5, "1", None):
        with pytest.raises((TypeError, ValueError)):
            prototype.build_episode(bad_seed, setting="bottom_right")
    for bad_count in (True, 0, -1, 65, 1.5, "4", None):
        with pytest.raises((TypeError, ValueError)):
            prototype.build_episode(
                1,
                setting="bottom_right",
                n_test=bad_count,
            )
    for bad_setting in (None, True, 1, "center", "BottomRight"):
        with pytest.raises((TypeError, ValueError)):
            prototype.build_episode(1, setting=bad_setting)
        with pytest.raises((TypeError, ValueError)):
            prototype.program_for(bad_setting)


def test_racket_verifier_writes_source_bound_public_and_private_artifacts(tmp_path):
    """Catches unexecuted labels, leaky public files, and overwrite-prone evidence."""
    prototype = _load_prototype()
    verifier = _load_verifier()
    out_path = tmp_path / "verification.json"
    artifact_dir = tmp_path / "artifacts"

    report = verifier.verify(
        seed=20261023,
        out_path=out_path,
        artifact_dir=artifact_dir,
    )
    assert report["status"] == "passed"
    assert report["counts"] == {
        "episodes": 4,
        "demonstrations_per_episode": 3,
        "queries_per_episode": 4,
        "distinct_shared_inputs": 7,
        "racket_setting_calls": 28,
        "canonical_pairs_checked": 3,
    }
    assert report["canonical_binding"]["default_program_exact_canonical"] is True
    assert report["teaching"]["every_demo_refutes_all_rivals"] is True
    assert report["teaching"]["every_query_distinguishes_all_settings"] is True
    assert all(row["all_settings_distinct"] for row in report["checks"])
    assert json.loads(out_path.read_text(encoding="utf-8")) == report
    assert str(out_path) in report["command"]
    assert str(artifact_dir) in report["command"]

    episode_dirs = sorted((artifact_dir / "episodes").iterdir())
    assert len(episode_dirs) == 4
    assert all(path.name.startswith("episode-") for path in episode_dirs)
    public_ids = set()
    for episode_dir in episode_dirs:
        public_path = episode_dir / "public" / "challenge.json"
        private_path = episode_dir / "private" / "episode.json"
        assert public_path.is_file() and private_path.is_file()
        challenge = json.loads(public_path.read_text(encoding="utf-8"))
        private = json.loads(private_path.read_text(encoding="utf-8"))
        assert all(set(pair) == {"input"} for pair in challenge["test"])
        assert all("output" in pair for pair in private["test"])
        identifier = prototype.public_identifier(challenge)
        assert episode_dir.name == "episode-" + identifier.removeprefix("challenge-").removesuffix(".json")
        assert public_path.read_bytes() == prototype.public_bytes(challenge)
        public_ids.add(identifier)
    assert len(public_ids) == 4
    assert {path.stem for path in (artifact_dir / "programs").glob("*.rkt")} == set(
        prototype.ALLOWED_SETTINGS
    )

    with pytest.raises(FileExistsError):
        verifier.verify(
            seed=20261023,
            out_path=out_path,
            artifact_dir=artifact_dir,
        )
