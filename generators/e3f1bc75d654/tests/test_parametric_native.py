"""Native parametric contract tests for e3f1bc75d654.

The alternate rule must have a real input-dependent composition: discover the
pattern's bounding box, then use that result to select a receiver frame before
stamping the normalized crop.
"""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from reviewer_support import canonical_path, find_root


ROOT = find_root(__file__)
HOME = ROOT / "generators/e3f1bc75d654/workspace/parametric"


def _load(name: str, filename: str):
    path = HOME / filename
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    programs = []
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == "e3f1bc75d654":
            programs.append(row["program_solution"])
    assert len(set(programs)) == 1
    return programs[0]


def _inputs(episode):
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def test_native_contract_and_default_program_are_exact():
    family = _load("_e3f1_native_family_contract", "prototype.py")
    adapter = _load("_e3f1_native_adapter_contract", "adapter.py")
    contract = json.loads((HOME / "promotion.json").read_text(encoding="utf-8"))

    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/e3f1bc75d654/workspace/parametric/adapter.py",
        "parameters": {
            "target_basis": ["template_interior", "pattern_bbox"],
        },
        "default": {"target_basis": "template_interior"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "resources": [
            "generators/e3f1bc75d654/workspace/parametric/canonical.rkt",
            "generators/e3f1bc75d654/workspace/parametric/pattern-bbox.rkt",
        ],
    }
    assert family.DEFAULT_SETTINGS == {"target_basis": "template_interior"}
    assert adapter.program(family.DEFAULT_SETTINGS) == _canonical_program()
    assert adapter.program({"target_basis": "pattern_bbox"}) != _canonical_program()


@pytest.mark.parametrize("setting", ["template_interior", "pattern_bbox"])
@pytest.mark.parametrize("demos", [2, 3, 6])
@pytest.mark.parametrize("queries", [1, 4])
def test_generate_supports_independent_counts_and_real_claims(setting, demos, queries):
    family = _load(f"_e3f1_native_family_{setting}_{demos}_{queries}", "prototype.py")
    episode = family.generate(
        1729,
        {"target_basis": setting},
        demos=demos,
        queries=queries,
    )
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == queries
    assert episode["program_solution"] == family.program({"target_basis": setting})
    inputs = _inputs(episode)
    assert len(inputs) == len({json.dumps(grid, separators=(",", ":")) for grid in inputs})
    for pair in [*episode["train"], *episode["test"]]:
        assert pair["output"] == family.transform(pair["input"], {"target_basis": setting})
        assert family.analyze_scene(pair["input"])["errors"] == []
    if queries == 4:
        stress = episode["test"][3]["input"]
        assert (len(stress), len(stress[0])) == (30, 30)


@pytest.mark.parametrize("seed", [0, 17, 2718])
def test_sampling_is_setting_neutral_and_prefix_stable(seed):
    family = _load(f"_e3f1_native_family_sampling_{seed}", "prototype.py")
    canonical = family.generate(seed, {"target_basis": "template_interior"}, 6, 4)
    alternate = family.generate(seed, {"target_basis": "pattern_bbox"}, 6, 4)
    assert _inputs(canonical) == _inputs(alternate)

    short_demos = family.generate(seed, {"target_basis": "pattern_bbox"}, 2, 4)
    short_queries = family.generate(seed, {"target_basis": "pattern_bbox"}, 6, 1)
    assert [p["input"] for p in short_demos["train"]] == [
        p["input"] for p in alternate["train"][:2]
    ]
    assert [p["input"] for p in short_queries["test"]] == [alternate["test"][0]["input"]]


def test_pattern_bbox_is_a_real_input_dependent_selector():
    family = _load("_e3f1_native_family_dependency", "prototype.py")
    episode = family.generate(0, {"target_basis": "pattern_bbox"}, 2, 4)
    grid = episode["train"][0]["input"]
    facts = family.analyze_scene(grid)
    intermediate = family.pattern_bbox_intermediate(grid)

    assert intermediate["crop_shape"] != facts["template"]["interior"]
    assert len(intermediate["target_frames"]) == 1
    assert any(
        frame["interior"] == tuple(reversed(intermediate["crop_shape"]))
        for frame in facts["frames"]
    )

    alternate = family.transform(grid, {"target_basis": "pattern_bbox"})
    canonical = family.transform(grid, {"target_basis": "template_interior"})
    target_color = intermediate["target_frames"][0]["color"]
    alternate_colors = {value for row in alternate for value in row if value}
    canonical_colors = {value for row in canonical for value in row if value}
    assert alternate_colors == {target_color}
    assert canonical_colors == {frame["color"] for frame in facts["matching"]}
    assert alternate != canonical


def test_two_demonstrations_eliminate_declared_settings_and_shortcuts():
    family = _load("_e3f1_native_family_certificate", "prototype.py")
    for setting in family.TARGET_BASES:
        episode = family.generate(17, {"target_basis": setting}, 2, 4)
        certificate = family.lesson_certificate(
            episode["train"], [pair["input"] for pair in episode["test"]]
        )
        assert certificate["surviving_settings"] == [{"target_basis": setting}]
        assert certificate["surviving_shortcuts"] == []
        assert certificate["query_outputs_consulted"] is False
        assert all(certificate["query_disagreements"].values())


