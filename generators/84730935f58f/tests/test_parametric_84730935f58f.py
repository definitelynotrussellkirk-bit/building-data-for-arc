"""Contract and adversarial tests for the proposed overlap-aware family."""
from __future__ import annotations

from functools import cache
import importlib.util
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "84730935f58f"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID / "workspace" / "parametric"


def load(path: Path, name: str):
    assert path.is_file(), f"missing {path.relative_to(ROOT)}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@cache
def prototype():
    return load(HOME / "prototype.py", "_parametric_84730935f58f")


@cache
def adapter():
    return load(HOME / "adapter.py", "_adapter_84730935f58f")


def all_pairs(episode):
    return episode["train"] + episode["test"]


def test_default_program_is_exact_canonical_and_alternate_is_distinct():
    p = prototype()
    canonical = p.canonical_program(root=ROOT)
    assert p.program({"render_mode": "union"}) == canonical
    assert p.program({"render_mode": "overlap_highlight"}) != canonical
    assert adapter().program({"render_mode": "union"}) == canonical


def test_python_claims_match_protected_racket_including_30x30():
    p = prototype()
    from arc_repl.racket_bridge import RacketBridge

    grids = [row["input"] for row in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)]
    grids += [p.scene(73, "demo", index, demos=3) for index in range(2)]
    grids += [p.scene(73, "query", index, demos=3) for index in range(4)]
    with RacketBridge(max_calls_before_restart=128) as bridge:
        for grid in grids:
            for render_mode in p.RENDER_MODES:
                settings = {"render_mode": render_mode}
                assert p.execute(bridge, p.program(settings), grid) == p.transform(grid, settings)


@pytest.mark.parametrize("demos", [2, 3, 6])
@pytest.mark.parametrize("render_mode", ["union", "overlap_highlight"])
def test_episode_supports_demo_range_four_queries_and_demo_only_identification(demos, render_mode):
    p = prototype()
    settings = {"render_mode": render_mode}
    episode = p.generate(500 + demos, settings, demos=demos, queries=4)
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == 4
    assert episode["program_solution"] == p.program(settings)
    inputs = [p.grid_digest(pair["input"]) for pair in all_pairs(episode)]
    assert len(inputs) == len(set(inputs)) == demos + 4
    assert p.surviving_settings(episode["train"]) == [settings]
    assert {p.profile(pair["input"])["mode"] for pair in episode["train"][:2]} == {"plus", "x"}
    assert all(p.profile(pair["input"])["overlap_cells"] > 0 for pair in episode["train"])


def test_equal_seed_and_counts_produce_matched_inputs_across_settings():
    p = prototype()
    first = p.generate(219, {"render_mode": "union"}, demos=3, queries=4)
    second = p.generate(219, {"render_mode": "overlap_highlight"}, demos=3, queries=4)
    assert [pair["input"] for pair in all_pairs(first)] == [pair["input"] for pair in all_pairs(second)]
    assert any(a["output"] != b["output"] for a, b in zip(all_pairs(first), all_pairs(second)))


def test_query_schedule_has_substantive_size_boundary_and_content_spread():
    p = prototype()
    episode = p.generate(41, {"render_mode": "overlap_highlight"}, demos=3, queries=4)
    profiles = [p.profile(pair["input"]) for pair in episode["test"]]
    assert [(row["height"], row["width"]) for row in profiles] == [
        (10, 12), (16, 18), (24, 27), (30, 30)
    ]
    assert {row["mode"] for row in profiles} == {"plus", "x"}
    assert profiles[-1]["num_seeds"] >= 16
    assert profiles[-1]["occupied_quadrants"] == 4
    assert profiles[-1]["boundary_seed_count"] >= 2
    assert profiles[-1]["overlap_cells"] >= 8


def test_overlap_highlight_is_coverage_multiplicity_not_seed_or_color_shortcut():
    p = prototype()
    episode = p.generate(101, {"render_mode": "overlap_highlight"}, demos=2, queries=4)
    saw_nonseed_overlap = False
    saw_single_seed = False
    for pair in all_pairs(episode):
        grid, output = pair["input"], pair["output"]
        counts = p.coverage_counts(grid)
        seeds = set(p.seed_cells(grid))
        for r, row in enumerate(output):
            for c, value in enumerate(row):
                count = counts.get((r, c), 0)
                assert value == (2 if count >= 2 else 8 if count == 1 else 0)
                saw_nonseed_overlap |= count >= 2 and (r, c) not in seeds
                saw_single_seed |= (r, c) in seeds and count == 1
    assert saw_nonseed_overlap
    assert saw_single_seed


@pytest.mark.parametrize("render_mode", ["union", "overlap_highlight"])
def test_minimum_lesson_rejects_fixed_stencil_and_wrong_render_rivals(render_mode):
    p = prototype()
    settings = {"render_mode": render_mode}
    episode = p.generate(83, settings, demos=2, queries=4)
    demos = episode["train"]
    other = {"render_mode": "overlap_highlight" if render_mode == "union" else "union"}
    assert any(p.transform(pair["input"], other) != pair["output"] for pair in demos)
    assert any(p.transform_with_stencil(pair["input"], settings, "plus") != pair["output"] for pair in demos)
    assert any(p.transform_with_stencil(pair["input"], settings, "x") != pair["output"] for pair in demos)
    if render_mode == "overlap_highlight":
        assert any(p.seed_center_highlight_rival(pair["input"]) != pair["output"] for pair in demos)


def test_crossed_controls_change_intermediate_without_dimension_confound():
    p = prototype()
    plus = p.scene(997, "cross_plus", 0, demos=2)
    x = p.scene(997, "cross_x", 0, demos=2)
    assert (len(plus), len(plus[0])) == (len(x), len(x[0]))
    assert p.seed_cells(plus) == p.seed_cells(x)
    assert p.profile(plus)["mode"] == "plus"
    assert p.profile(x)["mode"] == "x"
    assert p.coverage_counts(plus) != p.coverage_counts(x)
    settings = {"render_mode": "overlap_highlight"}
    assert p.transform(plus, settings) != p.transform(x, settings)


@pytest.mark.parametrize(
    "settings,demos,queries",
    [
        ({"render_mode": "unknown"}, 3, 4),
        ({"render_mode": "union", "extra": 1}, 3, 4),
        ({"render_mode": "union"}, 1, 4),
        ({"render_mode": "union"}, 7, 4),
        ({"render_mode": "union"}, 3, 3),
        ({"render_mode": "union"}, True, 4),
    ],
)
def test_invalid_settings_and_counts_reject(settings, demos, queries):
    with pytest.raises((TypeError, ValueError)):
        prototype().generate(1, settings, demos=demos, queries=queries)


def test_adapter_is_thin_and_matches_prototype():
    p = prototype()
    a = adapter()
    settings = {"render_mode": "overlap_highlight"}
    assert a.program(settings) == p.program(settings)
    assert a.generate(13, settings, demos=3, queries=4) == p.generate(
        13, settings, demos=3, queries=4
    )
