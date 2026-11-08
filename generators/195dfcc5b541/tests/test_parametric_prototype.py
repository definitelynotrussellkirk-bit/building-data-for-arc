"""Focused contract tests for the proposed 195dfcc5b541 parametric prototype."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"
RUNTIME = next(parent for parent in HOME.parents if (parent / "shared" / "runtime").is_dir())
for path in (RUNTIME / "shared" / "runtime", RUNTIME / "src"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from reviewer_support import canonical_path, public_challenge_bytes, public_challenge_id  # noqa: E402


def load_module(filename: str, name: str):
    path = PARAMETRIC / filename
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


proto = load_module("prototype.py", "parametric_prototype_195dfcc5b541")


def canonical_row():
    for line in canonical_path(RUNTIME).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == proto.TASK_ID:
            return row
    raise AssertionError("canonical row missing")


def json_hash(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def test_default_program_is_byte_exact_canonical_authority():
    source = canonical_row()["program_solution"]
    assert proto.DEFAULT_SETTING == ("dihedral", "left_to_right")
    assert proto.program_for() == source
    assert proto.normalized_source_hash(source) == proto.CANONICAL_RULE_HASH
    assert proto.normalized_program_hash() == proto.CANONICAL_RULE_HASH


def test_four_program_settings_are_bounded_and_distinct():
    assert proto.SETTINGS == (
        ("dihedral", "left_to_right"),
        ("dihedral", "right_to_left"),
        ("rotations_only", "left_to_right"),
        ("rotations_only", "right_to_left"),
    )
    programs = {setting: proto.program_for(*setting) for setting in proto.SETTINGS}
    assert len(set(programs.values())) == 4
    assert len({proto.exact_program_hash(*setting) for setting in proto.SETTINGS}) == 4
    assert "(list 1 (flip base))" not in programs[("rotations_only", "left_to_right")]
    assert "(else (> (third a) (third b)))" in programs[("dihedral", "right_to_left")]


def test_default_python_solver_replays_all_canonical_labels():
    row = canonical_row()
    for pair in [*row["train"], *row["test"]]:
        assert proto.solve(pair["input"]) == pair["output"]


def test_generated_teaching_input_separates_all_four_settings():
    episode = proto.generate_episode(
        17,
        reflection_mode="dihedral",
        column_order="left_to_right",
        n_train=1,
        n_test=1,
    )
    grid = episode["train"][0]["input"]
    outputs = {
        setting: proto.solve(
            grid,
            reflection_mode=setting[0],
            column_order=setting[1],
        )
        for setting in proto.SETTINGS
    }
    assert len({json_hash(output) for output in outputs.values()}) == 4
    provenance = episode["private"]["pairs"][0]
    assert provenance["overlap_patch"]["height"] == 2
    assert provenance["overlap_patch"]["width"] == 4
    assert provenance["all_setting_outputs_distinct"] is True


def test_episode_is_deterministic_fixed_setting_and_three_plus_four_by_default():
    first = proto.generate_episode(
        20261023,
        reflection_mode="rotations_only",
        column_order="right_to_left",
    )
    second = proto.generate_episode(
        20261023,
        reflection_mode="rotations_only",
        column_order="right_to_left",
    )
    assert first == second
    assert first["private"]["setting"] == {
        "reflection_mode": "rotations_only",
        "column_order": "right_to_left",
    }
    assert len(first["train"]) == proto.DEFAULT_N_TRAIN == 3
    assert len(first["test"]) == proto.DEFAULT_N_TEST == 4
    assert first["private"]["program_sha256"] == proto.exact_program_hash(
        "rotations_only", "right_to_left"
    )


def test_every_episode_pair_is_unique_lawful_and_refutes_every_other_setting():
    episode = proto.generate_episode(
        991,
        reflection_mode="dihedral",
        column_order="right_to_left",
    )
    setting = ("dihedral", "right_to_left")
    pairs = [*episode["train"], *episode["test"]]
    input_hashes = [json_hash(pair["input"]) for pair in pairs]
    assert len(input_hashes) == len(set(input_hashes)) == 7

    generator = proto.selected_generator()[0]
    for pair in pairs:
        assert generator.self_check(pair["input"]) == []
        assert pair["output"] == proto.solve(
            pair["input"], reflection_mode=setting[0], column_order=setting[1]
        )
        for rival in proto.SETTINGS:
            if rival == setting:
                continue
            assert proto.solve(
                pair["input"], reflection_mode=rival[0], column_order=rival[1]
            ) != pair["output"]

    checks = proto.lesson_checks(episode)
    assert checks["demos_refute_all_rivals"] is True
    assert checks["all_queries_identifiable"] is True
    assert checks["all_queries_setting_sensitive"] is True
    assert len(checks["queries"]) == 4


def test_public_projection_masks_private_fields_and_query_answers():
    episode = proto.generate_episode(
        123,
        reflection_mode="rotations_only",
        column_order="left_to_right",
    )
    public = proto.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])

    raw = proto.public_bytes(episode)
    assert raw == public_challenge_bytes(episode)
    assert proto.public_id(episode) == public_challenge_id(episode)
    assert proto.public_id(episode) == hashlib.sha256(raw).hexdigest()
    decoded = raw.decode("utf-8")
    for forbidden in (
        "reflection_mode",
        "column_order",
        "program_sha256",
        "generator_seed",
        "sample_index",
        '"seed"',
    ):
        assert forbidden not in decoded
    for pair in episode["test"]:
        assert json.dumps(pair["output"], separators=(",", ":")) not in decoded


@pytest.mark.parametrize(
    "call",
    [
        lambda: proto.program_for("bad", "left_to_right"),
        lambda: proto.program_for("dihedral", "bad"),
        lambda: proto.program_for(True, "left_to_right"),
        lambda: proto.generate_episode(-1),
        lambda: proto.generate_episode(True),
        lambda: proto.generate_episode(0, n_train=0),
        lambda: proto.generate_episode(0, n_test=True),
        lambda: proto.generate_episode(0, reflection_mode=3),
        lambda: proto.generate_episode(0, column_order=None, n_test="4"),
    ],
)
def test_invalid_parameters_fail_loudly(call):
    with pytest.raises((TypeError, ValueError)):
        call()


def test_racket_verifier_materializes_four_complete_masked_episodes(tmp_path):
    verify = load_module("verify.py", "parametric_verify_195dfcc5b541")
    artifact_dir = tmp_path / "artifacts"
    report = verify.build_report(seed_base=20261023, artifact_dir=artifact_dir)

    assert report["status"] == "pass"
    assert report["canonical_default"] == {
        "program_byte_exact": True,
        "program_hash_exact": True,
        "labeled_pairs": 5,
        "racket_exact": True,
    }
    assert report["totals"] == {
        "settings": 4,
        "episodes": 4,
        "demonstrations": 12,
        "queries": 16,
        "stored_labels_checked_by_racket": 28,
        "rival_labels_checked_by_racket": 84,
        "query_rival_checks": 48,
    }
    assert len(report["settings"]) == 4
    assert all(row["status"] == "pass" for row in report["settings"])
    assert all(row["racket_matches_stored"] for row in report["settings"])
    assert all(row["racket_matches_python_for_all_settings"] for row in report["settings"])
    assert all(row["demos_refute_all_rivals"] for row in report["settings"])
    assert all(row["all_queries_identifiable"] for row in report["settings"])
    assert all(row["all_queries_setting_sensitive"] for row in report["settings"])

    public_files = sorted((artifact_dir / "public").glob("challenge-*.json"))
    rule_files = sorted((artifact_dir / "private" / "rules").glob("*.rkt"))
    episode_files = sorted((artifact_dir / "private" / "episodes").glob("*.json"))
    assert len(public_files) == len(rule_files) == len(episode_files) == 4
    for path in public_files:
        payload = path.read_bytes()
        digest = hashlib.sha256(payload).hexdigest()
        assert path.name == f"challenge-{digest}.json"
        challenge = json.loads(payload)
        assert set(challenge) == {"train", "test"}
        assert len(challenge["train"]) == 3
        assert len(challenge["test"]) == 4
        assert all(set(pair) == {"input"} for pair in challenge["test"])
        assert "reflection_mode" not in payload.decode("utf-8")
        assert "column_order" not in payload.decode("utf-8")


def test_adversarial_probe_checks_sampler_boundaries_and_second_racket_seed():
    probe = load_module("adversarial_probe.py", "parametric_probe_195dfcc5b541")
    report = probe.build_report(seed_start=0, seed_count=2)
    assert report["status"] == "pass"
    assert report["seed_sweep"]["episodes"] == 8
    assert report["seed_sweep"]["pairs"] == 16
    assert report["seed_sweep"]["failures"] == []
    assert report["seed_sweep"]["max_accepted_attempt"] < proto.MAX_CANDIDATE_ATTEMPTS
    assert report["public_projection_invariance"] == {
        "private_metadata_does_not_change_id": True,
        "query_answers_do_not_change_id": True,
        "visible_demo_output_changes_id": True,
    }
    assert report["count_boundary"] == {
        "n_train": 16,
        "n_test": 16,
        "unique_inputs": 32,
        "status": "pass",
    }
    assert report["racket_recheck"]["status"] == "pass"
    assert report["racket_recheck"]["settings"] == 4
    assert report["racket_recheck"]["stored_labels_checked_by_racket"] == 28
