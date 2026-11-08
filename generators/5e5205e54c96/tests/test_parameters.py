"""Focused native-family tests for 5e5205e54c96."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TASK = "5e5205e54c96"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK / "workspace" / "parametric"
SETTINGS = ({"ring_order": "outer_to_inner"}, {"ring_order": "widest_gap_anchor"})


def _load_adapter():
    path = HOME / "adapter.py"
    assert path.is_file(), "native parametric adapter has not been implemented"
    spec = importlib.util.spec_from_file_location("_arc_5e5205e54c96_adapter_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    programs = set()
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            programs.add(row["program_solution"])
    assert len(programs) == 1
    return programs.pop()


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_existing_generator_accepts_all_canonical_inputs_and_ordinary_draws():
    generator, _, _ = load_selected_generator(TASK, root=ROOT)
    pairs = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    assert len(pairs) == 5
    assert all(generator.self_check(pair["input"]) == [] for pair in pairs)
    for difficulty in (None, "medium"):
        for sample_index in range(6):
            grid = generator.generate(23, sample_index, difficulty=difficulty)
            assert generator.self_check(grid, difficulty=difficulty) == []


def test_ordinary_sampler_covers_color_8_as_a_legend_value():
    generator, _, _ = load_selected_generator(TASK, root=ROOT)
    legends = [
        generator.generate(23, sample_index)[0]
        for sample_index in range(8)
    ]
    assert any(8 in legend for legend in legends)


def test_default_program_is_exact_selected_canonical_source():
    adapter = _load_adapter()
    assert adapter.program({"ring_order": "outer_to_inner"}) == _canonical_program()
    assert (HOME / "canonical.rkt").read_text(encoding="utf-8") == _canonical_program()


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_counts_matched_inputs_distinctness_and_setting_identification(demos):
    adapter = _load_adapter()
    for seed in (0, 17):
        episodes = [adapter.generate(seed, setting, demos, 4) for setting in SETTINGS]
        assert _inputs(episodes[0]) == _inputs(episodes[1])
        for setting, episode in zip(SETTINGS, episodes, strict=True):
            assert len(episode["train"]) == demos
            assert len(episode["test"]) == 4
            assert episode["program_solution"] == adapter.program(setting)
            keys = [json.dumps(grid, separators=(",", ":")) for grid in _inputs(episode)]
            assert len(keys) == len(set(keys)) == demos + 4
            assert adapter.family.teaching_check(episode, setting["ring_order"])["surviving_modes"] == [
                setting["ring_order"]
            ]
        assert episodes[0]["train"][0]["output"] != episodes[1]["train"][0]["output"]


def test_widest_gap_intermediate_varies_and_drives_the_output():
    adapter = _load_adapter()
    episode = adapter.generate(31, {"ring_order": "widest_gap_anchor"}, 6, 4)
    anchors = [adapter.family.widest_gap_index(pair["input"]) for pair in episode["train"] + episode["test"]]
    assert {0, 1, 2}.issubset(set(anchors))
    assert anchors[0] != 0, "first nondefault witness must exercise a noncanonical intermediate"
    for pair, anchor in zip(episode["train"] + episode["test"], anchors, strict=True):
        assert adapter.family.transform(pair["input"], "widest_gap_anchor", forced_anchor=anchor) == pair["output"]
        if anchor != 0:
            assert adapter.family.transform(pair["input"], "widest_gap_anchor", forced_anchor=0) != pair["output"]


def test_four_queries_include_substantive_30x30_stress():
    adapter = _load_adapter()
    episode = adapter.generate(7, {"ring_order": "widest_gap_anchor"}, 3, 4)
    large = episode["test"][-1]
    assert len(large["input"]) == 30 and all(len(row) == 30 for row in large["input"])
    assert sum(value == 8 for row in large["input"] for value in row) >= 180
    assert sum(value not in (0, 8) for row in large["output"][1:] for value in row) >= 350
    assert large["input"] != large["output"]


def test_python_claims_match_protected_racket_for_every_setting():
    adapter = _load_adapter()
    from arcpuzzles.parametric_worker import _real_evaluator
    import arc_repl.racket_bridge as bridge_module

    runtime = Path(bridge_module.__file__).resolve().parents[1]
    evaluate, identity, bridge = _real_evaluator(runtime)
    try:
        assert identity["backend"] == "racket" and identity["protected"] is True
        for setting in SETTINGS:
            episode = adapter.generate(13, setting, 2, 4)
            program = adapter.program(setting)
            for pair in episode["train"] + episode["test"]:
                assert evaluate(program, pair["input"]) == pair["output"]
    finally:
        bridge.close()


@pytest.mark.parametrize(
    "seed,settings,demos,queries",
    [
        (True, {"ring_order": "outer_to_inner"}, 2, 4),
        (-1, {"ring_order": "outer_to_inner"}, 2, 4),
        (0, {"ring_order": "outer_to_inner"}, 1, 4),
        (0, {"ring_order": "outer_to_inner"}, 7, 4),
        (0, {"ring_order": "outer_to_inner"}, 2, 3),
        (0, {"ring_order": "outer_to_inner"}, 2, 5),
        (0, {"ring_order": "bogus"}, 2, 4),
        (0, {"ring_order": "outer_to_inner", "extra": 1}, 2, 4),
    ],
)
def test_invalid_requests_fail_visibly(seed, settings, demos, queries):
    with pytest.raises((TypeError, ValueError)):
        _load_adapter().generate(seed, settings, demos, queries)


def test_bounded_self_audit_refutes_named_shortcuts():
    path = HOME / "audit.py"
    assert path.is_file(), "bounded self-audit has not been implemented"
    spec = importlib.util.spec_from_file_location("_arc_5e5205e54c96_audit_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    report = module.run(seeds=(0, 1, 17, 29))
    assert report["schema"] == "arcpuzzles-parametric-self-audit-v1"
    assert report["status"] == "passed"
    assert report["surviving_rivals"] == []
    assert report["episodes_checked"] == 8
    assert report["has_30x30"] is True
