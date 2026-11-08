from __future__ import annotations

import hashlib
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from reviewer_support import (
    canonical_path,
    find_root,
    public_challenge_bytes,
    public_challenge_id,
)


TASK_ID = "0f7d80015d9d"
ROOT = find_root(__file__)
PARAMETRIC_DIR = ROOT / "generators" / TASK_ID / "workspace" / "parametric"
PROTOTYPE_PATH = PARAMETRIC_DIR / "prototype.py"
VERIFY_PATH = PARAMETRIC_DIR / "verify.py"
RETAIN_PATH = PARAMETRIC_DIR / "retain.py"
CHECK_RETAINED_PATH = PARAMETRIC_DIR / "check_retained.py"


_PROTOTYPE = None
_VERIFIER = None
_RETAINER = None
_RETAINED_CHECKER = None


def _prototype():
    global _PROTOTYPE
    assert PROTOTYPE_PATH.is_file(), "parametric prototype has not been implemented"
    if _PROTOTYPE is None:
        name = "_test_parametric_stamp_rule_prototype"
        spec = importlib.util.spec_from_file_location(name, PROTOTYPE_PATH)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        _PROTOTYPE = module
    return _PROTOTYPE


def _verifier():
    global _VERIFIER
    assert VERIFY_PATH.is_file(), "parametric verifier has not been implemented"
    if _VERIFIER is None:
        name = "_test_parametric_stamp_rule_verifier"
        spec = importlib.util.spec_from_file_location(name, VERIFY_PATH)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        _VERIFIER = module
    return _VERIFIER


def _retainer():
    global _RETAINER
    assert RETAIN_PATH.is_file(), "parametric retainer has not been implemented"
    if _RETAINER is None:
        name = "_test_parametric_stamp_rule_retainer"
        spec = importlib.util.spec_from_file_location(name, RETAIN_PATH)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        _RETAINER = module
    return _RETAINER


def _retained_checker():
    global _RETAINED_CHECKER
    assert CHECK_RETAINED_PATH.is_file(), "retained checker has not been implemented"
    if _RETAINED_CHECKER is None:
        name = "_test_parametric_stamp_rule_retained_checker"
        spec = importlib.util.spec_from_file_location(name, CHECK_RETAINED_PATH)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        _RETAINED_CHECKER = module
    return _RETAINED_CHECKER


@pytest.fixture(scope="module")
def racket_verification(tmp_path_factory):
    verifier = _verifier()
    output_dir = tmp_path_factory.mktemp("parametric-racket-verification")
    manifest = verifier.run_verification(
        settings=tuple(reversed(verifier.prototype.SETTINGS[:2])),
        seed=20261023,
        train_count=3,
        query_count=4,
        output_dir=output_dir,
        overwrite=False,
    )
    return verifier, output_dir, manifest


def _canonical_program() -> str:
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row["program_solution"]
    raise AssertionError("canonical task record missing")


def _midpoint_fixture() -> list[list[int]]:
    grid = [[7 for _ in range(9)] for _ in range(7)]
    for row in range(4, 7):
        for col in range(2, 7):
            grid[row][col] = 5
    grid[1][4] = 2  # exact rectangle midpoint
    grid[2][5] = 8
    return grid


def test_default_program_is_byte_for_byte_canonical():
    prototype = _prototype()
    """Catches a prototype silently relabeling or rewriting canonical authority."""
    assert prototype.program_for(prototype.DEFAULT_SETTING) == _canonical_program()


def test_all_four_settings_have_hand_derived_midpoint_destinations():
    prototype = _prototype()
    """Catches swapped relation or midpoint branches in either prototype mirror."""
    grid = _midpoint_fixture()
    expected_destination = {
        ("opposite", "right"): 1,
        ("opposite", "left"): 7,
        ("same", "right"): 7,
        ("same", "left"): 1,
    }

    for setting in prototype.SETTINGS:
        output = prototype.apply_setting(grid, setting)
        destination = expected_destination[
            (setting.stamp_relation, setting.midpoint_side)
        ]
        assert output[1][4] == 7
        assert output[2][5] == 2
        assert output[6][destination] == 8
        assert sum(value == 8 for row in output for value in row) == 1


