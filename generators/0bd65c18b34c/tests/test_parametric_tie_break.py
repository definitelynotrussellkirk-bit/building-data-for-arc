"""Focused tests for the proposed nearest-square tie-break prototype."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import re

import pytest
from arc_repl.racket_bridge import RacketBridge
from reviewer_support import (
    canonical_path,
    find_root,
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)


TASK_ID = "0bd65c18b34c"
ROOT = find_root(__file__)
TASK_HOME = ROOT / "generators" / TASK_ID
PROTOTYPE_PATH = TASK_HOME / "workspace" / "parametric" / "prototype.py"

WITNESS_INPUT = [[0] * 13 for _ in range(10)]
for top, left in ((3, 1), (3, 8)):
    for row in (top, top + 1):
        for col in (left, left + 1):
            WITNESS_INPUT[row][col] = 2
WITNESS_INPUT[3][5] = 1
FIRST_EXPECTED = [row[:] for row in WITNESS_INPUT]
FIRST_EXPECTED[3][5] = 0
FIRST_EXPECTED[3][3] = 1
LAST_EXPECTED = [row[:] for row in WITNESS_INPUT]
LAST_EXPECTED[3][5] = 0
LAST_EXPECTED[3][7] = 1


def _load_prototype():
    assert PROTOTYPE_PATH.is_file(), f"missing prototype: {PROTOTYPE_PATH}"
    spec = importlib.util.spec_from_file_location(
        "parametric_0bd65c18b34c",
        PROTOTYPE_PATH,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    matches = []
    with canonical_path(ROOT).open(encoding="utf-8") as source:
        for line in source:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                matches.append(row["program_solution"])
    assert matches
    assert len(set(matches)) == 1
    return matches[0]


@pytest.fixture(scope="module")
def proto():
    return _load_prototype()


@pytest.fixture(scope="module")
def bridge():
    runtime = RacketBridge(max_calls_before_restart=128)
    try:
        yield runtime
    finally:
        runtime.shutdown()


def test_declares_bounded_episode_level_parameter(proto):
    assert proto.PARAMETERS == {
        "tie_break": {
            "allowed": ("first", "last"),
            "default": "first",
            "selected_once_per_episode": True,
        }
    }
    assert proto.DEFAULT_DEMONSTRATIONS == 3
    assert proto.DEFAULT_QUERIES == 4


def test_first_is_exact_canonical_and_last_changes_only_equal_distance_update(proto):
    canonical = _canonical_program()
    first = proto.racket_source("first")
    last = proto.racket_source("last")
    assert first == canonical
    assert last != canonical
    assert canonical.count("(if (< d (first best))") == 1
    assert last == canonical.replace(
        "(if (< d (first best))",
        "(if (<= d (first best))",
        1,
    )


@pytest.mark.parametrize("bad", [None, True, 0, "", "FIRST", "rightmost"])
def test_parameter_is_strictly_bounded(proto, bad):
    with pytest.raises(ValueError, match="tie_break"):
        proto.racket_source(bad)
    with pytest.raises(ValueError, match="tie_break"):
        proto.apply_python(WITNESS_INPUT, bad)
    with pytest.raises(ValueError, match="tie_break"):
        proto.build_episode(0, tie_break=bad)


def test_literal_witness_executes_in_python_and_racket(proto, bridge):
    assert proto.apply_python(WITNESS_INPUT, "first") == FIRST_EXPECTED
    assert proto.apply_python(WITNESS_INPUT, "last") == LAST_EXPECTED
    assert proto.apply_racket(
        WITNESS_INPUT,
        "first",
        bridge=bridge,
    ) == FIRST_EXPECTED
    assert proto.apply_racket(
        WITNESS_INPUT,
        "last",
        bridge=bridge,
    ) == LAST_EXPECTED


def test_parameter_is_drawn_once_deterministically_and_both_values_are_reachable(proto):
    assert proto.parameters(91) == proto.parameters(91)
    assert {
        proto.parameters(seed)["tie_break"]
        for seed in range(32)
    } == {"first", "last"}


@pytest.mark.parametrize("setting", ["first", "last"])
def test_complete_episode_is_racket_labeled_distinct_and_identifiable(
    proto,
    bridge,
    setting,
):
    selected, _source, _digest = load_selected_generator(TASK_ID, root=ROOT)
    episode = proto.build_episode(
        314159,
        tie_break=setting,
        n_train=3,
        n_test=4,
        bridge=bridge,
    )
    rival = "last" if setting == "first" else "first"
    assert episode["parameter_draw_count"] == 1
    assert episode["parameters"] == {"tie_break": setting}
    assert episode["counts"] == {"demonstrations": 3, "queries": 4}
    assert len(episode["train"]) == 3
    assert len(episode["test"]) == 4
    assert len(episode["sample_indices"]) == 7
    assert len(set(episode["sample_indices"])) == 7

    pairs = [*episode["train"], *episode["test"]]
    visible_inputs = {
        json.dumps(pair["input"], separators=(",", ":"))
        for pair in pairs
    }
    assert len(visible_inputs) == 7
    for pair in pairs:
        assert selected.self_check(pair["input"]) == []
        assert pair["output"] == proto.apply_python(pair["input"], setting)
        assert pair["output"] == proto.apply_racket(
            pair["input"],
            setting,
            bridge=bridge,
        )
        assert pair["output"] != proto.apply_racket(
            pair["input"],
            rival,
            bridge=bridge,
        )
    assert proto.parameter_rival_findings(episode, bridge=bridge) == []


def test_public_projection_masks_private_semantics_and_query_answers(proto, bridge):
    episode = proto.build_episode(7, tie_break="last", bridge=bridge)
    public = proto.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert len(public["train"]) == 3
    assert len(public["test"]) == 4
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    encoded = json.dumps(public, sort_keys=True)
    for forbidden in (
        "tie_break",
        "parameters",
        "program",
        "sample_indices",
        "seed",
        "query_outputs",
    ):
        assert forbidden not in encoded
    assert public_challenge_id(episode) == hashlib.sha256(
        public_challenge_bytes(episode)
    ).hexdigest()


def test_evidence_writer_materializes_two_opaque_public_challenges(proto, bridge, tmp_path):
    out = tmp_path / "evidence.json"
    public_dir = tmp_path / "public"
    report = proto.build_evidence(
        out=out,
        public_dir=public_dir,
        episode_seeds=proto.covering_episode_seeds(),
        n_train=3,
        n_test=4,
        bridge=bridge,
    )
    assert out.is_file()
    assert report["status"] == "proposed"
    assert report["checks"]["all_passed"] is True
    assert {episode["parameters"]["tie_break"] for episode in report["private_episodes"]} == {
        "first",
        "last",
    }
    assert len(report["public_files"]) == 2
    for record in report["public_files"]:
        path = Path(record["path"])
        assert re.fullmatch(r"[0-9a-f]{64}\.json", path.name)
        assert path.name == f"{record['public_id']}.json"
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record["public_id"]
        public = json.loads(path.read_text(encoding="utf-8"))
        assert len(public["train"]) == 3
        assert len(public["test"]) == 4
        assert all("output" not in pair for pair in public["test"])
        assert "tie_break" not in path.read_text(encoding="utf-8")


def test_demo_and_query_counts_are_independent_and_validated(proto, bridge):
    episode = proto.build_episode(
        5,
        tie_break="first",
        n_train=2,
        n_test=4,
        bridge=bridge,
    )
    assert episode["counts"] == {"demonstrations": 2, "queries": 4}
    with pytest.raises(ValueError, match="n_train"):
        proto.build_episode(5, n_train=0, n_test=4, bridge=bridge)
    with pytest.raises(ValueError, match="n_test"):
        proto.build_episode(5, n_train=3, n_test=0, bridge=bridge)
