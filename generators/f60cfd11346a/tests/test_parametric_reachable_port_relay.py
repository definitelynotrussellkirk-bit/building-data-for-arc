"""Focused contract, teaching, and causal checks for the native parametric family."""
from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"
CANONICAL_PROGRAM = """(rule!
  (let* ((seed (first (find-color g 2)))
         (region (connected-region g (first seed) (second seed) (lambda (r c v) (or (= v 0) (= v 2))) 4))
         (zeros (filter (lambda (p) (= (at g (first p) (second p)) 0)) region)))
    (paint-cells g zeros 8)))"""


def _load(name: str, path: Path):
    spec = spec_from_file_location(name, path)
    assert spec and spec.loader
    module = module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _prototype():
    return _load("f60cfd11346a_parametric_prototype_test", PARAMETRIC / "prototype.py")


def _adapter():
    return _load("f60cfd11346a_parametric_adapter_test", PARAMETRIC / "adapter.py")


def test_adapter_preserves_exact_canonical_program_and_validates_settings():
    prototype = _prototype()
    adapter = _adapter()

    assert adapter.program({"mode": "canonical"}) == CANONICAL_PROGRAM
    assert adapter.program({"mode": "reachable_port_relay"}) == prototype.RELAY_PROGRAM

    for invalid in (
        None,
        {},
        {"mode": "unknown"},
        {"mode": "canonical", "extra": 1},
        {"mode": True},
    ):
        with pytest.raises((TypeError, ValueError)):
            adapter.program(invalid)


def test_episode_counts_are_independent_prefix_stable_and_inputs_match_settings():
    prototype = _prototype()
    for seed in (0, 17, 991):
        short = prototype.generate_episode(seed, mode="reachable_port_relay", demos=2, queries=1)
        long = prototype.generate_episode(seed, mode="reachable_port_relay", demos=6, queries=4)
        canonical = prototype.generate_episode(seed, mode="canonical", demos=6, queries=4)

        assert short["train"] == long["train"][:2]
        assert short["test"] == long["test"][:1]
        assert [pair["input"] for pair in canonical["train"]] == [
            pair["input"] for pair in long["train"]
        ]
        assert [pair["input"] for pair in canonical["test"]] == [
            pair["input"] for pair in long["test"]
        ]
        all_inputs = [pair["input"] for pair in long["train"] + long["test"]]
        assert len({json.dumps(grid) for grid in all_inputs}) == len(all_inputs)


def test_generated_scenes_exercise_reachability_counts_boundaries_and_python_labels():
    prototype = _prototype()
    seen_counts = set()
    for seed in (0, 17, 991):
        for mode in prototype.MODES:
            episode = prototype.generate_episode(seed, mode=mode, demos=6, queries=4)
            for pair in episode["train"] + episode["test"]:
                grid = pair["input"]
                analysis = prototype.analyze_scene(grid)
                seen_counts.add(analysis["active_port_count"])
                assert len(analysis["anchors"]) == 3
                assert 1 <= analysis["active_port_count"] <= 3
                assert analysis["selected_anchor"] == analysis["anchors"][
                    analysis["active_port_count"] - 1
                ]
                assert pair["output"] == prototype.apply_mode(grid, mode)
                assert all(type(cell) is int and 0 <= cell <= 9 for row in grid for cell in row)
                assert 10 <= len(grid) <= 30
                assert 16 <= len(grid[0]) <= 30

            stress = episode["test"][3]["input"]
            assert (len(stress), len(stress[0])) == (30, 30)
            nonzero = [(r, c) for r, row in enumerate(stress) for c, value in enumerate(row) if value]
            assert len(nonzero) >= 180
            assert {0, 29} <= {r for r, _ in nonzero}
            assert {0, 29} <= {c for _, c in nonzero}

    assert seen_counts == {1, 2, 3}


def test_two_demonstrations_refute_declared_shortcuts_for_every_setting():
    prototype = _prototype()
    report = prototype.audit_python(seeds=range(12), demo_counts=(2, 3, 6))

    assert report["episodes"] == 72
    assert report["ambiguities"] == []
    assert report["distinct_inputs"] == report["pairs"]
    assert report["stress_30x30"] == 72
    assert {
        "canonical_only",
        "fixed_target_1",
        "fixed_target_2",
        "fixed_target_3",
        "global_port_count",
        "reverse_port_count",
        "source_area_modulo",
    } <= set(report["rivals"])


def test_wrong_global_port_intermediate_changes_the_selected_remote_chamber():
    prototype = _prototype()
    episode = prototype.generate_episode(0, mode="reachable_port_relay", demos=3, queries=4)
    witness = next(
        pair for pair in episode["test"]
        if prototype.analyze_scene(pair["input"])["active_port_count"] != 3
    )
    analysis = prototype.analyze_scene(witness["input"])

    assert len(analysis["all_ports"]) == 3
    assert analysis["active_port_count"] in {1, 2}
    assert prototype.apply_mode(witness["input"], "reachable_port_relay") == witness["output"]
    assert prototype.apply_global_port_count_rival(witness["input"]) != witness["output"]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"seed": True, "mode": "canonical", "demos": 3, "queries": 4},
        {"seed": -1, "mode": "canonical", "demos": 3, "queries": 4},
        {"seed": 0, "mode": "unknown", "demos": 3, "queries": 4},
        {"seed": 0, "mode": "canonical", "demos": 1, "queries": 4},
        {"seed": 0, "mode": "canonical", "demos": 7, "queries": 4},
        {"seed": 0, "mode": "canonical", "demos": 3, "queries": 0},
        {"seed": 0, "mode": "canonical", "demos": 3, "queries": 5},
    ],
)
def test_episode_rejects_out_of_contract_requests(kwargs):
    prototype = _prototype()
    with pytest.raises(ValueError):
        prototype.generate_episode(**kwargs)