def test_episode_has_one_fixed_identifiable_setting_and_four_unique_queries():
    prototype = _prototype()
    """Catches per-pair resampling, duplicate queries, or demo ambiguity."""
    selected = prototype.RuleSetting("same", "left")
    episode = prototype.build_episode(
        20261023,
        setting=selected,
        n_train=3,
        n_test=4,
    )

    assert episode["parameters"] == {
        "stamp_relation": "same",
        "midpoint_side": "left",
    }
    assert episode["program"] == prototype.program_for(selected)
    assert len(episode["train"]) == 3
    assert len(episode["test"]) == 4
    assert prototype.setting_survivors(episode["train"]) == [selected]
    assert prototype.episode_errors(episode) == []

    inputs = [pair["input"] for split in ("train", "test") for pair in episode[split]]
    serialized = [json.dumps(grid, separators=(",", ":")) for grid in inputs]
    assert len(serialized) == len(set(serialized)) == 7

    query_serialized = [
        json.dumps(pair["input"], separators=(",", ":")) for pair in episode["test"]
    ]
    assert len(query_serialized) == len(set(query_serialized)) == 4

    for grid in inputs:
        facts = prototype.analyze_scene(grid)
        _top, _bottom, left, right = facts["rect"]
        assert left > 0
        assert right < facts["width"] - 1


def test_public_projection_masks_hidden_rule_and_query_answers():
    prototype = _prototype()
    """Catches hidden setting, seed, rule, or labels leaking through public export."""
    episode = prototype.build_episode(
        91,
        setting=prototype.RuleSetting("opposite", "left"),
        n_train=3,
        n_test=4,
    )
    public = prototype.public_projection(episode)
    payload = json.dumps(public, sort_keys=True)

    assert "parameters" not in payload
    assert "program" not in payload
    assert "seed" not in payload
    assert all(set(pair) == {"input"} for pair in public["test"])
    assert prototype.public_identifier(episode) == public_challenge_id(public)

    hidden_only_mutation = deepcopy(episode)
    hidden_only_mutation["seed"] = 123456789
    hidden_only_mutation["parameters"] = {
        "stamp_relation": "same",
        "midpoint_side": "right",
    }
    hidden_only_mutation["program"] = "private replacement"
    assert prototype.public_identifier(hidden_only_mutation) == prototype.public_identifier(episode)


def test_public_batch_plan_uses_exact_bytes_sorts_ids_and_rejects_duplicates():
    prototype = _prototype()
    episodes = [
        prototype.build_episode(20261023, setting=setting, n_train=3, n_test=4)
        for setting in prototype.SETTINGS
    ]

    planned = prototype.plan_public_batch(reversed(episodes))
    assert [row["public_id"] for row in planned] == sorted(
        row["public_id"] for row in planned
    )
    assert len(planned) == 4
    for row in planned:
        expected = public_challenge_bytes(prototype.public_projection(row["episode"]))
        assert row["public_bytes"] == expected
        assert hashlib.sha256(row["public_bytes"]).hexdigest() == row["public_id"]

    hidden_duplicate = deepcopy(episodes[0])
    hidden_duplicate["seed"] = 999999
    hidden_duplicate["program"] = "private replacement"
    hidden_duplicate["test"][0]["output"] = [[9]]
    with pytest.raises(ValueError, match="duplicate public challenge"):
        prototype.plan_public_batch([episodes[0], hidden_duplicate])

    with pytest.raises(ValueError, match="at least one episode"):
        prototype.plan_public_batch([])


def test_invalid_settings_and_insufficient_episode_counts_fail_closed():
    prototype = _prototype()
    """Catches permissive APIs producing unidentifiable or undersized episodes."""
    with pytest.raises(ValueError):
        prototype.program_for(prototype.RuleSetting("diagonal", "right"))
    with pytest.raises(ValueError):
        prototype.program_for(prototype.RuleSetting("same", "center"))
    with pytest.raises(TypeError):
        prototype.build_episode(True)
    with pytest.raises(ValueError):
        prototype.build_episode(1, n_train=2, n_test=4)
    with pytest.raises(ValueError):
        prototype.build_episode(1, n_train=3, n_test=3)


def test_racket_verifier_writes_exact_public_bytes_in_public_id_order(
    racket_verification,
):
    verifier, output_dir, manifest = racket_verification
    public_ids = [row["public_id"] for row in manifest["episodes"]]

    assert public_ids == sorted(public_ids)
    assert verifier.prototype.program_for(
        verifier.prototype.DEFAULT_SETTING
    ) == _canonical_program()
    for row in manifest["episodes"]:
        public_id = row["public_id"]
        raw = (output_dir / public_id / "public.json").read_bytes()
        assert hashlib.sha256(raw).hexdigest() == public_id
        assert row["files"]["public.json"]["sha256"] == public_id
        assert raw == public_challenge_bytes(json.loads(raw))


