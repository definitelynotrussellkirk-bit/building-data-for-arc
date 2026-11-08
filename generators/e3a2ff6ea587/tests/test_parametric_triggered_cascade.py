"""Focused behavior tests for the repaired rectangle-fill cascade family."""
from __future__ import annotations

import copy
import importlib.util
import json
import random
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, canonical_path, find_root, public_challenge_bytes

TASK_ID = "e3a2ff6ea587"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID
GENERATOR = HOME / "generator.py"
PARAMETRIC = HOME / "workspace" / "parametric"
PROTOTYPE = PARAMETRIC / "prototype.py"
ADAPTER = PARAMETRIC / "adapter.py"
CONTRACT = PARAMETRIC / "promotion.json"
PROBE = PARAMETRIC / "adversarial_probe.py"

SETTINGS = (
    {"cascade_mode": "canonical"},
    {"cascade_mode": "triggered_cascade"},
)


def _load(name: str, path: Path):
    assert path.is_file(), f"missing artifact: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def generator():
    return _load("generator_e3a2ff6ea587", GENERATOR)


@pytest.fixture(scope="module")
def prototype():
    return _load("prototype_e3a2ff6ea587", PROTOTYPE)


@pytest.fixture(scope="module")
def adapter():
    return _load("adapter_e3a2ff6ea587", ADAPTER)


@pytest.fixture(scope="module")
def probe():
    return _load("probe_e3a2ff6ea587", PROBE)


def _canonical_program() -> str:
    rows = [json.loads(line) for line in canonical_path(ROOT).read_text().splitlines()]
    programs = {row["program_solution"] for row in rows if row.get("task_id") == TASK_ID}
    assert len(programs) == 1
    return next(iter(programs))


def _all_inputs(episode):
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def _color_cells(grid):
    result = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                result.setdefault(value, []).append((r, c))
    return result


def _is_qualifying(cells):
    if len(cells) != 4:
        return False
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    return set(cells) == {
        (min(rs), min(cs)),
        (min(rs), max(cs)),
        (max(rs), min(cs)),
        (max(rs), max(cs)),
    }


def test_required_artifacts_exist():
    for path in (PROTOTYPE, ADAPTER, CONTRACT, PROBE):
        assert path.is_file()


def test_base_generator_repairs_positive_only_curriculum_and_controls(generator):
    for difficulty in (None, "easy", "medium", "hard"):
        for seed in range(8):
            grid = generator.generate(seed, seed % 3, difficulty=difficulty)
            assert generator.self_check(grid, difficulty=difficulty) == []
            classes = [_is_qualifying(cells) for cells in _color_cells(grid).values()]
            assert any(classes), (difficulty, seed)
            assert any(not value for value in classes), (difficulty, seed)

    forced = generator.generate(
        77,
        5,
        difficulty="hard",
        grid_h=12,
        grid_w=16,
        n_rects=3,
        n_distractors=3,
        texture="mixed",
    )
    observed = generator.observe_overrides(forced)
    assert observed["grid_h"] == 12
    assert observed["grid_w"] == 16
    assert observed["n_rects"] == 3
    assert observed["n_distractors"] == 3
    assert observed["texture"] == "mixed"
    assert generator.self_check(forced, meta={"overrides": observed}) == []

    for obsolete in ("palette_size", "position_bias", "n_distinct_colors", "rect_area"):
        with pytest.raises(ValueError, match="unknown override"):
            generator.generate(0, 0, **{obsolete: 1})
    with pytest.raises(ValueError, match="unknown override"):
        generator.generate(0, 0, typo_axis=1)


def test_base_rule_mirror_matches_all_original_labels(generator):
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) >= 5
    for pair in pairs:
        assert generator.rule_mirror(pair["input"]) == pair["output"]


def test_base_generation_is_deterministic_fresh_and_rng_pure(generator):
    random.seed(9917)
    before = random.getstate()
    first = generator.generate(55, 23, difficulty="hard")
    after = random.getstate()
    second = generator.generate(55, 23, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))


