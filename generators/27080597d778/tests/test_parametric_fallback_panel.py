"""Focused tests for the proposed fallback-panel rule parameter.

The production generator and canonical authority stay unchanged. These tests
exercise the separate task-local prototype requested by PARAMETRIC-RULES.md.
"""
from __future__ import annotations

from copy import deepcopy
from functools import cache
import importlib.util
from pathlib import Path

import pytest

from reviewer_support import find_root

TASK_ID = "27080597d778"
ROOT = find_root(__file__)
PROTOTYPE_PATH = (
    ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"
)
AUDIT_PATH = ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "audit.py"


@cache
def prototype():
    assert PROTOTYPE_PATH.is_file(), "fallback-panel parametric prototype is not implemented"
    spec = importlib.util.spec_from_file_location(
        "parametric_fallback_panel_27080597d778", PROTOTYPE_PATH
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@cache
def auditor():
    assert AUDIT_PATH.is_file(), "parametric adversarial auditor is not implemented"
    spec = importlib.util.spec_from_file_location(
        "parametric_fallback_panel_audit_27080597d778", AUDIT_PATH
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


FAILURE_WITNESS = [
    [1, 0, 0, 0, 5, 2, 0, 0, 0],
    [0, 1, 0, 0, 5, 0, 0, 2, 0],
    [0, 0, 1, 0, 5, 0, 0, 0, 2],
]
FAILURE_LEFT = [
    [1, 0, 0, 0],
    [0, 1, 0, 0],
    [0, 0, 1, 0],
]
FAILURE_RIGHT = [
    [2, 0, 0, 0],
    [0, 0, 2, 0],
    [0, 0, 0, 2],
]
COMPLEMENT_WITNESS = [
    [1, 0, 0, 0, 5, 0, 2, 2, 2],
    [0, 1, 0, 0, 5, 2, 0, 2, 2],
    [0, 0, 1, 0, 5, 2, 2, 0, 2],
]
COMPLEMENT_OVERLAY = [
    [1, 2, 2, 2],
    [2, 1, 2, 2],
    [2, 2, 1, 2],
]


def test_default_rule_is_exact_canonical_and_setting_validation_is_strict():
    p = prototype()
    canonical = p.canonical_record(root=ROOT)["program_solution"]
    assert p.PARAMETER_SPEC == {
        "name": "fallback_panel",
        "values": ("left", "right"),
        "default": "left",
    }
    assert p.program_for("left", root=ROOT) == canonical
    assert p.program_for("right", root=ROOT) != canonical
    for invalid in (None, "overlay", "LEFT", 0, True, ["left"]):
        with pytest.raises(ValueError, match="fallback_panel"):
            p.program_for(invalid, root=ROOT)


def test_python_semantics_change_only_the_noncomplement_fallback():
    p = prototype()
    failure = deepcopy(FAILURE_WITNESS)
    complement = deepcopy(COMPLEMENT_WITNESS)
    assert p.apply_python(failure, "left") == FAILURE_LEFT
    assert p.apply_python(failure, "right") == FAILURE_RIGHT
    assert p.apply_python(complement, "left") == COMPLEMENT_OVERLAY
    assert p.apply_python(complement, "right") == COMPLEMENT_OVERLAY
    assert failure == FAILURE_WITNESS
    assert complement == COMPLEMENT_WITNESS


def test_both_exact_programs_execute_in_racket_and_match_hand_checked_outputs():
    p = prototype()
    from arc_repl.racket_bridge import RacketBridge

    with RacketBridge() as bridge:
        for setting, expected_failure in (
            ("left", FAILURE_LEFT),
            ("right", FAILURE_RIGHT),
        ):
            program = p.program_for(setting, root=ROOT)
            assert p.execute(bridge, program, FAILURE_WITNESS) == expected_failure
            assert p.execute(bridge, program, COMPLEMENT_WITNESS) == COMPLEMENT_OVERLAY


def _branch(grid):
    overlap = any(grid[r][c] and grid[r][c + 5] for r in range(len(grid)) for c in range(4))
    gap = any(not grid[r][c] and not grid[r][c + 5] for r in range(len(grid)) for c in range(4))
    if overlap and gap:
        overlaps = sum(bool(row[c]) and bool(row[c + 5]) for row in grid for c in range(4))
        gaps = sum(not row[c] and not row[c + 5] for row in grid for c in range(4))
        return "balanced" if overlaps == gaps else "mixed"
    return "overlap" if overlap else "gap" if gap else "complement"


@pytest.mark.parametrize("seed,expected_setting", [(0, "left"), (1, "right")])
def test_episode_chooses_one_setting_and_has_four_distinct_queries(seed, expected_setting):
    p = prototype()
    from arc_repl.racket_bridge import RacketBridge

    with RacketBridge(max_calls_before_restart=128) as bridge:
        episode = p.build_episode(
            seed=seed,
            bridge=bridge,
            difficulty="medium",
            start_index=0,
            n_train=4,
            n_test=4,
            root=ROOT,
        )
        replay = p.build_episode(
            seed=seed,
            bridge=bridge,
            difficulty="medium",
            start_index=0,
            n_train=4,
            n_test=4,
            root=ROOT,
        )

    assert episode == replay
    assert episode["meta"]["parameters"] == {"fallback_panel": expected_setting}
    assert episode["meta"]["parameter_scope"] == "chosen once per episode"
    assert len(episode["train"]) == 4
    assert len(episode["test"]) == 4
    assert {_branch(pair["input"]) for pair in episode["train"]} == {
        "complement", "overlap", "gap", "balanced"
    }
    assert {_branch(pair["input"]) for pair in episode["test"]} == {
        "complement", "overlap", "gap", "balanced"
    }
    inputs = [pair["input"] for pair in [*episode["train"], *episode["test"]]]
    assert len({repr(grid) for grid in inputs}) == 8
    assert all(pair["output"] == p.apply_python(pair["input"], expected_setting)
               for pair in [*episode["train"], *episode["test"]])


@pytest.mark.parametrize("setting", ["left", "right"])
def test_demonstrations_identify_setting_before_every_query(setting):
    p = prototype()
    from arc_repl.racket_bridge import RacketBridge

    with RacketBridge(max_calls_before_restart=128) as bridge:
        episode = p.build_episode(
            seed=19,
            fallback_panel=setting,
            bridge=bridge,
            difficulty="hard",
            start_index=5,
            n_train=4,
            n_test=4,
            root=ROOT,
        )

    checks = episode["analysis"]["parameter_rivals"]
    assert checks[setting]["matches_all_demonstrations"] is True
    other = "right" if setting == "left" else "left"
    assert checks[other]["matches_all_demonstrations"] is False
    assert checks[other]["distinguishing_demo_indices"]
    assert len(episode["analysis"]["queries"]) == 4
    for query in episode["analysis"]["queries"]:
        assert query["conflicting_parameter_settings"] == []
        assert query["selected_output_matches_racket"] is True
        assert query["selected_output_matches_python"] is True


@pytest.mark.parametrize(
    "kwargs,match",
    [
        ({"seed": True}, "seed"),
        ({"seed": 0, "start_index": -1}, "start_index"),
        ({"seed": 0, "n_train": 0}, "n_train"),
        ({"seed": 0, "n_test": 0}, "n_test"),
        ({"seed": 0, "difficulty": "extreme"}, "difficulty"),
    ],
)
def test_episode_rejects_invalid_counts_and_controls(kwargs, match):
    p = prototype()
    from arc_repl.racket_bridge import RacketBridge

    defaults = {
        "seed": 0,
        "difficulty": "medium",
        "start_index": 0,
        "n_train": 4,
        "n_test": 4,
        "root": ROOT,
    }
    defaults.update(kwargs)
    with RacketBridge() as bridge, pytest.raises((TypeError, ValueError), match=match):
        p.build_episode(bridge=bridge, **defaults)


def test_public_projection_and_id_ignore_private_metadata_and_query_answers():
    p = prototype()
    from arc_repl.racket_bridge import RacketBridge
    from reviewer_support import public_challenge_bytes, public_challenge_id

    with RacketBridge(max_calls_before_restart=128) as bridge:
        episode = p.build_episode(seed=7, bridge=bridge, root=ROOT)
    public = p.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    assert p.public_bytes(episode) == public_challenge_bytes(public)
    identifier = p.public_id(episode)
    assert identifier == public_challenge_id(public)

    changed_private = deepcopy(episode)
    changed_private["meta"]["seed"] = 999999
    changed_private["meta"]["parameters"]["fallback_panel"] = "left"
    changed_private["analysis"] = {"replaced": True}
    for pair in changed_private["test"]:
        pair["output"] = [[9] * 4 for _ in pair["output"]]
    assert p.public_id(changed_private) == identifier
    assert p.public_bytes(changed_private) == p.public_bytes(episode)

    public["train"][0]["input"][0][0] = 9
    assert episode["train"][0]["input"][0][0] != 9


def test_writer_uses_opaque_sorted_ids_and_keeps_settings_and_answers_private(tmp_path):
    p = prototype()
    import hashlib
    import json
    import re

    out = tmp_path / "evidence"
    manifest = p.write_evidence(
        out,
        seeds=[1, 0],
        difficulty="medium",
        start_index=0,
        n_train=4,
        n_test=4,
        root=ROOT,
    )
    assert manifest["status"] == p.STATUS
    assert manifest["parameter"] == {
        "name": "fallback_panel",
        "allowed": ["left", "right"],
        "default": "left",
    }
    assert manifest["canonical_default_unchanged"] is True
    assert manifest["canonical_replay"]["pairs_checked"] == 9
    assert manifest["canonical_replay"]["passed"] is True
    assert len(manifest["episodes"]) == 2
    assert [row["public_id"] for row in manifest["episodes"]] == sorted(
        row["public_id"] for row in manifest["episodes"]
    )

    public_files = sorted((out / "public").glob("*.json"))
    assert len(public_files) == 2
    for path in public_files:
        assert re.fullmatch(r"challenge-[0-9a-f]{64}\.json", path.name)
        data = json.loads(path.read_text())
        assert set(data) == {"train", "test"}
        assert len(data["train"]) == 4 and len(data["test"]) == 4
        assert all(set(pair) == {"input"} for pair in data["test"])
        text = path.read_text()
        assert "fallback_panel" not in text
        assert '"seed"' not in text
        assert "program" not in text
        public_id = path.stem.removeprefix("challenge-")
        assert hashlib.sha256(path.read_bytes()).hexdigest() == public_id

    setting_map = json.loads((out / "private" / "setting-map.json").read_text())
    assert {row["fallback_panel"] for row in setting_map} == {"left", "right"}
    assert {row["public_id"] for row in setting_map} == {
        row["public_id"] for row in manifest["episodes"]
    }
    for row in manifest["episodes"]:
        private = json.loads((out / row["private_file"]).read_text())
        assert len(private["test"]) == 4
        assert all(set(pair) == {"input", "output"} for pair in private["test"])
    assert (out / "rules" / "left.rkt").read_text() == p.program_for("left", root=ROOT)
    assert (out / "rules" / "right.rkt").read_text() == p.program_for("right", root=ROOT)

    report = auditor().audit_export(out, root=ROOT)
    assert report["passed"] is True
    assert report["public_challenges_checked"] == 2
    assert report["paired_inputs_identical"] is True
    assert report["private_settings"] == ["left", "right"]

    import shutil
    tampered = tmp_path / "tampered"
    shutil.copytree(out, tampered)
    public_path = next((tampered / "public").glob("*.json"))
    public_path.write_bytes(public_path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="public hash mismatch"):
        auditor().audit_export(tampered, root=ROOT)

    tampered_manifest = tmp_path / "tampered-manifest"
    shutil.copytree(out, tampered_manifest)
    manifest_path = tampered_manifest / "manifest.json"
    bad_manifest = json.loads(manifest_path.read_text())
    bad_manifest["prototype_sha256"] = "0" * 64
    manifest_path.write_text(json.dumps(bad_manifest, sort_keys=True))
    with pytest.raises(ValueError, match="prototype hash mismatch"):
        auditor().audit_export(tampered_manifest, root=ROOT)


def test_adversarial_auditor_runs_bounded_real_racket_matrix():
    report = auditor().audit_rule_matrix(
        root=ROOT,
        input_seeds=[0],
        sample_indices=[0, 1, 2, 3],
        difficulties=["easy"],
    )
    assert report["passed"] is True
    assert report["inputs_checked"] == 4
    assert report["racket_evaluations"] == 8
    assert report["branch_counts"] == {
        "balanced": 1,
        "complement": 1,
        "gap": 1,
        "overlap": 1,
    }
    assert report["distinguishing_noncomplements"] == 3


def test_writer_rejects_duplicate_public_payloads_without_creating_output(tmp_path):
    p = prototype()
    out = tmp_path / "duplicates"
    with pytest.raises(ValueError, match="duplicate public challenge"):
        p.write_evidence(out, seeds=[3, 3], root=ROOT)
    assert not out.exists()


def test_paired_parameter_seeds_hold_inputs_fixed_while_rule_outputs_change():
    p = prototype()
    from arc_repl.racket_bridge import RacketBridge

    with RacketBridge(max_calls_before_restart=128) as bridge:
        left = p.build_episode(seed=0, bridge=bridge, root=ROOT)
        right = p.build_episode(seed=1, bridge=bridge, root=ROOT)

    left_pairs = [*left["train"], *left["test"]]
    right_pairs = [*right["train"], *right["test"]]
    assert [pair["input"] for pair in left_pairs] == [pair["input"] for pair in right_pairs]
    assert left["meta"]["input_seed"] == right["meta"]["input_seed"] == 0
    branches = [_branch(pair["input"]) for pair in left_pairs]
    for branch, left_pair, right_pair in zip(branches, left_pairs, right_pairs):
        if branch == "complement":
            assert left_pair["output"] == right_pair["output"]
        else:
            assert left_pair["output"] != right_pair["output"]
