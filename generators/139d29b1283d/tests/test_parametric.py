from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

from arcpuzzles import Catalog
from reviewer_support import find_root

TASK = "139d29b1283d"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK / "workspace" / "parametric"


def _load(name: str, filename: str):
    path = HOME / filename
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    record = Catalog(ROOT).get(TASK)
    programs = {
        variant["program_solution"]
        for variant in record["variants"]
        if isinstance(variant.get("program_solution"), str)
    }
    assert len(programs) == 1
    return next(iter(programs))


def _inputs(episode: dict) -> list[list[list[int]]]:
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def test_native_contract_and_exact_canonical_default() -> None:
    family = _load("_p139_contract_family", "prototype.py")
    adapter = _load("_p139_contract_adapter", "adapter.py")
    contract = json.loads((HOME / "promotion.json").read_text(encoding="utf-8"))

    assert contract["schema"] == "arcpuzzles-parametric-adapter-v1"
    assert contract["parameters"] == {
        "finish": ["intersection_only", "overlap_size_payload"]
    }
    assert contract["default"] == {"finish": "intersection_only"}
    assert contract["limits"] == {"demos": [2, 6], "queries": [1, 4]}
    assert contract["qualification_demos"] == 3
    assert adapter.program(contract["default"]) == _canonical_program()
    assert family.program(contract["default"]) == _canonical_program()
    assert family.program({"finish": "overlap_size_payload"}) != _canonical_program()


@pytest.mark.parametrize("finish", ["intersection_only", "overlap_size_payload"])
@pytest.mark.parametrize("demos", [2, 3, 6])
@pytest.mark.parametrize("queries", [1, 4])
def test_generate_supports_counts_real_claims_and_30x30(finish: str, demos: int, queries: int) -> None:
    family = _load(f"_p139_generate_{finish}_{demos}_{queries}", "prototype.py")
    episode = family.generate(1729, {"finish": finish}, demos, queries)
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == queries
    assert episode["program_solution"] == family.program({"finish": finish})
    inputs = _inputs(episode)
    assert len(inputs) == len({json.dumps(grid, separators=(",", ":")) for grid in inputs})
    for pair in episode["train"] + episode["test"]:
        assert pair["output"] == family.transform(pair["input"], {"finish": finish})
        facts = family.analyze(pair["input"])
        assert facts["errors"] == []
        assert facts["template_size"] > facts["visible_overlap_count"] >= 2
        assert facts["payload_sizes"].count(facts["visible_overlap_count"]) == 1
        assert facts["payload_sizes"].count(facts["template_size"]) == 1
    if queries == 4:
        stress = episode["test"][3]["input"]
        assert (len(stress), len(stress[0])) == (30, 30)
        facts = family.analyze(stress)
        assert facts["nonzero_count"] >= 40
        assert facts["boundary_sides"] == ["bottom", "left", "right", "top"]


@pytest.mark.parametrize("seed", [0, 17, 97])
def test_inputs_are_setting_neutral_and_prefix_stable(seed: int) -> None:
    family = _load(f"_p139_prefix_{seed}", "prototype.py")
    default = family.generate(seed, {"finish": "intersection_only"}, 6, 4)
    relay = family.generate(seed, {"finish": "overlap_size_payload"}, 6, 4)
    assert _inputs(default) == _inputs(relay)

    short_demos = family.generate(seed, {"finish": "intersection_only"}, 2, 4)
    short_queries = family.generate(seed, {"finish": "intersection_only"}, 6, 1)
    assert [p["input"] for p in short_demos["train"]] == [
        p["input"] for p in default["train"][:2]
    ]
    assert [p["input"] for p in short_queries["test"]] == [default["test"][0]["input"]]


def test_two_demos_identify_setting_and_reject_declared_shortcuts() -> None:
    family = _load("_p139_certificate", "prototype.py")
    for finish in family.FINISHES:
        episode = family.generate(17, {"finish": finish}, 2, 4)
        certificate = family.lesson_certificate(episode["train"], {"finish": finish})
        assert certificate["surviving_settings"] == [{"finish": finish}]
        assert certificate["surviving_shortcuts"] == []
        assert certificate["query_outputs_consulted"] is False


def test_overlap_count_is_a_real_relay_intermediate() -> None:
    family = _load("_p139_dependency", "prototype.py")
    episode = family.generate(0, {"finish": "overlap_size_payload"}, 2, 4)
    grid = episode["train"][0]["input"]
    facts = family.analyze(grid)
    intermediate = family.overlap_intermediate(grid)
    assert intermediate["visible_overlap_count"] == facts["visible_overlap_count"]
    assert intermediate["visible_overlap_count"] != facts["template_size"]
    assert len(intermediate["selected_payload"]) == intermediate["visible_overlap_count"]
    assert family.transform(grid, {"finish": "overlap_size_payload"}) != family.transform(
        grid, {"finish": "intersection_only"}
    )
    assert family.counterfactual_transform(grid) != family.transform(
        grid, {"finish": "overlap_size_payload"}
    )


def test_invalid_adapter_requests_reject_loudly() -> None:
    family = _load("_p139_invalid", "prototype.py")
    with pytest.raises(ValueError, match="settings"):
        family.program({})
    with pytest.raises(ValueError, match="finish"):
        family.program({"finish": "bogus"})
    with pytest.raises(ValueError, match="seed"):
        family.generate(True, {"finish": "intersection_only"}, 3, 4)
    with pytest.raises(ValueError, match="demos"):
        family.generate(0, {"finish": "intersection_only"}, 1, 4)
    with pytest.raises(ValueError, match="queries"):
        family.generate(0, {"finish": "intersection_only"}, 3, 5)


def test_programs_and_counterfactual_execute_in_protected_racket() -> None:
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    family = _load("_p139_racket", "prototype.py")
    grid = family.generate(0, {"finish": "overlap_size_payload"}, 2, 4)["train"][0]["input"]
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    cases = {
        "canonical": (
            family.program({"finish": "intersection_only"}),
            family.transform(grid, {"finish": "intersection_only"}),
        ),
        "relay": (
            family.program({"finish": "overlap_size_payload"}),
            family.transform(grid, {"finish": "overlap_size_payload"}),
        ),
        "counterfactual": (family.counterfactual_program(), family.counterfactual_transform(grid)),
    }
    with RacketBridge(timeout=30, max_calls_before_restart=16) as bridge:
        assert bridge.runtime_identity["backend"] == "racket"
        assert bridge.runtime_identity["protected"] is True
        for name, (program, expected) in cases.items():
            actual = bridge.eval_text(f"({wrap_rule(program)} {literal})")
            assert actual == expected, name