def test_default_program_is_exact_canonical_and_alternate_is_stateful(prototype, adapter):
    canonical = _canonical_program()
    assert prototype.program(SETTINGS[0]) == canonical
    assert adapter.program(SETTINGS[0]) == canonical
    alternate = prototype.program(SETTINGS[1])
    assert alternate == adapter.program(SETTINGS[1])
    assert alternate != canonical
    assert "anchor-hits" in alternate
    assert "stage" in alternate
    assert "(at stage" in alternate


def test_matched_inputs_minimum_and_maximum_lessons_with_four_queries(prototype):
    for demos in (2, 3, 6):
        episodes = [prototype.generate(17, setting, demos, 4) for setting in SETTINGS]
        assert _all_inputs(episodes[0]) == _all_inputs(episodes[1])
        assert all(len(ep["train"]) == demos and len(ep["test"]) == 4 for ep in episodes)
        encoded = [json.dumps(grid, separators=(",", ":")) for grid in _all_inputs(episodes[0])]
        assert len(encoded) == len(set(encoded))
        assert any(
            left["output"] != right["output"]
            for left, right in zip(episodes[0]["train"], episodes[1]["train"])
        )

    short = prototype.generate(29, SETTINGS[1], 2, 4)
    long = prototype.generate(29, SETTINGS[1], 6, 4)
    assert short["train"] == long["train"][:2]
    assert short["test"] == long["test"]


def test_sequential_intermediate_and_wrong_order_change_stage_b(prototype):
    episode = prototype.generate(41, SETTINGS[1], 2, 4)
    witnessed = 0
    for pair in episode["train"] + episode["test"]:
        analysis = prototype.analyze_scene(pair["input"])
        assert analysis["qualifying_colors"] >= 2
        assert analysis["positive_triggers"] >= 1
        assert analysis["overlap_decoys"] >= 1
        actual = prototype.apply_rule(pair["input"], "triggered_cascade")
        skipped = prototype.apply_counterfactual(pair["input"], "skip_stage_a")
        reversed_stage = prototype.apply_counterfactual(pair["input"], "reverse_stage_order")
        coverage_only = prototype.apply_counterfactual(pair["input"], "coverage_only")
        assert actual != skipped
        assert actual != reversed_stage
        assert actual != coverage_only
        witnessed += 1
    assert witnessed == 6


def test_substantive_30x30_query_spans_canvas_and_has_multiple_roles(prototype):
    for seed in (0, 17, 41, 91, 2**31 - 1):
        episode = prototype.generate(seed, SETTINGS[1], 2, 4)
        grid = episode["test"][-1]["input"]
        assert (len(grid), len(grid[0])) == (30, 30)
        analysis = prototype.analyze_scene(grid)
        assert analysis["occupied_rows"] >= 20, (seed, analysis)
        assert analysis["occupied_columns"] >= 24, (seed, analysis)
        assert analysis["input_nonzero"] >= 35, (seed, analysis)
        assert analysis["qualifying_colors"] >= 2
        assert analysis["two_point_colors"] >= 3
        assert analysis["nonqualifying_colors"] >= 4
        assert analysis["boundary_nonzero"] >= 4


def test_claim_labels_match_python_and_protected_racket(prototype):
    with RacketBridge(timeout=60) as bridge:
        assert bridge.runtime_identity["backend"] == "racket"
        assert bridge.runtime_identity["protected"] is True
        for setting in SETTINGS:
            episode = prototype.generate(37, setting, 2, 4)
            for pair in episode["train"] + episode["test"]:
                assert pair["output"] == prototype.apply_rule(pair["input"], setting["cascade_mode"])
                assert prototype.execute_rule(episode["program_solution"], pair["input"], bridge=bridge) == pair["output"]


