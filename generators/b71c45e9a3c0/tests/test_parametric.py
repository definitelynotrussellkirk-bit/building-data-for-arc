from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from arcpuzzles import Catalog
from reviewer_support import find_root

TASK = "b71c45e9a3c0"
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
    family = _load("_pb71_contract_family", "prototype.py")
    adapter = _load("_pb71_contract_adapter", "adapter.py")
    contract = json.loads((HOME / "promotion.json").read_text(encoding="utf-8"))

    assert contract["schema"] == "arcpuzzles-parametric-adapter-v1"
    assert contract["parameters"] == {
        "scope": ["all_objects", "largest_key_size"]
    }
    assert contract["default"] == {"scope": "all_objects"}
    assert contract["limits"] == {"demos": [2, 6], "queries": [1, 4]}
    assert contract["qualification_demos"] == 3
    assert adapter.program(contract["default"]) == _canonical_program()
    assert family.program(contract["default"]) == _canonical_program()
    assert family.program({"scope": "largest_key_size"}) != _canonical_program()


@pytest.mark.parametrize("scope", ["all_objects", "largest_key_size"])
@pytest.mark.parametrize("demos", [2, 3, 6])
@pytest.mark.parametrize("queries", [1, 4])
def test_generate_supports_counts_real_claims_and_30x30(scope: str, demos: int, queries: int) -> None:
    family = _load(f"_pb71_generate_{scope}_{demos}_{queries}", "prototype.py")
    episode = family.generate(1729, {"scope": scope}, demos, queries)
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == queries
    assert episode["program_solution"] == family.program({"scope": scope})
    inputs = _inputs(episode)
    assert len(inputs) == len({json.dumps(grid, separators=(",", ":")) for grid in inputs})
    for pair in episode["train"] + episode["test"]:
        assert pair["output"] == family.transform(pair["input"], {"scope": scope})
        facts = family.analyze(pair["input"])
        assert facts["errors"] == []
        assert facts["largest_size"] > facts["largest_key"] >= 4
        assert facts["component_sizes"].count(facts["largest_key"]) == 1
        assert facts["empty_bbox_corner_count"] >= 2
        assert facts["largest_is_first"] is False
    if queries == 4:
        stress = episode["test"][3]["input"]
        assert (len(stress), len(stress[0])) == (30, 30)
        facts = family.analyze(stress)
        assert facts["nonzero_count"] >= 45
        assert facts["boundary_sides"] == ["bottom", "left", "right", "top"]
        assert len(facts["component_sizes"]) == 6


@pytest.mark.parametrize("seed", [0, 17, 97])
def test_inputs_are_setting_neutral_and_prefix_stable(seed: int) -> None:
    family = _load(f"_pb71_prefix_{seed}", "prototype.py")
    canonical = family.generate(seed, {"scope": "all_objects"}, 6, 4)
    relay = family.generate(seed, {"scope": "largest_key_size"}, 6, 4)
    assert _inputs(canonical) == _inputs(relay)

    short_demos = family.generate(seed, {"scope": "all_objects"}, 2, 4)
    short_queries = family.generate(seed, {"scope": "all_objects"}, 6, 1)
    assert [p["input"] for p in short_demos["train"]] == [
        p["input"] for p in canonical["train"][:2]
    ]
    assert [p["input"] for p in short_queries["test"]] == [canonical["test"][0]["input"]]


def test_two_demos_identify_setting_and_reject_declared_shortcuts() -> None:
    family = _load("_pb71_certificate", "prototype.py")
    for scope in family.SCOPES:
        episode = family.generate(17, {"scope": scope}, 2, 4)
        certificate = family.lesson_certificate(episode["train"], {"scope": scope})
        assert certificate["surviving_settings"] == [{"scope": scope}]
        assert certificate["surviving_shortcuts"] == []
        assert certificate["query_outputs_consulted"] is False


def test_largest_key_is_a_real_size_selector_intermediate() -> None:
    family = _load("_pb71_dependency", "prototype.py")
    episode = family.generate(0, {"scope": "largest_key_size"}, 2, 4)
    grid = episode["train"][0]["input"]
    facts = family.analyze(grid)
    intermediate = family.relay_intermediate(grid)
    assert intermediate["target_size"] == facts["largest_key"]
    assert intermediate["target_size"] != facts["largest_size"]
    assert len(intermediate["selected_components"]) == 1
    assert len(intermediate["selected_components"][0]) == intermediate["target_size"]
    assert family.transform(grid, {"scope": "largest_key_size"}) != family.transform(
        grid, {"scope": "all_objects"}
    )
    assert family.counterfactual_transform(grid) != family.transform(
        grid, {"scope": "largest_key_size"}
    )


def test_invalid_adapter_requests_reject_loudly() -> None:
    family = _load("_pb71_invalid", "prototype.py")
    with pytest.raises(ValueError, match="settings"):
        family.program({})
    with pytest.raises(ValueError, match="scope"):
        family.program({"scope": "bogus"})
    with pytest.raises(ValueError, match="seed"):
        family.generate(True, {"scope": "all_objects"}, 3, 4)
    with pytest.raises(ValueError, match="demos"):
        family.generate(0, {"scope": "all_objects"}, 1, 4)
    with pytest.raises(ValueError, match="queries"):
        family.generate(0, {"scope": "all_objects"}, 3, 5)


def test_programs_and_counterfactual_execute_in_protected_racket() -> None:
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    family = _load("_pb71_racket", "prototype.py")
    grid = family.generate(0, {"scope": "largest_key_size"}, 2, 4)["train"][0]["input"]
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    cases = {
        "canonical": (
            family.program({"scope": "all_objects"}),
            family.transform(grid, {"scope": "all_objects"}),
        ),
        "relay": (
            family.program({"scope": "largest_key_size"}),
            family.transform(grid, {"scope": "largest_key_size"}),
        ),
        "counterfactual": (family.counterfactual_program(), family.counterfactual_transform(grid)),
    }
    with RacketBridge(timeout=30, max_calls_before_restart=16) as bridge:
        assert bridge.runtime_identity["backend"] == "racket"
        assert bridge.runtime_identity["protected"] is True
        for name, (program, expected) in cases.items():
            actual = bridge.eval_text(f"({wrap_rule(program)} {literal})")
            assert actual == expected, name


def test_bounded_audit_without_racket_covers_all_declared_jobs() -> None:
    audit = _load("_pb71_audit", "audit.py")
    family = _load("_pb71_audit_family", "prototype.py")
    report = audit.build_report(seeds=(0,), demos=(2,), include_racket=False)
    assert report["status"] == "passed"
    assert report["summary"]["jobs"] == len(family.SCOPES)
    assert report["summary"]["settings"] == [
        {"scope": value} for value in family.SCOPES
    ]
    assert report["summary"]["declared_shortcuts"] == sorted(family.SHORTCUTS)
    assert report["summary"]["all_inputs_setting_neutral"] is True
    assert report["summary"]["all_declared_shortcuts_rejected"] is True
    assert report["summary"]["racket_evaluations"] == 0
