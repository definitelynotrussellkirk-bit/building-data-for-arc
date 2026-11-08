"""Tests for the task-local palette-direction parametric family."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PROTOTYPE = _load("fe0_palette_direction_prototype", PARAMETRIC / "prototype.py")
ADAPTER = _load("fe0_palette_direction_adapter", PARAMETRIC / "adapter.py")


def _input_hashes(episode):
    return [
        hashlib.sha256(
            json.dumps(pair["input"], sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        for split in ("train", "test")
        for pair in episode[split]
    ]


def test_default_program_is_exact_canonical_and_alternate_is_distinct():
    canonical = PROTOTYPE.canonical_program_from_ledger()
    assert PROTOTYPE.program_for("outer_to_inner") == canonical
    assert ADAPTER.program({"palette_direction": "outer_to_inner"}) == canonical
    alternate = PROTOTYPE.program_for("inner_to_outer")
    assert alternate != canonical
    assert "reverse" in alternate
    assert ADAPTER.program({"palette_direction": "inner_to_outer"}) == alternate


@pytest.mark.parametrize("demos", [2, 3, 4, 5, 6])
@pytest.mark.parametrize("direction", PROTOTYPE.PALETTE_DIRECTIONS)
def test_supported_demo_counts_have_four_distinct_queries(demos, direction):
    episode = PROTOTYPE.generate_episode(
        47, palette_direction=direction, demos=demos, queries=4
    )
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == 4
    hashes = _input_hashes(episode)
    assert len(hashes) == len(set(hashes)) == demos + 4
    assert episode["program_solution"] == PROTOTYPE.program_for(direction)
    assert episode["settings"] == {"palette_direction": direction}
    PROTOTYPE.validate_episode(episode)


@pytest.mark.parametrize(
    "kwargs, error",
    [
        ({"demos": 1, "queries": 4}, ValueError),
        ({"demos": 7, "queries": 4}, ValueError),
        ({"demos": 3, "queries": 3}, ValueError),
        ({"demos": 3, "queries": 5}, ValueError),
        ({"demos": True, "queries": 4}, TypeError),
        ({"demos": 3, "queries": False}, TypeError),
    ],
)
def test_count_contract_rejects_unsupported_requests(kwargs, error):
    with pytest.raises(error):
        PROTOTYPE.generate_episode(1, palette_direction="outer_to_inner", **kwargs)


@pytest.mark.parametrize("bad", [None, 1, True, "forward", "OUTER_TO_INNER"])
def test_setting_contract_is_exact(bad):
    with pytest.raises((TypeError, ValueError)):
        ADAPTER.program({"palette_direction": bad})
    with pytest.raises((TypeError, ValueError)):
        PROTOTYPE.generate_episode(0, palette_direction=bad, demos=3, queries=4)


def test_paired_settings_share_inputs_but_change_labels():
    forward = PROTOTYPE.generate_episode(
        991, palette_direction="outer_to_inner", demos=3, queries=4
    )
    reverse = PROTOTYPE.generate_episode(
        991, palette_direction="inner_to_outer", demos=3, queries=4
    )
    assert [p["input"] for p in forward["train"] + forward["test"]] == [
        p["input"] for p in reverse["train"] + reverse["test"]
    ]
    assert any(
        a["output"] != b["output"]
        for a, b in zip(
            forward["train"] + forward["test"],
            reverse["train"] + reverse["test"],
        )
    )


@pytest.mark.parametrize("direction", PROTOTYPE.PALETTE_DIRECTIONS)
def test_two_demonstrations_refute_all_declared_shortcuts(direction):
    episode = PROTOTYPE.generate_episode(
        17, palette_direction=direction, demos=2, queries=4
    )
    audit = PROTOTYPE.audit_episode(episode)
    assert audit["selected"] == direction
    assert audit["surviving_rivals"] == []
    assert all(report["status"] == "identified" for report in audit["queries"])
    facts = [PROTOTYPE.scene_facts(pair["input"]) for pair in episode["train"]]
    assert any(fact["max_depth"] >= 3 for fact in facts)
    assert any(fact["warped_qualifying_components"] >= 1 for fact in facts)
    assert any(fact["malformed_components"] >= 1 for fact in facts)
    assert any(fact["palette_exhaustion_cells"] >= 1 for fact in facts)


def test_query_set_contains_substantive_30x30_case_and_size_generalization():
    episode = PROTOTYPE.generate_episode(
        1234, palette_direction="outer_to_inner", demos=3, queries=4
    )
    demo_max = max(max(len(p["input"]), len(p["input"][0])) for p in episode["train"])
    query_facts = [PROTOTYPE.scene_facts(pair["input"]) for pair in episode["test"]]
    large = [fact for fact in query_facts if fact["shape"] == [30, 30]]
    assert len(large) == 1
    assert large[0]["color8_cells"] >= 120
    assert large[0]["qualifying_components"] >= 4
    assert large[0]["nonzero_body_bbox"][0] <= 1
    assert large[0]["nonzero_body_bbox"][2] >= 28
    assert max(max(f["shape"]) for f in query_facts) > demo_max


def test_public_sequential_turns_hide_private_data_and_preserve_first_turn_bytes():
    episode = PROTOTYPE.generate_episode(
        83, palette_direction="inner_to_outer", demos=3, queries=4
    )
    turns = PROTOTYPE.public_turn_payloads(episode)
    assert len(turns) == 4
    assert turns[0] == PROTOTYPE.public_single_query_payload(episode)
    assert PROTOTYPE.public_bytes(turns[0]) == PROTOTYPE.public_bytes(
        PROTOTYPE.public_single_query_payload(episode)
    )
    for index, turn in enumerate(turns):
        assert set(turn) == {"train", "test"}
        assert len(turn["test"]) == 1
        assert turn["test"][0] == {"input": episode["test"][index]["input"]}
        serialized = json.dumps(turn, sort_keys=True)
        assert "palette_direction" not in serialized
        assert "program_solution" not in serialized
        assert "query_count" not in serialized
        assert episode["test"][index]["output"] not in turn["test"][0].values()


def test_adapter_returns_only_native_required_episode_fields_with_private_labels():
    settings = {"palette_direction": "outer_to_inner"}
    result = ADAPTER.generate(5, copy.deepcopy(settings), 3, 4)
    assert result["program_solution"] == ADAPTER.program(settings)
    assert len(result["train"]) == 3
    assert len(result["test"]) == 4
    assert all(set(pair) >= {"input", "output"} for pair in result["train"] + result["test"])


def test_evidence_builder_sweeps_all_counts_and_settings(tmp_path):
    builder = _load(
        "fe0_palette_direction_evidence_builder",
        PARAMETRIC / "build_evidence.py",
    )
    report = builder.build_report([0, 17])
    assert report["schema"] == "nested-palette-parametric-evidence-v1"
    assert report["episode_count"] == 20
    assert report["ambiguous_episode_count"] == 0
    assert report["settings"] == list(PROTOTYPE.PALETTE_DIRECTIONS)
    assert report["demo_counts"] == [2, 3, 4, 5, 6]
    assert report["query_count"] == 4
    assert report["substantive_30x30_episode_count"] == 20
    assert len(report["first_public_turn_sha256"]) == 20

    paths = builder.write_evidence(tmp_path, [0, 17])
    assert sorted(path.name for path in paths) == [
        "first-public-turns.json",
        "self-audit.json",
        "summary.json",
    ]
    assert json.loads((tmp_path / "summary.json").read_text()) == report
    public = json.loads((tmp_path / "first-public-turns.json").read_text())
    assert all("payload" not in record for record in public["records"])
    assert (tmp_path / "first-public-turns.json").stat().st_size < 100_000