def test_public_first_turn_hides_private_and_future_fields(prototype):
    episode = prototype.generate(53, SETTINGS[1], 3, 4)
    first = {"train": episode["train"], "test": [{"input": episode["test"][0]["input"]}]}
    raw = public_challenge_bytes(first)
    assert b"triggered_cascade" not in raw and b"program" not in raw
    assert "output" not in first["test"][0]

    changed = copy.deepcopy(episode)
    changed["program_solution"] = "private replacement"
    changed["test"][0]["output"][0][0] ^= 1
    changed["test"][2]["input"][0][0] ^= 1
    changed_first = {"train": changed["train"], "test": [{"input": changed["test"][0]["input"]}]}
    assert public_challenge_bytes(changed_first) == raw

    visible = copy.deepcopy(first)
    visible["test"][0]["input"][0][0] = (visible["test"][0]["input"][0][0] + 1) % 10
    assert public_challenge_bytes(visible) != raw


def test_contract_and_adapter_fail_closed(adapter):
    contract = json.loads(CONTRACT.read_text())
    assert contract["parameters"] == {"cascade_mode": ["canonical", "triggered_cascade"]}
    assert contract["default"] == {"cascade_mode": "canonical"}
    assert contract["limits"] == {"demos": [2, 6], "queries": [1, 4]}

    for settings in ({}, {"cascade_mode": "bbox"}, {"cascade_mode": "canonical", "x": 1}, None):
        with pytest.raises((TypeError, ValueError)):
            adapter.program(settings)
    for demos in (1, 7, True, 2.0):
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(0, SETTINGS[0], demos, 4)
    for queries in (0, 5, True, 4.0):
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(0, SETTINGS[0], 2, queries)
    for seed in (-1, True, 1.0):
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(seed, SETTINGS[0], 2, 4)


def test_deep_probe_refutes_shortcuts_and_crosses_nuisance_controls(probe):
    report = probe.run(seeds=(0, 17, 41, 91), demo_counts=(2, 6))
    assert report["status"] == "passed"
    assert report["episodes"] == 16
    assert report["remaining_demo_shortcuts"] == []
    assert report["remaining_query_shortcuts"] == []
    assert report["ambiguous_episode_shortcuts"] == []
    assert report["crossed_controls"] == {
        "intermediate_varies_at_fixed_profile": True,
        "profiles_vary_at_fixed_intermediate": True,
    }
    assert {
        "fill_every_bbox",
        "fill_exactly_four_bbox",
        "all_two_point_triggers",
        "any_anchor_hit",
        "coverage_only",
        "reverse_stage_order",
        "skip_stage_a",
        "lowest_trigger_only",
        "boundary_profile",
        "first_two_by_position",
        "largest_two_bboxes",
        "reuse_first_demo_output",
    } <= set(report["rivals"])
    assert report["boundaries"]["minimum_demos"] == 2
    assert report["boundaries"]["maximum_demos"] == 6
    assert report["boundaries"]["maximum_query_shape"] == [30, 30]


def test_minimum_lesson_defeats_boundary_profile_shortcut(prototype):
    """Regression: active triggers must not be inferable from fixed boundary roles."""
    def shortcut(grid):
        stage, _ = prototype._stage(grid)
        out = copy.deepcopy(stage)
        h, w = len(grid), len(grid[0])
        cells = prototype._cells_by_color(grid)
        for color in prototype._colors(grid):
            points = cells[color]
            boundary = [
                (r, c) for r, c in points
                if r in (0, h - 1) or c in (0, w - 1)
            ]
            if len(points) == 2 and len(boundary) == 1 and boundary[0] != (h - 1, w - 1):
                prototype._paint(out, prototype._bbox(points), color)
        return out

    for seed in (0, 17, 41, 91):
        episode = prototype.generate(seed, SETTINGS[1], 2, 4)
        assert any(shortcut(pair["input"]) != pair["output"] for pair in episode["train"])
