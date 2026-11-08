from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, find_root, public_challenge_bytes

TASK_ID = "1856980929fe"
ROOT = find_root(__file__)
PROTOTYPE_PATH = ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"
EXPECTED_CANONICAL_SHA256 = "d57dfba75662273fbbd5aced174f3a28831099169574954cffd383ff42478ccf"


def _load_prototype():
    assert PROTOTYPE_PATH.is_file(), "fan-stride prototype must be runnable"
    spec = importlib.util.spec_from_file_location(
        f"parametric_fan_stride_{TASK_ID}", PROTOTYPE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def prototype():
    return _load_prototype()


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge(timeout=30) as instance:
        yield instance


def test_default_rule_is_exact_canonical_and_stride_two_is_guarded_change(prototype):
    canonical = prototype.canonical_source(root=ROOT)
    assert hashlib.sha256(canonical.encode()).hexdigest() == EXPECTED_CANONICAL_SHA256
    assert prototype.CANONICAL_SHA256 == EXPECTED_CANONICAL_SHA256
    assert prototype.DEFAULT_FAN_STRIDE == 1
    assert prototype.FAN_STRIDES == (1, 2)
    assert prototype.materialize_rule(1, source=canonical) == canonical

    stride_two = prototype.materialize_rule(2, source=canonical)
    assert stride_two != canonical
    assert stride_two.count(prototype.STRIDE_TWO_TERM) == 2
    assert prototype.restore_canonical(stride_two) == canonical


@pytest.mark.parametrize("bad", [None, True, False, 0, 3, 1.0, "1"])
def test_materialize_rule_rejects_undeclared_settings(prototype, bad):
    with pytest.raises((TypeError, ValueError), match="fan_stride"):
        prototype.materialize_rule(bad, root=ROOT)


def test_exact_default_racket_replays_every_canonical_label(prototype, bridge):
    canonical = prototype.materialize_rule(1, root=ROOT)
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert pairs
    for pair in pairs:
        assert prototype.execute_rule(canonical, pair["input"], bridge=bridge) == pair[
            "output"
        ]


def test_stride_two_racket_changes_a_lawful_canonical_input(prototype, bridge):
    pair = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)[0]
    canonical = prototype.materialize_rule(1, root=ROOT)
    stride_two = prototype.materialize_rule(2, root=ROOT)
    assert prototype.execute_rule(canonical, pair["input"], bridge=bridge) == pair["output"]
    assert prototype.execute_rule(stride_two, pair["input"], bridge=bridge) != pair[
        "output"
    ]


@pytest.mark.parametrize("bad", [True, False, -1, 1.0, "1", None])
def test_episode_seed_requires_a_nonnegative_plain_integer(prototype, bad):
    with pytest.raises((TypeError, ValueError), match="seed"):
        prototype.choose_setting(bad)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"demo_count": 0},
        {"demo_count": True},
        {"query_count": 0},
        {"query_count": 1.5},
    ],
)
def test_episode_counts_require_positive_plain_integers(prototype, bridge, kwargs):
    with pytest.raises((TypeError, ValueError), match="count"):
        prototype.make_episode(0, root=ROOT, bridge=bridge, **kwargs)


def test_two_seeds_cover_fixed_setting_three_demo_four_query_episodes(prototype, bridge):
    episodes = [
        prototype.make_episode(seed, root=ROOT, bridge=bridge)
        for seed in (0, 1)
    ]
    assert {episode["parameters"]["fan_stride"] for episode in episodes} == set(
        prototype.FAN_STRIDES
    )
    for episode in episodes:
        selected = episode["parameters"]["fan_stride"]
        assert episode["status"] == "proposed_unapproved"
        assert episode["approved"] is False
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 4
        assert len(episode["pairs"]) == 7
        assert {pair["fan_stride"] for pair in episode["pairs"]} == {selected}
        assert [pair["sampling"]["n_seeds"] for pair in episode["train"]] == [3, 2, 1]

        inputs = [pair["input_sha256"] for pair in episode["pairs"]]
        assert len(set(inputs)) == 7
        for pair in episode["pairs"]:
            assert set(pair["counterfactual_outputs"]) == {"1", "2"}
            assert pair["counterfactual_outputs"][str(selected)] == pair["output"]
            rival = 2 if selected == 1 else 1
            assert pair["counterfactual_outputs"][str(rival)] != pair["output"]

        analysis = prototype.analyze_episode(episode, root=ROOT, bridge=bridge)
        assert analysis["status"] == "no_ambiguity_found"
        by_stride = {row["fan_stride"]: row for row in analysis["settings"]}
        assert by_stride[selected]["status"] == "matches_episode"
        rival = 2 if selected == 1 else 1
        assert by_stride[rival]["status"] == "refuted_by_demonstrations"
        assert by_stride[rival]["demonstration_mismatch_indices"] == [0, 1, 2]
        assert by_stride[rival]["query_mismatch_indices"] == [0, 1, 2, 3]


