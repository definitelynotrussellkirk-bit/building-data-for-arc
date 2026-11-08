from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root

TASK_ID = "7515881f2786"
HERE = Path(__file__).resolve().parent
PROTOTYPE_PATH = HERE.parent / "workspace" / "parametric" / "prototype.py"


def _load_prototype():
    spec = importlib.util.spec_from_file_location(
        "parametric_bridge_axes_7515881f2786", PROTOTYPE_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load prototype from {PROTOTYPE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    root = find_root(__file__)
    for line in canonical_path(root).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row["program_solution"]
    raise AssertionError("canonical program missing")


def _axis_witness_grid() -> list[list[int]]:
    return [
        [8, 0, 0, 8, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [8, 0, 0, 0, 0],
    ]


def test_parameter_contract_and_default_program_are_exactly_canonical():
    prototype = _load_prototype()
    assert prototype.PARAMETER_NAME == "bridge_axes"
    assert prototype.ALLOWED_SETTINGS == ("both", "horizontal", "vertical")
    assert prototype.DEFAULT_SETTING == "both"

    canonical = _canonical_program()
    assert prototype.program_for("both") == canonical
    assert prototype.CANONICAL_RULE_HASH == "7327f2eb0272"
    assert (
        hashlib.sha256(" ".join(canonical.split()).encode()).hexdigest()[:12]
        == prototype.CANONICAL_RULE_HASH
    )
    assert len({prototype.program_for(value) for value in prototype.ALLOWED_SETTINGS}) == 3


def test_python_mirror_executes_each_axis_setting_without_mutating_input():
    prototype = _load_prototype()
    grid = _axis_witness_grid()
    before = copy.deepcopy(grid)

    horizontal = prototype.apply_python(grid, "horizontal")
    vertical = prototype.apply_python(grid, "vertical")
    both = prototype.apply_python(grid, "both")

    assert grid == before
    assert horizontal == [
        [8, 8, 8, 8, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [8, 0, 0, 0, 0],
    ]
    assert vertical == [
        [8, 0, 0, 8, 0],
        [8, 0, 0, 0, 0],
        [8, 0, 0, 0, 0],
        [8, 0, 0, 0, 0],
        [8, 0, 0, 0, 0],
    ]
    assert both == [
        [8, 8, 8, 8, 0],
        [8, 0, 0, 0, 0],
        [8, 0, 0, 0, 0],
        [8, 0, 0, 0, 0],
        [8, 0, 0, 0, 0],
    ]


def test_setting_selection_is_deterministic_strict_and_episode_constant():
    prototype = _load_prototype()
    selected = prototype.choose_setting(20261021)
    assert selected in prototype.ALLOWED_SETTINGS
    assert prototype.choose_setting(20261021) == selected
    assert len({prototype.choose_setting(seed) for seed in range(30)}) == 3

    for invalid in (True, False, 1.0, "1", None):
        with pytest.raises(TypeError):
            prototype.choose_setting(invalid)
    for invalid in (None, True, 1, "diagonal"):
        with pytest.raises((TypeError, ValueError)):
            prototype.program_for(invalid)


def test_complete_episodes_distinguish_every_setting_on_every_demonstration():
    prototype = _load_prototype()
    for setting in prototype.ALLOWED_SETTINGS:
        episode = prototype.build_episode(
            20261021,
            setting=setting,
            n_train=4,
            n_test=1,
        )
        assert episode["parameter"] == {prototype.PARAMETER_NAME: setting}
        assert episode["program"] == prototype.program_for(setting)
        assert len(episode["train"]) == 4
        assert len(episode["test"]) == 1
        assert prototype.episode_errors(episode) == []

        rivals = [value for value in prototype.ALLOWED_SETTINGS if value != setting]
        for pair in episode["train"]:
            selected = prototype.apply_python(pair["input"], setting)
            assert pair["output"] == selected
            assert all(
                prototype.apply_python(pair["input"], rival) != selected
                for rival in rivals
            )


def test_public_challenge_removes_hidden_rule_sampling_and_query_answers():
    prototype = _load_prototype()
    episode = prototype.build_episode(20261021, setting="vertical")
    public = prototype.public_challenge(episode)
    serialized = json.dumps(public, sort_keys=True)

    assert prototype.PARAMETER_NAME not in serialized
    assert "rule!" not in serialized
    assert "sampling" not in serialized
    assert len(public["train"]) == 4
    assert len(public["test"]) == 1
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])


def test_verifier_executes_every_program_and_materializes_redacted_artifacts(tmp_path):
    verify_path = HERE.parent / "workspace" / "parametric" / "verify.py"
    spec = importlib.util.spec_from_file_location(
        "parametric_bridge_axes_verify_7515881f2786", verify_path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load verifier from {verify_path}")
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)

    out_path = tmp_path / "verification.json"
    artifact_dir = tmp_path / "materialized"
    report = verifier.verify(
        seed=20261021,
        out_path=out_path,
        artifact_dir=artifact_dir,
    )

    assert report["status"] == "passed"
    assert report["scope"] == "proposed task-local prototype; canonical production unchanged"
    assert report["counts"] == {
        "settings": 3,
        "episodes": 3,
        "train_pairs_per_episode": 4,
        "test_pairs_per_episode": 1,
        "racket_program_pair_checks": 45,
        "selected_racket_pair_checks": 15,
        "rival_racket_pair_checks": 30,
        "train_rival_disagreements": 24,
        "test_rival_disagreements": 6,
    }
    assert report["canonical"]["exact_text_match"] is True
    assert report["canonical"]["normalized_rule_hash"] == "7327f2eb0272"
    assert report["all_racket_python_exact"] is True
    assert report["all_demos_refute_every_rival"] is True
    assert report["all_queries_setting_sensitive"] is True
    assert report["replay"]["cwd"] == "packet_root"
    assert report["replay"]["command"].startswith("python3 review.py run")
    assert out_path.exists()

    manifest = json.loads((artifact_dir / "manifest.json").read_text())
    assert manifest["status"] == "passed"
    assert len(manifest["files"]) == 9
    for relative, metadata in manifest["files"].items():
        path = artifact_dir / relative
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == metadata["sha256"]
        assert path.stat().st_size == metadata["bytes"]

    public_paths = sorted((artifact_dir / "public" / "challenges").glob("*.json"))
    assert len(public_paths) == 3
    for path in public_paths:
        public = json.loads(path.read_text())
        serialized = json.dumps(public, sort_keys=True)
        assert "bridge_axes" not in serialized
        assert "horizontal" not in serialized
        assert "vertical" not in serialized
        assert "both" not in serialized
        assert "rule!" not in serialized
        assert "sampling" not in serialized
        assert all("output" not in pair for pair in public["test"])

    readme = verify_path.with_name("README.md").read_text()
    assert "review.py run" in readme
    assert "--artifact-dir" in readme
    assert "production generator remains unchanged" in readme.lower()
