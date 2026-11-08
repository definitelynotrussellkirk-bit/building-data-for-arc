"""Contract tests for the native b5b012cd97d9 parametric family."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys

import pytest

from reviewer_support import (
    canonical_path,
    find_root,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "b5b012cd97d9"
ROOT = find_root(__file__)
PARAMETRIC = ROOT / "generators" / TASK_ID / "workspace" / "parametric"


def _load(name: str, filename: str):
    path = PARAMETRIC / filename
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


family = _load("_test_b5b012cd97d9_family", "family.py")
adapter = _load("_test_b5b012cd97d9_adapter", "adapter.py")


def _canonical_program() -> str:
    programs = set()
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for raw in handle:
            row = json.loads(raw)
            if row.get("task_id") == TASK_ID and isinstance(row.get("program_solution"), str):
                programs.add(row["program_solution"])
    assert len(programs) == 1
    return programs.pop()


def _inputs(episode: dict) -> list[list[list[int]]]:
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def test_default_program_is_byte_exact_canonical_and_contract_is_native():
    canonical = _canonical_program()
    assert family.program({"secondary": "next_repeated"}) == canonical
    assert adapter.program({"secondary": "next_repeated"}) == canonical
    assert (PARAMETRIC / "canonical.rkt").read_text(encoding="utf-8") == canonical

    contract = json.loads((PARAMETRIC / "promotion.json").read_text(encoding="utf-8"))
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"secondary": ["next_repeated", "big_side_relay", "preserve_vertical"]},
        "default": {"secondary": "next_repeated"},
        "limits": {"demos": [3, 6], "queries": [1, 4]},
        "qualification_demos": 3,
        "resources": [
            f"generators/{TASK_ID}/workspace/parametric/family.py",
            f"generators/{TASK_ID}/workspace/parametric/canonical.rkt",
            f"generators/{TASK_ID}/workspace/parametric/big_side_relay.rkt",
            f"generators/{TASK_ID}/workspace/parametric/fixed_four_relay.rkt",
            f"generators/{TASK_ID}/workspace/parametric/union_family.py",
            f"generators/{TASK_ID}/workspace/parametric/branches/incoming/prototype.py",
            f"generators/{TASK_ID}/workspace/parametric/branches/incoming/canonical.rkt",
            f"generators/{TASK_ID}/workspace/parametric/branches/incoming/preserve_vertical.rkt",
        ],
    }


def test_request_validation_is_strict_and_bool_safe():
    good = family.generate(0, {"secondary": "next_repeated"}, 2, 1)
    assert len(good["train"]) == 2 and len(good["test"]) == 1

    bad_settings = (
        None,
        {},
        {"secondary": "unknown"},
        {"secondary": "next_repeated", "extra": 1},
        {"secondary": 1},
    )
    for settings in bad_settings:
        with pytest.raises(ValueError):
            family.generate(0, settings, 2, 1)
    for seed in (-1, True, 2**63):
        with pytest.raises(ValueError):
            family.generate(seed, {"secondary": "next_repeated"}, 2, 1)
    for demos, queries in ((1, 1), (7, 1), (2, 0), (2, 5), (True, 1), (2, True)):
        with pytest.raises(ValueError):
            family.generate(0, {"secondary": "next_repeated"}, demos, queries)


def test_generation_is_deterministic_matched_prefix_stable_and_distinct():
    canonical = family.generate(17, {"secondary": "next_repeated"}, 6, 4)
    relay = family.generate(17, {"secondary": "big_side_relay"}, 6, 4)
    repeat = family.generate(17, {"secondary": "next_repeated"}, 6, 4)
    assert canonical == repeat
    assert _inputs(canonical) == _inputs(relay)
    assert canonical["program_solution"] != relay["program_solution"]
    assert any(a["output"] != b["output"] for a, b in zip(canonical["train"], relay["train"]))
    assert len({json.dumps(grid, separators=(",", ":")) for grid in _inputs(canonical)}) == 10

    short = family.generate(17, {"secondary": "next_repeated"}, 2, 1)
    assert short["train"] == canonical["train"][:2]
    assert short["test"] == canonical["test"][:1]
    mutated = deepcopy(short)
    mutated["train"][0]["input"][0][0] ^= 1
    assert family.generate(17, {"secondary": "next_repeated"}, 2, 1) == short


def test_claims_follow_mass_ranking_and_big_side_relay_relation():
    for seed in (0, 17, 2**31 + 9):
        for setting in family.SECONDARY_SETTINGS:
            episode = family.generate(seed, {"secondary": setting}, 6, 4)
            for pair in episode["train"] + episode["test"]:
                analysis = family.analyze(pair["input"])
                assert analysis["big"]["count"] == analysis["big_side"] ** 2
                assert analysis["relay"]["count"] == analysis["big_side"]
                assert analysis["canonical_secondary"]["count"] > analysis["relay"]["count"]
                expected = family.solve_python(pair["input"], setting)
                assert pair["output"] == expected
                assert 1 <= len(expected) <= 30
                assert 1 <= len(expected[0]) <= 30


def test_two_demonstrations_identify_each_setting_against_finite_rivals():
    for seed in range(32):
        inputs = family.sample_inputs(seed, demos=2, queries=4)
        report = family.teaching_report(inputs[:2])
        assert report["survivors"] == {
            "next_repeated": ["next_repeated"],
            "big_side_relay": ["big_side_relay"],
        }
        assert not report["harmful_survivors"]


def test_four_queries_cover_transfer_boundary_and_substantive_30_by_30():
    episode = family.generate(23, {"secondary": "big_side_relay"}, 3, 4)
    shapes = [(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]]
    assert shapes == [(10, 12), (18, 20), (23, 17), (30, 30)]

    stress = episode["test"][-1]["input"]
    analysis = family.analyze(stress)
    non_background = sum(cell != analysis["background"] for row in stress for cell in row)
    assert non_background >= 400
    assert analysis["role_count"] >= 8
    assert any(cell != analysis["background"] for cell in stress[0])
    assert any(cell != analysis["background"] for cell in stress[-1])
    assert any(row[0] != analysis["background"] for row in stress)
    assert any(row[-1] != analysis["background"] for row in stress)


def test_public_turn_hides_private_state_and_hashes_exact_visible_bytes():
    full = family.generate(91, {"secondary": "big_side_relay"}, 3, 4)
    first_only = family.generate(91, {"secondary": "big_side_relay"}, 3, 1)
    first = family.public_turn(full, 0)
    assert first == family.public_turn(first_only, 0)
    assert set(first) == {"train", "test"}
    assert len(first["test"]) == 1 and set(first["test"][0]) == {"input"}
    raw = public_challenge_bytes(first)
    assert public_challenge_id(first) == hashlib.sha256(raw).hexdigest()
    serialized = raw.decode("utf-8")
    assert "big_side_relay" not in serialized
    assert "program" not in serialized
    for pair in full["test"]:
        assert json.dumps(pair["output"], separators=(",", ":")) not in serialized


def test_sequential_counterfactual_uses_wrong_intermediate_and_changes_output():
    witness = family.sequential_witness_input()
    analysis = family.analyze(witness)
    assert analysis["big_side"] == 9
    assert analysis["relay"]["count"] == 9
    assert any(record["count"] == 4 for record in analysis["secondary_candidates"])
    correct = family.solve_python(witness, "big_side_relay")
    wrong = family.solve_rival(witness, "fixed_four")
    assert correct != wrong
    differing = sum(a != b for ra, rb in zip(correct, wrong) for a, b in zip(ra, rb)) if (
        len(correct) == len(wrong) and len(correct[0]) == len(wrong[0])
    ) else None
    assert differing is None or differing > 0


def test_adapter_is_thin_exact_path_and_returns_fresh_values():
    one = adapter.generate(5, {"secondary": "big_side_relay"}, 3, 4)
    two = adapter.generate(5, {"secondary": "big_side_relay"}, 3, 4)
    assert one == two
    assert one is not two and one["train"] is not two["train"]
    assert adapter.program({"secondary": "big_side_relay"}) == (
        PARAMETRIC / "big_side_relay.rkt"
    ).read_text(encoding="utf-8")