def test_retention_preflights_then_writes_exact_bytes_in_public_id_order(
    racket_verification,
    tmp_path,
):
    _verifier_module, checks_dir, manifest = racket_verification
    retainer = _retainer()
    reversed_manifest = deepcopy(manifest)
    reversed_manifest["episodes"] = list(reversed(reversed_manifest["episodes"]))
    examples_dir = tmp_path / "examples"
    racket_dir = tmp_path / "racket"

    retained = retainer.retain_verified_batch(
        checks_dir=checks_dir,
        checked=reversed_manifest,
        examples_dir=examples_dir,
        racket_dir=racket_dir,
        overwrite=False,
    )

    retained_ids = [row["public_id"] for row in retained]
    assert retained_ids == sorted(retained_ids)
    assert [
        path.stem for path in sorted(examples_dir.glob("*.json"))
    ] == retained_ids
    assert [
        path.stem for path in sorted(racket_dir.glob("*.rkt"))
    ] == retained_ids
    for public_path in sorted(examples_dir.glob("*.json")):
        raw = public_path.read_bytes()
        assert hashlib.sha256(raw).hexdigest() == public_path.stem
        assert raw == public_challenge_bytes(json.loads(raw))

    duplicate_manifest = deepcopy(manifest)
    duplicate_manifest["episodes"].append(
        deepcopy(duplicate_manifest["episodes"][0])
    )
    duplicate_examples = tmp_path / "duplicate-examples"
    duplicate_racket = tmp_path / "duplicate-racket"
    with pytest.raises(ValueError, match="duplicate"):
        retainer.retain_verified_batch(
            checks_dir=checks_dir,
            checked=duplicate_manifest,
            examples_dir=duplicate_examples,
            racket_dir=duplicate_racket,
            overwrite=False,
        )
    assert not duplicate_examples.exists()
    assert not duplicate_racket.exists()


def test_retention_summary_update_preserves_historical_siblings(tmp_path):
    """Catches current retention erasing evidence from earlier review returns."""
    retainer = _retainer()
    reported_dir = tmp_path / "reviewer-reported"
    historical = reported_dir / "older-return" / "receipt.json"
    historical.parent.mkdir(parents=True)
    historical.write_text('{"status":"historical"}\n', encoding="utf-8")
    summary_path = reported_dir / "verification-summary.json"
    summary_path.write_text('{"status":"old"}\n', encoding="utf-8")

    retainer.write_reported_summary(
        summary_path,
        {"status": "passed", "assignment_id": "review-current"},
        overwrite=True,
    )

    assert json.loads(summary_path.read_text(encoding="utf-8")) == {
        "assignment_id": "review-current",
        "status": "passed",
    }
    assert historical.read_text(encoding="utf-8") == '{"status":"historical"}\n'


def test_retained_summary_command_uses_verifier_manifest_argv():
    """Catches a retained receipt claiming a stale or hard-coded verifier path."""
    retainer = _retainer()
    checked = {
        "cwd": "/private/packet/WORK/repo",
        "argv": [
            "generators/0f7d80015d9d/workspace/parametric/verify.py",
            "--all-settings",
            "--output-dir",
            "../checks/custom-final",
        ],
    }

    assert retainer.verification_command(checked) == {
        "cwd": "repo",
        "argv": [
            "python3",
            "generators/0f7d80015d9d/workspace/parametric/verify.py",
            "--all-settings",
            "--output-dir",
            "../checks/custom-final",
        ],
    }


def test_retained_checker_rejects_noncanonical_or_misnamed_public_bytes(tmp_path):
    prototype = _prototype()
    checker = _retained_checker()
    episode = prototype.build_episode(
        20261023,
        setting=prototype.DEFAULT_SETTING,
        n_train=3,
        n_test=4,
    )
    public = prototype.public_projection(episode)
    canonical = public_challenge_bytes(public)
    public_id = hashlib.sha256(canonical).hexdigest()

    pretty_path = tmp_path / f"{public_id}.json"
    pretty_path.write_text(
        json.dumps(public, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    assert pretty_path.read_bytes() != canonical
    with pytest.raises(ValueError, match="canonical"):
        checker._load_canonical_public(pretty_path)

    misnamed_path = tmp_path / ("0" * 64 + ".json")
    misnamed_path.write_bytes(canonical)
    with pytest.raises(ValueError, match="hash to filename"):
        checker._load_canonical_public(misnamed_path)
