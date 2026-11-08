"""Focused tests for the proposed destination-edge rule prototype."""
from __future__ import annotations

import importlib.util
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

import pytest

from reviewer_support import (
    find_root,
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)
from arc_repl.racket_bridge import RacketBridge


TASK_ID = "44d20451ce17"
ROOT = find_root(__file__)
PROTOTYPE_PATH = (
    ROOT
    / "generators"
    / TASK_ID
    / "workspace"
    / "parametric"
    / "prototype.py"
)

WITNESS_INPUT = [
    [5, 0, 0, 0, 0],
    [0, 1, 0, 1, 0],
    [0, 1, 0, 0, 0],
    [0, 5, 0, 5, 0],
    [5, 0, 5, 5, 5],
]
BOTTOM_EXPECTED = [
    [5, 0, 0, 0, 0],
    [0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0],
    [0, 5, 0, 5, 0],
    [5, 1, 5, 1, 5],
]
TOP_EXPECTED = [
    [5, 1, 0, 1, 0],
    [0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0],
    [0, 5, 0, 5, 0],
    [5, 0, 5, 5, 5],
]


@pytest.fixture(scope="module")
def proto():
    assert PROTOTYPE_PATH.is_file(), f"missing prototype: {PROTOTYPE_PATH}"
    spec = importlib.util.spec_from_file_location(
        "task_44d20451ce17_parametric_prototype", PROTOTYPE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def bridge():
    runtime = RacketBridge(max_calls_before_restart=64)
    try:
        yield runtime
    finally:
        runtime.shutdown()


def test_bottom_is_exact_canonical_program_and_both_rules_execute_literal_witness(
    proto, bridge
) -> None:
    canonical = proto.canonical_program(ROOT)
    assert proto.racket_source("bottom") == canonical

    assert proto.apply_python(WITNESS_INPUT, "bottom") == BOTTOM_EXPECTED
    assert proto.apply_python(WITNESS_INPUT, "top") == TOP_EXPECTED
    assert proto.apply_racket(WITNESS_INPUT, "bottom", bridge=bridge) == BOTTOM_EXPECTED
    assert proto.apply_racket(WITNESS_INPUT, "top", bridge=bridge) == TOP_EXPECTED


def test_parameter_is_drawn_once_deterministically_and_invalid_values_fail(proto) -> None:
    assert proto.parameters(0) == {"destination_edge": "top"}
    assert proto.parameters(1) == {"destination_edge": "bottom"}
    assert proto.parameters(0) == proto.parameters(0)
    assert {proto.parameters(seed)["destination_edge"] for seed in range(10)} == {
        "bottom",
        "top",
    }

    with pytest.raises(ValueError, match="destination_edge"):
        proto.racket_source("middle")
    with pytest.raises(ValueError, match="destination_edge"):
        proto.apply_python(WITNESS_INPUT, "middle")


def test_complete_episodes_are_lawful_racket_labeled_and_distinguish_the_rival(
    proto, bridge
) -> None:
    selected, _, _ = load_selected_generator(TASK_ID, root=ROOT)
    episodes = [proto.build_episode(seed, bridge=bridge) for seed in (1, 0)]
    assert {episode["parameters"]["destination_edge"] for episode in episodes} == {
        "bottom",
        "top",
    }

    for episode in episodes:
        assert episode["counts"] == {"demonstrations": 3, "queries": 4}
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 4
        assert len(episode["sample_indices"]) == 7
        assert episode["sample_indices"] == sorted(episode["sample_indices"])
        visible_inputs = [
            json.dumps(pair["input"], separators=(",", ":"))
            for pair in [*episode["train"], *episode["test"]]
        ]
        assert len(set(visible_inputs)) == 7
        assert not proto.parameter_rival_findings(episode, bridge=bridge)
        assert episode["rival"]["status"] == "distinguished"
        assert episode["rival"]["demo_differences"]
        assert episode["rival"]["query_differs"] is True
        assert episode["rival"]["query_differences"] == [0, 1, 2, 3]
        for pair in [*episode["train"], *episode["test"]]:
            assert selected.self_check(pair["input"]) == []
            assert pair["output"] == proto.apply_python(
                pair["input"], episode["parameters"]["destination_edge"]
            )


def test_public_challenge_masks_hidden_rule_and_query_answers(proto, bridge) -> None:
    episode = proto.build_episode(1, bridge=bridge)
    public = proto.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    serialized = json.dumps(public, sort_keys=True)
    for forbidden in ("destination_edge", "parameters", "program", "rival"):
        assert forbidden not in serialized


def test_evidence_materializer_retains_private_provenance_and_masks_public_files(
    proto, bridge, tmp_path: Path
) -> None:
    out = tmp_path / "evidence.json"
    public_dir = tmp_path / "public"
    public_dir.mkdir()
    for legacy_name in ("episode-a.json", "episode-b.json"):
        (public_dir / legacy_name).write_text('{"legacy":true}\n', encoding="utf-8")
    report = proto.build_evidence(out=out, public_dir=public_dir, bridge=bridge)

    assert out.is_file()
    assert report["status"] == "proposed"
    assert report["checks"]["all_passed"] is True
    assert report["parameter"]["default"] == "bottom"
    assert set(report["parameter"]["values"]) == {"bottom", "top"}
    assert len(report["private_episodes"]) == 2
    assert report["replay"]["n_train"] == 3
    assert report["replay"]["n_test"] == 4
    assert report["witness"]["outputs"]["bottom"] == BOTTOM_EXPECTED
    assert report["witness"]["outputs"]["top"] == TOP_EXPECTED

    legacy_files = [
        public_dir / "episode-a.json",
        public_dir / "episode-b.json",
    ]
    assert all(path.read_bytes() == proto.LEGACY_PUBLIC_TOMBSTONE for path in legacy_files)
    public_files = sorted(
        path
        for path in public_dir.glob("*.json")
        if re.fullmatch(r"[0-9a-f]{64}\.json", path.name)
    )
    assert len(public_files) == 2
    assert [record["public_id"] for record in report["public_files"]] == sorted(
        record["public_id"] for record in report["public_files"]
    )
    by_id = {
        public_challenge_id(episode): episode
        for episode in report["private_episodes"]
    }
    for record, path in zip(report["public_files"], public_files, strict=True):
        public_id = record["public_id"]
        assert re.fullmatch(r"[0-9a-f]{64}", public_id)
        assert path.name == f"{public_id}.json"
        assert record["path"] == str(path)
        assert record["sha256"] == public_id
        assert hashlib.sha256(path.read_bytes()).hexdigest() == public_id
        assert path.read_bytes() == public_challenge_bytes(by_id[public_id])
        public = json.loads(path.read_text(encoding="utf-8"))
        assert len(public["test"]) == 4
        assert all("output" not in pair for pair in public["test"])
        text = path.read_text(encoding="utf-8")
        assert "destination_edge" not in text
        assert "program" not in text


def test_public_materializer_rejects_duplicate_visible_payloads(
    proto, bridge, tmp_path: Path
) -> None:
    with pytest.raises(ValueError, match="duplicate public payload"):
        proto.build_evidence(
            out=tmp_path / "evidence.json",
            public_dir=tmp_path / "public",
            bridge=bridge,
            episode_seeds=(1, 1),
        )


def test_cli_exposes_separate_demo_and_query_counts(tmp_path: Path) -> None:
    out = tmp_path / "evidence.json"
    public_dir = tmp_path / "public"
    completed = subprocess.run(
        [
            sys.executable,
            str(PROTOTYPE_PATH),
            "--out",
            str(out),
            "--public-dir",
            str(public_dir),
            "--demos",
            "3",
            "--queries",
            "4",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["replay"]["n_train"] == 3
    assert report["replay"]["n_test"] == 4
    assert all(len(episode["test"]) == 4 for episode in report["private_episodes"])
