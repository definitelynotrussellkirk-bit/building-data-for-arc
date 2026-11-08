"""Contract tests for the proposed episode-level contact-mode family."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

try:
    from reviewer_support import find_root, public_challenge_bytes
except ModuleNotFoundError:
    import sys
    for ancestor in Path(__file__).resolve().parents:
        runtime = ancestor / "shared" / "runtime"
        if (runtime / "reviewer_support.py").is_file():
            sys.path.insert(0, str(runtime))
            break
    from reviewer_support import find_root, public_challenge_bytes

TASK_ID = "7f2dafa2bee4"
ROOT = find_root(__file__)
HOME = Path(__file__).resolve().parents[1]
PROTOTYPE = HOME / "workspace/parametric/prototype.py"
ADAPTER = HOME / "workspace/parametric/adapter.py"
PROMOTION = HOME / "workspace/parametric/promotion.json"


def _load(path: Path, name: str):
    assert path.is_file(), f"missing {path.relative_to(HOME)}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    ledger = ROOT / "shared/data/canonical/puzzles.jsonl"
    for line in ledger.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row["program_solution"]
    raise AssertionError("canonical program not found")


def _norm(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()


def test_declares_bounded_contact_mode_parameter_and_canonical_default():
    proto = _load(PROTOTYPE, "contact_mode_proto")
    assert proto.PARAMETERS == {"contact_mode": ("cardinal", "eight_neighbor")}
    assert proto.DEFAULT_SETTINGS == {"contact_mode": "cardinal"}
    assert _norm(proto.program({"contact_mode": "cardinal"})) == _norm(_canonical_program())
    assert _norm(proto.program({"contact_mode": "cardinal"})) != _norm(
        proto.program({"contact_mode": "eight_neighbor"})
    )
    assert {proto.choose_settings(seed)["contact_mode"] for seed in range(8)} == {
        "cardinal",
        "eight_neighbor",
    }
    promotion = json.loads(PROMOTION.read_text(encoding="utf-8"))
    assert promotion["limits"] == {"demos": [2, 6], "queries": [1, 4]}


@pytest.mark.parametrize("mode", ["cardinal", "eight_neighbor"])
def test_four_query_episode_is_distinct_identifiable_and_large(mode):
    proto = _load(PROTOTYPE, f"contact_mode_proto_{mode}")
    settings = {"contact_mode": mode}
    episode = proto.generate_episode(20261024, settings=settings, demos=3, queries=4)
    assert len(episode["train"]) == 3
    assert len(episode["test"]) == 4
    assert episode["settings"] == settings
    assert episode["program_solution"] == proto.program(settings)
    assert proto.episode_errors(episode) == []

    inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
    frozen = {json.dumps(grid, separators=(",", ":")) for grid in inputs}
    assert len(frozen) == 7
    assert any(len(pair["input"]) == 30 and len(pair["input"][0]) == 30 for pair in episode["test"])

    rival = "eight_neighbor" if mode == "cardinal" else "cardinal"
    assert all(
        proto.apply_python(pair["input"], mode) == pair["output"]
        for pair in episode["train"] + episode["test"]
    )
    assert all(
        proto.apply_python(pair["input"], rival) != pair["output"]
        for pair in episode["train"]
    )


@pytest.mark.parametrize("demos", [2, 3, 4, 5, 6])
def test_demo_count_is_independent_and_still_teaches(demos):
    proto = _load(PROTOTYPE, f"contact_mode_proto_d{demos}")
    episode = proto.generate_episode(
        17,
        settings={"contact_mode": "eight_neighbor"},
        demos=demos,
        queries=4,
    )
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == 4
    assert proto.episode_errors(episode) == []


def test_first_query_and_first_turn_are_identical_for_one_or_four_queries():
    proto = _load(PROTOTYPE, "contact_mode_proto_projection")
    settings = {"contact_mode": "cardinal"}
    one = proto.generate_episode(91, settings=settings, demos=3, queries=1)
    four = proto.generate_episode(91, settings=settings, demos=3, queries=4)
    assert one["test"][0] == four["test"][0]
    assert proto.public_turn(one, 0) == proto.public_turn(four, 0)

    public = proto.public_turn(four, 0)
    assert set(public) == {"train", "test"}
    assert len(public["test"]) == 1
    assert set(public["test"][0]) == {"input"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    visible = public_challenge_bytes(public)
    assert b"contact_mode" not in visible
    assert b"program" not in visible


def test_public_identifier_hashes_only_visible_turn_bytes():
    proto = _load(PROTOTYPE, "contact_mode_proto_public_id")
    episode = proto.generate_episode(31337, settings={"contact_mode": "cardinal"}, demos=3, queries=4)
    visible = proto.public_turn(episode, 0)
    expected = hashlib.sha256(public_challenge_bytes(visible)).hexdigest()
    assert proto.public_id(episode, 0) == expected

    private_changes = copy.deepcopy(episode)
    private_changes["settings"] = {"contact_mode": "eight_neighbor"}
    private_changes["program_solution"] = "secret replacement"
    private_changes["test"][0]["output"][0][0] = 9
    assert proto.public_id(private_changes, 0) == expected

    visible_change = copy.deepcopy(episode)
    visible_change["test"][0]["input"][0][0] = 9
    assert proto.public_id(visible_change, 0) != expected


def test_adapter_matches_prototype_contract():
    proto = _load(PROTOTYPE, "contact_mode_proto_adapter_expected")
    adapter = _load(ADAPTER, "contact_mode_adapter")
    settings = {"contact_mode": "cardinal"}
    assert adapter.program(settings) == proto.program(settings)
    assert adapter.generate(123, settings, 2, 4) == proto.generate_episode(
        123, settings=settings, demos=2, queries=4
    )
