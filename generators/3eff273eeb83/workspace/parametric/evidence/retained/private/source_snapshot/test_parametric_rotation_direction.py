"""Contract tests for the proposed, unapproved rotation-direction prototype."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, find_root


TASK_ID = "3eff273eeb83"
ROOT = find_root(__file__)
PROTOTYPE_DIR = ROOT / f"generators/{TASK_ID}/workspace/parametric"
PROTOTYPE_PATH = PROTOTYPE_DIR / "prototype.py"
README_PATH = PROTOTYPE_DIR / "README.md"


def _load_prototype():
    assert PROTOTYPE_PATH.is_file(), "rotation-direction prototype is missing"
    spec = importlib.util.spec_from_file_location(
        "parametric_3eff273eeb83_rotation", PROTOTYPE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge() as runtime:
        yield runtime


def test_prototype_files_and_documented_command_exist():
    assert PROTOTYPE_PATH.is_file()
    assert README_PATH.is_file()
    readme = README_PATH.read_text(encoding="utf-8")
    assert "python3 review.py run" in readme
    assert "proposed" in readme.lower()
    assert "unapproved" in readme.lower()


def test_parameter_contract_and_canonical_default_are_exact():
    prototype = _load_prototype()
    assert prototype.PROTOTYPE_STATUS == "proposed_unapproved"
    assert prototype.PARAMETER_NAME == "rotation_direction"
    assert prototype.SETTINGS == ("clockwise", "counterclockwise")
    assert prototype.DEFAULT_SETTING == "clockwise"

    canonical = prototype.canonical_source(root=ROOT)
    assert hashlib.sha256(canonical.encode()).hexdigest() == prototype.CANONICAL_SHA256
    assert prototype.materialize_rule("clockwise", root=ROOT) == canonical
    counterclockwise = prototype.materialize_rule("counterclockwise", root=ROOT)
    assert counterclockwise != canonical
    assert prototype.restore_canonical(counterclockwise) == canonical


@pytest.mark.parametrize("value", [True, 1, None, "left", "clock-wise"])
def test_invalid_rotation_setting_is_rejected(value):
    prototype = _load_prototype()
    with pytest.raises(ValueError):
        prototype.materialize_rule(value, root=ROOT)


def test_clockwise_rule_reproduces_every_labeled_canonical_pair(bridge):
    prototype = _load_prototype()
    source = prototype.materialize_rule("clockwise", root=ROOT)
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert pairs
    for pair in pairs:
        assert prototype.execute_rule(source, pair["input"], bridge=bridge) == pair["output"]


def test_same_lawful_input_distinguishes_both_rotation_settings(bridge):
    prototype = _load_prototype()
    grid = prototype.build_input(17, 3)
    assert prototype.input_errors(grid) == []
    outputs = {
        setting: prototype.execute_rule(
            prototype.materialize_rule(setting, root=ROOT), grid, bridge=bridge
        )
        for setting in prototype.SETTINGS
    }
    assert outputs["clockwise"] != outputs["counterclockwise"]
    assert outputs["clockwise"] == prototype.apply_python(grid, "clockwise")
    assert outputs["counterclockwise"] == prototype.apply_python(
        grid, "counterclockwise"
    )


def test_episode_selects_once_and_demonstrations_refute_the_other_setting(bridge):
    prototype = _load_prototype()
    clockwise = prototype.make_episode(
        0, setting="clockwise", root=ROOT, bridge=bridge
    )
    counterclockwise = prototype.make_episode(
        1, setting="counterclockwise", root=ROOT, bridge=bridge
    )
    for episode, selected in (
        (clockwise, "clockwise"),
        (counterclockwise, "counterclockwise"),
    ):
        assert episode["parameters"] == {"rotation_direction": selected}
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 1
        assert episode["ambiguities"] == []
        matching = [
            row for row in episode["parameter_rivals"]
            if row["status"] == "matches_episode"
        ]
        refuted = [
            row for row in episode["parameter_rivals"]
            if row["status"] == "refuted_by_demonstrations"
        ]
        assert [row["rotation_direction"] for row in matching] == [selected]
        assert len(refuted) == 1
        assert refuted[0]["demonstration_mismatch_indices"]
        assert refuted[0]["query_mismatch_indices"] == [0]


def test_public_projection_omits_hidden_setting_program_seed_and_query_answer(bridge):
    prototype = _load_prototype()
    episode = prototype.make_episode(0, root=ROOT, bridge=bridge)
    public = prototype.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    serialized = json.dumps(public)
    for forbidden in ("rotation_direction", "racket", "seed", "parameter"):
        assert forbidden not in serialized
    before = json.loads(json.dumps(episode))
    public["train"][0]["input"][0][0] = 9
    assert episode == before


def test_evidence_writer_hashes_artifacts_and_keeps_queries_private(tmp_path):
    prototype = _load_prototype()
    out = tmp_path / "rotation-evidence"
    report = prototype.write_evidence((0, 1), out=out, root=ROOT)
    assert report["passed"] is True
    assert report["status"] == "proposed_unapproved"
    assert report["counts"]["episodes"] == 2
    assert report["counts"]["episode_settings_exercised"] == 2
    assert report["counts"]["ambiguous_parameter_rivals"] == 0
    assert report["counts"]["canonical_pairs_checked"] == len(
        canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    )

    manifest = json.loads((out / "manifest.json").read_text())
    for row in manifest["files"]:
        assert hashlib.sha256((out / row["path"]).read_bytes()).hexdigest() == row["sha256"]
    for row in report["episodes"]:
        public = json.loads((out / row["public_path"]).read_text())
        private = json.loads((out / row["private_path"]).read_text())
        assert public == prototype.public_challenge(private)
        assert "output" not in public["test"][0]
        assert "output" in private["test"][0]
    with pytest.raises(FileExistsError):
        prototype.write_evidence((0, 1), out=out, root=ROOT)


@pytest.mark.parametrize("seed", [False, -1, 2**63, 1.5, "0"])
def test_invalid_episode_seed_is_rejected(seed):
    prototype = _load_prototype()
    with pytest.raises(ValueError):
        prototype.choose_setting(seed)