def test_sequential_public_projection_hides_all_private_fields():
    family = _load("_e3f1_native_family_public", "prototype.py")
    episode = family.generate(91, {"target_basis": "pattern_bbox"}, 3, 4)
    private = {
        **copy.deepcopy(episode),
        "settings": {"target_basis": "pattern_bbox"},
        "seed": 91,
        "private_note": "secret",
    }
    turns = family.sequential_public_turns(private)
    assert len(turns) == 4
    assert all(len(turn["challenge"]["test"]) == 1 for turn in turns)
    assert turns[0]["challenge"] == family.public_challenge(
        {**private, "test": [private["test"][0]]}
    )

    changed = copy.deepcopy(private)
    changed["settings"] = {"target_basis": "template_interior"}
    changed["program_solution"] = "private replacement"
    changed["private_note"] = "changed"
    for pair in changed["test"]:
        pair["output"] = [[9 for _ in row] for row in pair["output"]]
    assert family.sequential_public_turns(changed) == turns
    assert all(set(turn) == {"turn", "challenge_id", "challenge"} for turn in turns)


def test_stress_scene_has_edge_and_quadrant_coverage():
    family = _load("_e3f1_native_family_stress", "prototype.py")
    grid = family.generate(8, {"target_basis": "pattern_bbox"}, 2, 4)["test"][3]["input"]
    facts = family.analyze_scene(grid)
    assert facts["errors"] == []
    boxes = [frame["bbox"] for frame in facts["frames"]]
    assert any(r0 == 0 for r0, _c0, _r1, _c1 in boxes)
    assert any(r1 == 29 for _r0, _c0, r1, _c1 in boxes)
    assert any(c0 == 0 for _r0, c0, _r1, _c1 in boxes)
    assert any(c1 == 29 for _r0, _c0, _r1, c1 in boxes)
    occupied = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    assert all(
        any((r < 15) == top and (c < 15) == left for r, c in occupied)
        for top in (False, True)
        for left in (False, True)
    )


def test_invalid_adapter_requests_reject_loudly():
    family = _load("_e3f1_native_family_invalid", "prototype.py")
    with pytest.raises(ValueError, match="settings"):
        family.program({})
    with pytest.raises(ValueError, match="target_basis"):
        family.program({"target_basis": "bogus"})
    with pytest.raises(ValueError, match="seed"):
        family.generate(True, family.DEFAULT_SETTINGS, 3, 4)
    with pytest.raises(ValueError, match="demos"):
        family.generate(0, family.DEFAULT_SETTINGS, 1, 4)
    with pytest.raises(ValueError, match="queries"):
        family.generate(0, family.DEFAULT_SETTINGS, 3, 5)


def test_wrong_intermediate_counterfactual_is_source_guarded():
    family = _load("_e3f1_native_family_counterfactual", "prototype.py")
    correct = family.program({"target_basis": "pattern_bbox"})
    wrong = family.counterfactual_program("template_extent")
    assert wrong != correct
    assert "target-h t-ih" in wrong
    assert "target-w t-iw" in wrong


def test_materialized_rules_and_rivals_execute_against_real_racket():
    """Catch malformed or semantically divergent source, not just Python mirrors."""
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    family = _load("_e3f1_native_family_racket", "prototype.py")
    episode = family.generate(0, {"target_basis": "pattern_bbox"}, 2, 4)
    grid = episode["train"][0]["input"]
    literal = "'(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in grid
    ) + ")"

    programs = {
        "setting:template_interior": (
            family.program({"target_basis": "template_interior"}),
            family.transform(grid, {"target_basis": "template_interior"}),
        ),
        "setting:pattern_bbox": (
            family.program({"target_basis": "pattern_bbox"}),
            family.transform(grid, {"target_basis": "pattern_bbox"}),
        ),
        **{
            f"shortcut:{name}": (source, family.shortcut_output(grid, name))
            for name, source in family.rival_programs().items()
        },
    }
    with RacketBridge(timeout=30, max_calls_before_restart=32) as bridge:
        for name, (source, expected) in programs.items():
            actual = bridge.eval_text(f"({wrap_rule(source)} {literal})")
            assert actual == expected, name


def test_reusable_audit_checks_lessons_exports_and_stress_without_query_labels(tmp_path):
    audit = _load("_e3f1_native_audit_contract", "audit.py")
    report = audit.build_report(
        seeds=(0, 17),
        demo_counts=(2, 3, 6),
        stress_seeds=3,
        include_racket=False,
        public_dir=tmp_path / "public",
    )
    assert report["status"] == "passed"
    assert report["summary"]["lesson_cases"] == 12
    assert report["summary"]["stress_episodes"] == 18
    assert report["summary"]["query_outputs_consulted"] is False
    assert report["summary"]["all_shortcuts_rejected"] is True
    assert report["summary"]["all_inputs_setting_independent"] is True
    assert report["summary"]["all_public_projections_private_invariant"] is True
    assert len(list((tmp_path / "public").glob("*.json"))) == 2
