from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import (
    canonical_pairs,
    find_root,
    public_challenge_bytes,
    public_challenge_id,
)


TASK_ID = "761a24339019"
ROOT = find_root(__file__)
TASK_ROOT = ROOT / "generators" / TASK_ID
PARAMETRIC_ROOT = TASK_ROOT / "workspace" / "parametric"
PROTOTYPE_PATH = PARAMETRIC_ROOT / "prototype.py"
ADAPTER_PATH = PARAMETRIC_ROOT / "adapter.py"
PROMOTION_PATH = PARAMETRIC_ROOT / "promotion.json"
SETTINGS = (
    {"stamp_transform": "identity"},
    {"stamp_transform": "rotate_cw"},
)


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(name, None)
    return module


@pytest.fixture(scope="module")
def prototype():
    return _load(PROTOTYPE_PATH, "_review_761a24339019_parametric_prototype")


@pytest.fixture(scope="module")
def racket_bridge():
    with RacketBridge(max_calls_before_restart=64) as bridge:
        yield bridge


def _all_pairs(episode):
    return list(episode["train"]) + list(episode["test"])


def _input_hashes(prototype, episode):
    return [prototype.grid_sha256(pair["input"]) for pair in _all_pairs(episode)]


def test_default_is_exact_canonical_and_guarded_rotation_executes(
    prototype, racket_bridge
):
    canonical = prototype.canonical_source(root=ROOT)
    assert hashlib.sha256(canonical.encode("utf-8")).hexdigest() == prototype.CANONICAL_SOURCE_SHA256
    assert prototype.materialize_rule(None, root=ROOT) == canonical
    assert prototype.materialize_rule(SETTINGS[0], root=ROOT) == canonical
    rotated = prototype.materialize_rule(SETTINGS[1], root=ROOT)
    assert rotated != canonical
    assert prototype.recognize_rule(canonical, root=ROOT) == SETTINGS[0]
    assert prototype.recognize_rule(rotated, root=ROOT) == SETTINGS[1]

    for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True):
        assert prototype.execute_rule(canonical, pair["input"], bridge=racket_bridge, root=ROOT) == pair["output"]
        assert prototype.independent_output(pair["input"], SETTINGS[0]) == pair["output"]

    witness = prototype.episode_inputs(0, demos=2, queries=1, root=ROOT)[0]
    identity_output = prototype.execute_rule(canonical, witness, bridge=racket_bridge, root=ROOT)
    rotated_output = prototype.execute_rule(rotated, witness, bridge=racket_bridge, root=ROOT)
    assert identity_output == prototype.independent_output(witness, SETTINGS[0])
    assert rotated_output == prototype.independent_output(witness, SETTINGS[1])
    assert identity_output != rotated_output


@pytest.mark.parametrize(
    "bad",
    [
        True,
        "identity",
        {},
        {"stamp_transform": "bad"},
        {"stamp_transform": 1},
        {"stamp_transform": "identity", "extra": "x"},
    ],
)
def test_settings_are_strict(prototype, bad):
    with pytest.raises(ValueError):
        prototype.normalize_settings(bad)


