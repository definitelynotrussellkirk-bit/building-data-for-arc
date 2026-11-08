"""Canonical and parametric authoring tests for public parent 38007db0."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import shutil
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]


def load(name):
    path = HOME / "workspace/parametric" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"_p380_{name}", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def official_pairs():
    from reviewer_support import find_root

    root = find_root(__file__)
    challenge = json.loads(
        (root / "shared/data/raw/arc-agi_evaluation_challenges.json").read_text()
    )["38007db0"]
    solutions = json.loads(
        (root / "shared/data/raw/arc-agi_evaluation_solutions.json").read_text()
    )["38007db0"]
    return challenge["train"] + [
        {"input": pair["input"], "output": solutions[index]}
        for index, pair in enumerate(challenge["test"])
    ]


def test_reference_and_python_match_all_four_official_labels():
    family = load("family")
    assert (HOME / "reference.rkt").is_file()
    assert (HOME / "workspace/parametric/canonical.rkt").read_bytes() == (
        HOME / "reference.rkt"
    ).read_bytes()
    for pair in official_pairs():
        assert family.solve(pair["input"], "source_rows") == pair["output"]


def test_reference_matches_all_four_official_labels_in_protected_racket():
    from arcpuzzles.parametric_worker import _real_evaluator
    from reviewer_support import find_root

    apply, identity, bridge = _real_evaluator(find_root(__file__) / "shared/runtime")
    try:
        assert identity["backend"] == "racket" and identity["protected"]
        source = (HOME / "reference.rkt").read_text()
        for pair in official_pairs():
            assert apply(source, pair["input"]) == pair["output"]
    finally:
        bridge.close()


@pytest.mark.parametrize("seed", [0, 17, 43])
def test_parametric_counts_matched_inputs_and_stress(seed):
    adapter = load("adapter")
    for demos in (2, 3, 6):
        episodes = [
            adapter.generate(seed, {"stack_order": setting}, demos, 4)
            for setting in ("source_rows", "difference_desc")
        ]
        inputs = [
            [pair["input"] for pair in e["train"] + e["private_query_bank"]]
            for e in episodes
        ]
        assert inputs[0] == inputs[1]
        for episode in episodes:
            assert len(episode["train"]) == demos
            assert len(episode["test"]) == len(episode["private_query_bank"]) == 4
            assert len({json.dumps(g) for g in inputs[0]}) == demos + 4
            assert any(
                len(pair["input"]) == len(pair["input"][0]) == 30
                for pair in episode["private_query_bank"]
            )
            assert not adapter.family.harmful_survivors(episode, episode["settings"]["stack_order"])
        assert any(
            a["output"] != b["output"]
            for a, b in zip(episodes[0]["train"], episodes[1]["train"])
        )
        short = adapter.generate(seed, {"stack_order": "difference_desc"}, demos, 1)
        assert short["test"] == episodes[1]["test"][:1]
        assert short["private_query_bank"] == episodes[1]["private_query_bank"]


def test_public_views_hide_private_bank_and_vary_first_query():
    adapter = load("adapter")
    episode = adapter.generate(17, {"stack_order": "difference_desc"}, 2, 4)
    assert {adapter.presentation_order(seed)[0] for seed in range(64)} == {0, 1, 2, 3}
    for index in range(4):
        view = adapter.public_view(episode, index)
        poisoned = copy.deepcopy(episode)
        poisoned.update(seed="secret", settings={"secret": True}, program_solution="secret")
        for j, pair in enumerate(poisoned["private_query_bank"]):
            pair["output"] = [[9]]
            if j != index:
                pair["input"] = [[8]]
        assert adapter.public_view(poisoned, index) == view
        assert set(view) == {"train", "test"}
        assert len(view["test"]) == 1 and set(view["test"][0]) == {"input"}


def test_generated_racket_parity_and_causal_counterfactual():
    from arcpuzzles.parametric_worker import _real_evaluator
    from reviewer_support import find_root

    adapter = load("adapter")
    apply, _, bridge = _real_evaluator(find_root(__file__) / "shared/runtime")
    try:
        for setting in ("source_rows", "difference_desc"):
            episode = adapter.generate(17, {"stack_order": setting}, 2, 4)
            for pair in episode["train"] + episode["test"]:
                assert apply(episode["program_solution"], pair["input"]) == pair["output"]
        episode = adapter.generate(17, adapter.causal_settings(), 2, 4)
        pair = episode["test"][-1]
        assert apply(adapter.counterfactual_program(), pair["input"]) != pair["output"]
        intermediate = adapter.causal_intermediate(pair["input"])
        assert intermediate["rows"] and len({r["difference_count"] for r in intermediate["rows"]}) > 1
        assert set(adapter.CAUSAL_DESCRIPTIONS) == {
            "step_a",
            "intermediate",
            "step_b",
            "why_b_depends_on_a",
        }
    finally:
        bridge.close()


def test_strict_settings_counts_and_canonical_program():
    adapter = load("adapter")
    assert adapter.program({"stack_order": "source_rows"}) == (HOME / "reference.rkt").read_text()
    for settings in ({}, None, {"stack_order": "bad"}, {"stack_order": True}, {"stack_order": "source_rows", "x": 1}):
        with pytest.raises(ValueError):
            adapter.program(settings)
    for field, bad in (("seed", True), ("demos", 1), ("demos", 7), ("queries", 0), ("queries", 5)):
        args = dict(seed=0, settings={"stack_order": "source_rows"}, demos=2, queries=4)
        args[field] = bad
        with pytest.raises(ValueError):
            adapter.generate(**args)


def test_canonical_generator_is_self_contained_when_relocated(tmp_path):
    path = tmp_path / "generator.py"
    shutil.copy2(HOME / "generator.py", path)
    spec = importlib.util.spec_from_file_location("_relocated_380", path)
    generator = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(generator)
    assert generator.RULE_TASK_ID == "ee_38007db0"
    for index in range(8):
        grid = generator.generate(17, index)
        assert not generator.self_check(grid)
        assert generator.rule_mirror(grid) == load("family").solve(grid, "source_rows")


def test_reusable_audit_tool_smoke(tmp_path):
    audit = load("audit_native")
    report = audit.run_audit(tmp_path / "audit", seeds=[0], racket_seeds=[])
    assert report["status"] == "passed" and not report["findings"]
    assert report["episodes"] == 6 and report["public_turns"] == 8


def test_minimum_difference_lesson_rejects_unique_column_sort_seed_one():
    adapter = load("adapter")
    family = adapter.family
    episode = adapter.generate(1, {"stack_order": "difference_desc"}, 2, 4)
    assert "unique_column_asc" not in family.harmful_survivors(episode, "difference_desc")


def test_minimum_difference_lesson_rejects_foreground_ascending_seed_seven():
    adapter = load("adapter")
    family = adapter.family
    episode = adapter.generate(7, {"stack_order": "difference_desc"}, 2, 4)
    assert "foreground_asc" not in family.harmful_survivors(episode, "difference_desc")
