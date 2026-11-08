"""Focused tests for the proposed episode-wide symmetry-axis prototype."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "1a5d49e539de"
ROOT = find_root(__file__)
PROTOTYPE_PATH = ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"


def _load_prototype():
    assert PROTOTYPE_PATH.is_file(), "symmetry-axis prototype is missing"
    name = "_test_parametric_symmetry_axis"
    module = sys.modules.get(name)
    if module is not None:
        return module
    spec = importlib.util.spec_from_file_location(name, PROTOTYPE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _canonical_source() -> str:
    sources = set()
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                sources.add(row["program_solution"])
    assert len(sources) == 1
    return sources.pop()


def test_materialized_left_right_rule_is_exact_canonical_and_top_bottom_is_distinct():
    proto = _load_prototype()
    canonical = _canonical_source()
    left_right = proto.materialize_rule("left-right", root=ROOT)
    top_bottom = proto.materialize_rule("top-bottom", root=ROOT)

    assert proto.PARAMETER_SPEC == {
        "name": "symmetry_axis",
        "values": ("left-right", "top-bottom"),
        "default": "left-right",
        "scope": "one fixed value per episode",
    }
    assert left_right == canonical
    assert hashlib.sha256(left_right.encode()).hexdigest() == proto.CANONICAL_RULE_SHA256
    assert top_bottom != left_right
    assert "(- (- oh 1) (first c))" in top_bottom
    assert "(- (- ow 1) (second c))" in left_right


def test_axis_choice_is_deterministic_and_covers_both_values_for_retained_seeds():
    proto = _load_prototype()
    assert proto.choose_symmetry_axis(0) == "top-bottom"
    assert proto.choose_symmetry_axis(1) == "left-right"
    assert proto.choose_symmetry_axis(0) == proto.choose_symmetry_axis(0)
    with pytest.raises((TypeError, ValueError)):
        proto.choose_symmetry_axis(True)


@pytest.mark.parametrize("seed,expected_axis", [(0, "top-bottom"), (1, "left-right")])
def test_complete_episode_has_fixed_axis_three_demos_four_queries_and_refutes_rival(seed, expected_axis):
    proto = _load_prototype()
    episode = proto.build_episode(
        seed=seed,
        difficulty="medium",
        start_index=0,
        n_train=3,
        n_test=4,
    )

    assert episode["meta"]["parameters"] == {"symmetry_axis": expected_axis}
    assert episode["meta"]["parameter_scope"] == "chosen once per episode"
    assert len(episode["train"]) == 3
    assert len(episode["test"]) == 4
    pairs = [*episode["train"], *episode["test"]]
    input_keys = {json.dumps(pair["input"], separators=(",", ":")) for pair in pairs}
    assert len(input_keys) == 7

    rival = proto.other_axis(expected_axis)
    for ordinal, pair in enumerate(pairs):
        assert proto.validate_input(pair["input"], expected_axis) == []
        assert pair["output"] == proto.apply_python(pair["input"], expected_axis)
        assert pair["output"] != proto.apply_python(pair["input"], rival)
        assert pair["source_sample_index"] % 3 == ordinal % 3

    assert proto.parameter_rival_findings(episode) == []


def test_episode_generation_is_deterministic_fresh_and_count_validated():
    proto = _load_prototype()
    first = proto.build_episode(seed=1, n_train=3, n_test=4)
    second = proto.build_episode(seed=1, n_train=3, n_test=4)
    assert first == second
    assert first is not second
    assert first["train"][0]["input"] is not second["train"][0]["input"]

    for kwargs in (
        {"n_train": 0},
        {"n_test": 0},
        {"start_index": -1},
        {"max_attempts_per_pair": 0},
        {"symmetry_axis": "diagonal"},
    ):
        with pytest.raises((TypeError, ValueError)):
            proto.build_episode(seed=1, **kwargs)


def test_racket_rules_match_python_for_selected_and_rival_outputs():
    proto = _load_prototype()
    from arc_repl.racket_bridge import RacketBridge

    with RacketBridge() as bridge:
        for seed in (0, 1):
            episode = proto.build_episode(
                seed=seed,
                n_train=3,
                n_test=4,
                labeler=lambda grid, axis: proto.execute_racket(
                    proto.materialize_rule(axis, root=ROOT), grid, bridge=bridge
                ),
            )
            for pair in [*episode["train"], *episode["test"]]:
                for axis in proto.PARAMETER_SPEC["values"]:
                    actual = proto.execute_racket(
                        proto.materialize_rule(axis, root=ROOT),
                        pair["input"],
                        bridge=bridge,
                    )
                    assert actual == proto.apply_python(pair["input"], axis)


def test_public_projection_and_id_ignore_private_fields_and_query_answers():
    proto = _load_prototype()
    episode = proto.build_episode(seed=1, n_train=3, n_test=4)
    public = proto.public_challenge(episode)

    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    original_id = public_challenge_id(public)
    assert public_challenge_bytes(public).decode("utf-8").endswith("\n")

    private_mutation = copy.deepcopy(episode)
    private_mutation["meta"]["seed"] = 999999
    private_mutation["meta"]["parameters"]["symmetry_axis"] = "top-bottom"
    private_mutation["test"][0]["output"] = [[9]]
    private_mutation["racket_source"] = "private-only"
    assert public_challenge_id(proto.public_challenge(private_mutation)) == original_id

    visible_mutation = copy.deepcopy(episode)
    visible_mutation["test"][0]["input"][0][0] = (
        visible_mutation["test"][0]["input"][0][0] + 1
    ) % 10
    assert public_challenge_id(proto.public_challenge(visible_mutation)) != original_id


def test_writer_retains_racket_verified_private_evidence_and_opaque_public_files(tmp_path):
    proto = _load_prototype()
    out_dir = tmp_path / "evidence"
    public_dir = tmp_path / "examples"
    manifest = proto.write_evidence(
        seeds=[0, 1],
        out_dir=out_dir,
        public_dir=public_dir,
        root=ROOT,
        difficulty="medium",
        start_index=0,
        n_train=3,
        n_test=4,
    )

    assert manifest["status"] == "verified"
    assert manifest["settings_covered"] == ["left-right", "top-bottom"]
    assert manifest["episode_count"] == 2
    assert manifest["demo_count_per_episode"] == 3
    assert manifest["query_count_per_episode"] == 4
    assert manifest["racket_evaluations"] >= 28

    public_files = sorted(public_dir.glob("challenge_*.json"))
    private_files = sorted((out_dir / "private" / "episodes").glob("episode_*.json"))
    assert len(public_files) == len(private_files) == 2
    assert all(re.fullmatch(r"challenge_[0-9a-f]{64}\.json", path.name) for path in public_files)
    assert all("left" not in path.name and "top" not in path.name and "seed" not in path.name
               for path in public_files)

    ids = []
    for path in public_files:
        challenge = json.loads(path.read_text())
        expected = public_challenge_bytes(challenge)
        assert path.read_bytes() == expected
        ids.append(public_challenge_id(challenge))
        assert path.stem == f"challenge_{ids[-1]}"
    assert ids == sorted(ids)
    assert len(set(ids)) == 2

    settings = set()
    for path in private_files:
        episode = json.loads(path.read_text())
        settings.add(episode["meta"]["parameters"]["symmetry_axis"])
        assert episode["racket_verification"]["selected_matches_python"] is True
        assert episode["racket_verification"]["rival_matches_python"] is True
        assert episode["parameter_rival"]["status"] == "refuted_by_demonstrations"
        assert len(episode["test"]) == 4
    assert settings == {"left-right", "top-bottom"}