def test_public_projection_and_filename_depend_only_on_visible_challenge(
    prototype, bridge
):
    episode = prototype.make_episode(0, root=ROOT, bridge=bridge)
    public = prototype.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert len(public["train"]) == 3
    assert len(public["test"]) == 4
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    serialized = json.dumps(public, sort_keys=True)
    for forbidden in ("fan_stride", "racket", "program", "seed", "counterfactual"):
        assert forbidden not in serialized

    name = prototype.public_filename(episode)
    assert name.startswith("challenge-") and name.endswith(".json")
    changed_private = copy.deepcopy(episode)
    changed_private["seed"] = 999
    changed_private["parameters"] = {"fan_stride": 999}
    changed_private["program_sha256"] = "private-change"
    for pair in changed_private["test"]:
        pair["output"] = [[9]]
    assert prototype.public_filename(changed_private) == name

    changed_visible = copy.deepcopy(episode)
    changed_visible["train"][0]["output"][0][0] = (
        changed_visible["train"][0]["output"][0][0] + 1
    ) % 10
    assert prototype.public_filename(changed_visible) != name


def test_evidence_writer_fails_closed_on_existing_output(prototype, tmp_path):
    out = tmp_path / "already-there"
    out.mkdir()
    with pytest.raises(FileExistsError):
        prototype.write_evidence((0, 1), out=out, root=ROOT)
    assert list(out.iterdir()) == []


def test_evidence_writer_builds_verified_public_private_bundle(prototype, tmp_path):
    out = tmp_path / "evidence"
    report = prototype.write_evidence(
        (1, 0),
        out=out,
        root=ROOT,
        demo_count=3,
        query_count=4,
    )
    assert report["status"] == "proposed_unapproved"
    assert report["approved"] is False
    assert report["parameter"] == {
        "name": "fan_stride",
        "allowed_values": [1, 2],
        "original_default": 1,
        "input_constraints_depend_on_parameter": False,
    }
    assert report["counts"]["episodes"] == 2
    assert report["counts"]["train_pairs"] == 6
    assert report["counts"]["query_pairs"] == 8
    assert report["counts"]["distinct_input_grids"] == 14
    assert report["counts"]["settings_exercised"] == 2
    assert report["counts"]["ambiguous_parameter_rivals"] == 0

    verification = json.loads((out / "verification.json").read_text())
    assert verification["status"] == "pass"
    assert verification["episodes_checked"] == 2
    assert verification["labels_checked"] == 14
    assert verification["rival_predictions_checked"] == 28

    rules = {row["fan_stride"]: row for row in report["rules"]}
    assert set(rules) == set(prototype.FAN_STRIDES)
    for setting, row in rules.items():
        path = out / row["path"]
        assert path.read_text() == prototype.materialize_rule(setting, root=ROOT)
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"]

    public_ids = [row["public_id"] for row in report["episodes"]]
    assert public_ids == sorted(public_ids)
    seen_public_names = set()
    for row in report["episodes"]:
        episode = json.loads((out / row["private_path"]).read_text())
        analysis = json.loads((out / row["analysis_path"]).read_text())
        public_path = out / row["public_path"]
        public = json.loads(public_path.read_text())
        assert analysis["status"] == "no_ambiguity_found"
        assert public == prototype.public_challenge(episode)
        assert public_path.read_bytes() == public_challenge_bytes(public)
        assert public_path.name == prototype.public_filename(episode)
        assert all("output" not in pair for pair in public["test"])
        seen_public_names.add(public_path.name)
    assert len(seen_public_names) == 2

    for row in report["files"]:
        path = out / row["path"]
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"]


def test_public_files_are_physically_emitted_in_visible_id_order(prototype, tmp_path, monkeypatch):
    writes = []
    original = Path.write_bytes
    def record(path, payload):
        if path.parent.name == "public":
            writes.append(path.name)
        return original(path, payload)
    monkeypatch.setattr(Path, "write_bytes", record)
    prototype.write_evidence((0, 1), out=tmp_path / "ordered", root=ROOT, demo_count=1, query_count=1)
    assert len(writes) == 2
    assert writes == sorted(writes)