def test_inputs_are_setting_independent_distinct_large_and_content_spread(prototype):
    first = prototype.episode_inputs(17, demos=3, queries=4, root=ROOT)
    replay = prototype.episode_inputs(17, demos=3, queries=4, root=ROOT)
    one_query = prototype.episode_inputs(17, demos=3, queries=1, root=ROOT)
    assert first == replay
    assert first[:3] == one_query[:3]
    assert first[3] == one_query[3]
    assert len(first) == 7
    assert len({prototype.grid_sha256(grid) for grid in first}) == 7

    certificates = [prototype.input_certificate(grid) for grid in first]
    assert all(row["complete_for_all_settings"] for row in certificates)
    assert all(row["setting_outputs_distinct"] for row in certificates)
    assert all(row["boundary_contact"] for row in certificates)
    assert all(row["target_row_span"] >= max(1, row["height"] // 3) for row in certificates)
    assert all(row["target_col_span"] >= max(1, row["width"] // 3) for row in certificates)

    first_query = certificates[3]
    assert (first_query["height"], first_query["width"]) == (30, 30)
    assert first_query["distractor_cells"] >= 24
    assert first_query["content_bbox_height"] >= 24
    assert first_query["content_bbox_width"] >= 24
    assert sum(max(row["height"], row["width"]) > 20 for row in certificates[3:]) >= 3


def test_fixed_setting_episodes_are_racket_labeled_and_demo_identifiable(
    prototype, racket_bridge
):
    assert prototype.parameter_for_seed(0) == SETTINGS[0]
    assert prototype.parameter_for_seed(1) == SETTINGS[1]
    for seed, selected in enumerate(SETTINGS):
        episode = prototype.generate_episode(
            seed,
            settings=selected,
            demos=3,
            queries=4,
            bridge=racket_bridge,
            root=ROOT,
        )
        assert episode["settings"] == selected
        assert episode["demo_count"] == 3
        assert episode["query_count"] == 4
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 4
        assert len(set(_input_hashes(prototype, episode))) == 7
        assert episode["surviving_settings_from_demonstrations"] == [selected]
        assert episode["program_solution"] == prototype.materialize_rule(selected, root=ROOT)
        for pair in _all_pairs(episode):
            assert pair["output"] == prototype.independent_output(pair["input"], selected)
        assert all(report["query_answer_used_for_demo_fit"] is False for report in episode["query_identification"])
        assert all(report["eliminated_rivals_that_disagree"] == [SETTINGS[1 - seed]] for report in episode["query_identification"])


def test_forced_settings_share_identical_inputs(prototype, racket_bridge):
    identity = prototype.generate_episode(
        29,
        settings=SETTINGS[0],
        demos=2,
        queries=4,
        bridge=racket_bridge,
        root=ROOT,
    )
    rotated = prototype.generate_episode(
        29,
        settings=SETTINGS[1],
        demos=2,
        queries=4,
        bridge=racket_bridge,
        root=ROOT,
    )
    assert _input_hashes(prototype, identity) == _input_hashes(prototype, rotated)
    assert any(a["output"] != b["output"] for a, b in zip(_all_pairs(identity), _all_pairs(rotated)))


@pytest.mark.parametrize("demos", [2, 6])
@pytest.mark.parametrize("queries", [1, 4, 8])
def test_supported_count_boundaries_are_independent(prototype, demos, queries):
    grids = prototype.episode_inputs(41, demos=demos, queries=queries, root=ROOT)
    assert len(grids) == demos + queries
    assert len({prototype.grid_sha256(grid) for grid in grids}) == len(grids)


@pytest.mark.parametrize("bad_seed", [True, -1, 2**63, 1.5, "1"])
def test_seed_validation_is_strict(prototype, bad_seed):
    with pytest.raises(ValueError):
        prototype.parameter_for_seed(bad_seed)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("demos", 1),
        ("demos", 7),
        ("demos", True),
        ("queries", 0),
        ("queries", 9),
        ("queries", 2.0),
    ],
)
def test_count_validation_is_strict(prototype, field, value):
    kwargs = {"demos": 3, "queries": 4, field: value}
    with pytest.raises(ValueError):
        prototype.episode_inputs(0, root=ROOT, **kwargs)


def test_public_projection_and_sequential_first_turn_hide_private_state(
    prototype, racket_bridge
):
    four = prototype.generate_episode(
        9,
        settings=SETTINGS[1],
        demos=3,
        queries=4,
        bridge=racket_bridge,
        root=ROOT,
    )
    one = prototype.generate_episode(
        9,
        settings=SETTINGS[1],
        demos=3,
        queries=1,
        bridge=racket_bridge,
        root=ROOT,
    )
    first_turn = prototype.sequential_public_turn(four, 0)
    assert prototype.sequential_turn_bytes(four, 0) == public_challenge_bytes(prototype.public_payload(one))
    assert first_turn == prototype.public_payload(one)
    assert set(first_turn) == {"train", "test"}
    assert len(first_turn["test"]) == 1
    assert set(first_turn["test"][0]) == {"input"}

    public = prototype.public_payload(four)
    raw = public_challenge_bytes(public)
    text = raw.decode("utf-8")
    assert public_challenge_id(public) == hashlib.sha256(raw).hexdigest()
    for forbidden in (
        '"seed"',
        '"settings"',
        '"program_solution"',
        '"query_answers"',
        "identity",
        "rotate_cw",
        "1 of 4",
        "query_count",
    ):
        assert forbidden not in text

    private_only = copy.deepcopy(four)
    private_only["seed"] = 999
    private_only["settings"] = SETTINGS[0]
    private_only["program_solution"] = "different"
    private_only["test"][0]["output"] = [[9]]
    assert public_challenge_id(prototype.public_payload(private_only)) == public_challenge_id(public)


def test_evidence_writer_is_hash_named_private_transactional_and_verifiable(
    prototype, racket_bridge, tmp_path
):
    out = tmp_path / "evidence"
    manifest = prototype.write_evidence(
        out,
        seeds=(0, 1),
        demos=3,
        queries=4,
        bridge=racket_bridge,
        root=ROOT,
    )
    assert manifest["schema"] == "761a24339019-stamp-transform-evidence-v1"
    assert manifest["status"] == "proposed_unapproved"
    assert manifest["approved"] is False
    assert manifest["canonical_default_unchanged"] is True
    assert manifest["counts"] == {
        "episodes": 2,
        "train_pairs": 6,
        "query_pairs": 8,
        "distinct_input_grids": 14,
        "settings_exercised": 2,
    }
    assert {row["settings"]["stamp_transform"] for row in manifest["episodes"]} == {"identity", "rotate_cw"}

    public_paths = sorted((out / "public").glob("challenge-*.json"))
    private_paths = sorted((out / "private" / "episodes").glob("*.json"))
    rule_paths = sorted((out / "private" / "rules").glob("*.rkt"))
    assert len(public_paths) == len(private_paths) == len(rule_paths) == 2
    for path in public_paths:
        assert re.fullmatch(r"challenge-[0-9a-f]{64}\.json", path.name)
        public = json.loads(path.read_text(encoding="utf-8"))
        assert path.read_bytes() == public_challenge_bytes(public)
        assert path.name == f"challenge-{public_challenge_id(public)}.json"
        assert all(set(pair) == {"input"} for pair in public["test"])
        assert "stamp_transform" not in path.read_text(encoding="utf-8")
    for path in private_paths:
        private = json.loads(path.read_text(encoding="utf-8"))
        assert len(private["query_answers"]) == 4
        assert private["query_answers"] == [pair["output"] for pair in private["test"]]
        assert prototype.public_payload(private) == json.loads((out / private["public_path"]).read_text())
    for row in manifest["files"]:
        payload = (out / row["path"]).read_bytes()
        assert len(payload) == row["bytes"]
        assert hashlib.sha256(payload).hexdigest() == row["sha256"]
    assert json.loads((out / "manifest.json").read_text()) == manifest
    with pytest.raises(FileExistsError):
        prototype.write_evidence(out, seeds=(0,), bridge=racket_bridge, root=ROOT)


def test_evidence_writer_rejects_duplicate_visible_batch_and_cleans_up(
    prototype, racket_bridge, monkeypatch, tmp_path
):
    base = prototype.generate_episode(
        0,
        settings=SETTINGS[0],
        demos=2,
        queries=1,
        bridge=racket_bridge,
        root=ROOT,
    )

    def duplicate_episode(seed, **kwargs):
        del kwargs
        episode = copy.deepcopy(base)
        episode["seed"] = seed
        episode["settings"] = prototype.parameter_for_seed(seed)
        return episode

    monkeypatch.setattr(prototype, "generate_episode", duplicate_episode)
    out = tmp_path / "duplicate"
    with pytest.raises(ValueError, match="same visible public challenge"):
        prototype.write_evidence(
            out,
            seeds=(0, 1),
            demos=2,
            queries=1,
            bridge=racket_bridge,
            root=ROOT,
        )
    assert not out.exists()


def test_promotion_adapter_and_contract(prototype, racket_bridge):
    assert ADAPTER_PATH.is_file()
    assert PROMOTION_PATH.is_file()
    adapter = _load(ADAPTER_PATH, "_review_761a24339019_parametric_adapter")
    promotion = json.loads(PROMOTION_PATH.read_text(encoding="utf-8"))
    assert promotion == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "status": "proposed_unapproved",
        "approved": False,
        "adapter": "generators/761a24339019/workspace/parametric/adapter.py",
        "parameters": {"stamp_transform": ["identity", "rotate_cw"]},
        "default": {"stamp_transform": "identity"},
        "limits": {"demos": [2, 6], "queries": [1, 8]},
    }
    assert adapter.program(SETTINGS[0]) == prototype.canonical_source(root=ROOT)
    episode = adapter.generate(
        3,
        SETTINGS[1],
        2,
        4,
        bridge=racket_bridge,
        root=ROOT,
    )
    assert episode["settings"] == SETTINGS[1]
    assert len(episode["train"]) == 2
    assert len(episode["test"]) == 4
