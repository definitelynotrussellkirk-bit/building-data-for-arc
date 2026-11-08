from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _generator():
    return _load("b87_generator_under_test", HOME / "generator.py")


def _adapter():
    return _load("b87_adapter_under_test", HOME / "workspace/parametric/adapter.py")


def _prototype():
    return _load("b87_prototype_under_test", HOME / "workspace/parametric/prototype.py")


def _adversarial():
    return _load("b87_adversarial_under_test", HOME / "workspace/parametric/adversarial_review.py")


def test_canonical_generator_honors_exact_live_axes_and_requires_portals():
    gen = _generator()
    cases = [
        (8, 9, 1, "vertical", 0),
        (9, 8, 2, "horizontal", 3),
        (30, 30, 3, "vertical", 8),
    ]
    for index, (height, width, portals, orientation, extra_walls) in enumerate(cases):
        grid = gen.generate(
            9100 + index,
            index,
            difficulty="easy",
            grid_h=height,
            grid_w=width,
            n_portals=portals,
            barrier_orientation=orientation,
            extra_walls=extra_walls,
        )
        assert gen.self_check(grid) == []
        observed = gen.observe_overrides(grid)
        assert observed == {
            "grid_h": height,
            "grid_w": width,
            "n_portals": portals,
            "barrier_orientation": orientation,
            "extra_walls": extra_walls,
        }
        assert gen._shortest_path(grid, portal_mode="all_pairs") is not None
        assert gen._shortest_path(grid, portal_mode="none") is None
        assert grid == gen.generate(
            9100 + index,
            index,
            difficulty="easy",
            grid_h=height,
            grid_w=width,
            n_portals=portals,
            barrier_orientation=orientation,
            extra_walls=extra_walls,
        )


@pytest.mark.parametrize(
    "kwargs",
    [
        {"difficulty": "unknown"},
        {"unknown_axis": 1},
        {"grid_h": True},
        {"grid_w": 9.0},
        {"n_portals": "2"},
        {"extra_walls": False},
        {"barrier_orientation": 1},
        {"grid_h": 7},
        {"grid_w": 31},
        {"n_portals": 0},
        {"extra_walls": 9},
        {"barrier_orientation": "diagonal"},
    ],
)
def test_canonical_generator_rejects_invalid_calls(kwargs):
    gen = _generator()
    difficulty = kwargs.pop("difficulty", None)
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 0, difficulty=difficulty, **kwargs)


def test_canonical_self_check_rejects_structural_and_semantic_impostors():
    gen = _generator()
    good = gen.generate(3, 0, grid_h=10, grid_w=12, n_portals=2)
    malformed = [
        [],
        [[0], [0, 0]],
        [[True]],
        [row[:] for row in good],
        [row[:] for row in good],
        [row[:] for row in good],
    ]
    # Duplicate start.
    malformed[3][0][0] = 2
    # Break one portal pair.
    portal = next(v for v in (4, 5, 6) if sum(row.count(v) for row in malformed[4]) == 2)
    changed = False
    for row in malformed[4]:
        for c, value in enumerate(row):
            if value == portal:
                row[c] = 0
                changed = True
                break
        if changed:
            break
    # Punch a hole in the sole barrier, making a no-portal crossing possible.
    info = gen.observe_overrides(malformed[5])
    if info["barrier_orientation"] == "vertical":
        col = next(c for c in range(len(malformed[5][0])) if all(row[c] == 8 for row in malformed[5]))
        malformed[5][0][col] = 0
    else:
        row = next(r for r, values in enumerate(malformed[5]) if all(v == 8 for v in values))
        malformed[5][row][0] = 0
    for grid in malformed:
        assert gen.self_check(grid)


def test_parametric_programs_bind_canonical_bytes_and_are_distinct():
    adapter = _adapter()
    canonical = None
    for line in (ROOT / "shared/data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == "b87dcd3011b1":
            canonical = row["program_solution"]
            break
    assert canonical is not None
    all_pairs = adapter.program({"portal_policy": "all_pairs"})
    widest = adapter.program({"portal_policy": "widest_pair_only"})
    assert all_pairs == canonical
    assert widest != canonical
    assert all_pairs.startswith("(rule!") and widest.startswith("(rule!")


def test_parametric_inputs_are_matched_distinct_and_cover_boundaries():
    adapter = _adapter()
    proto = _prototype()
    left = adapter.generate(0, {"portal_policy": "all_pairs"}, demos=3, queries=4)
    right = adapter.generate(0, {"portal_policy": "widest_pair_only"}, demos=3, queries=4)
    left_pairs = left["train"] + left["test"]
    right_pairs = right["train"] + right["test"]
    assert [p["input"] for p in left_pairs] == [p["input"] for p in right_pairs]
    encoded = [json.dumps(p["input"]) for p in left_pairs]
    assert len(encoded) == len(set(encoded)) == 7
    assert all(p["output"] == proto.apply_policy(p["input"], "all_pairs") for p in left_pairs)
    assert all(p["output"] == proto.apply_policy(p["input"], "widest_pair_only") for p in right_pairs)
    assert all(a["output"] != b["output"] for a, b in zip(left_pairs, right_pairs))
    assert {proto.widest_portal_color(p["input"]) for p in left["train"]} == {4, 5, 6}
    assert any(len(p["input"]) == 30 and len(p["input"][0]) == 30 for p in left["test"])
    assert any(min(len(p["input"]), len(p["input"][0])) == 8 for p in left["test"])


def test_declared_minimum_defeats_tested_shortcut_selectors():
    audit = _adversarial()
    for seed in range(12):
        for setting in ("all_pairs", "widest_pair_only"):
            result = audit.review_episode(seed, setting, demos=3, queries=4)
            assert result["surviving_wrong_rivals"] == []
            assert result["query_failures"] == []


def test_adversarial_audit_reports_one_shot_seed_iterables_correctly():
    audit = _adversarial()
    result = audit.run(seeds=iter((0, 1)), demos=3, queries=4)
    assert result["seeds"] == 2
    assert result["episodes"] == 4
    assert result["status"] == "passed"


@pytest.mark.parametrize(
    "args",
    [
        (True, {"portal_policy": "all_pairs"}, 3, 4),
        (0, {"portal_policy": "all_pairs"}, 2, 4),
        (0, {"portal_policy": "all_pairs"}, 7, 4),
        (0, {"portal_policy": "all_pairs"}, 3, 0),
        (0, {"portal_policy": "all_pairs"}, 3, 5),
        (0, {"portal_policy": "bogus"}, 3, 4),
        (0, {"portal_policy": "all_pairs", "extra": 1}, 3, 4),
    ],
)
def test_adapter_rejects_bad_seed_settings_and_counts(args):
    adapter = _adapter()
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(*args)


def test_widest_intermediate_changes_across_inputs_and_fixed_color_ablation_changes_output():
    proto = _prototype()
    scenes = [proto.build_scene(17, "demo", index) for index in range(3)]
    assert [proto.widest_portal_color(grid) for grid in scenes] == [4, 5, 6]
    assert any(
        proto.apply_policy(grid, "widest_pair_only")
        != proto.apply_fixed_portal_color(grid, 4)
        for grid in scenes
    )


def test_canonical_semantic_contract_accepts_authority_and_refutes_no_portal_rival():
    gen = _generator()
    canonical_inputs = []
    for line in (ROOT / "shared/data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == "b87dcd3011b1":
            canonical_inputs = [
                pair["input"] for pair in [*row["train"], *row["test"]]
            ]
            break
    assert canonical_inputs
    for grid in canonical_inputs:
        assert gen.strict_canonical_like(grid) == []
        assert gen.self_check(grid) == []

    generated = gen.generate(
        42,
        0,
        difficulty="hard",
        grid_h=18,
        grid_w=19,
        n_portals=3,
        barrier_orientation="horizontal",
        extra_walls=8,
    )
    assert gen.strict_canonical_like(generated) == []
    assert gen.SEMANTIC_WITNESSES["portal_required"](generated)
    assert gen.SEMANTIC_RIVALS["no_portals"](generated) != gen.solve(generated)


def test_canonical_lesson_contract_rejects_a_no_portal_teaching_shortcut():
    gen = _generator()
    demos = []
    for index in range(gen.EXAMPLES_NEEDED):
        grid = gen.generate(51, index, difficulty="medium")
        demos.append({"input": grid, "output": gen.solve(grid)})
    query_grid = gen.generate(51, gen.EXAMPLES_NEEDED, difficulty="medium")
    query = {"input": query_grid, "output": gen.solve(query_grid)}
    assert gen.lesson_identifiable(demos, query) == []

    shortcut_demos = [
        {"input": pair["input"], "output": gen.SEMANTIC_RIVALS["no_portals"](pair["input"])}
        for pair in demos
    ]
    reasons = gen.lesson_identifiable(shortcut_demos, query)
    assert reasons
    assert any("output" in reason or "no_portals" in reason for reason in reasons)


def test_adapter_supports_both_count_edges_and_keeps_four_queries_independent():
    adapter = _adapter()
    one_query = adapter.generate(23, {"portal_policy": "all_pairs"}, demos=6, queries=1)
    four_queries = adapter.generate(23, {"portal_policy": "all_pairs"}, demos=6, queries=4)
    assert len(one_query["train"]) == len(four_queries["train"]) == 6
    assert len(one_query["test"]) == 1
    assert len(four_queries["test"]) == 4
    assert one_query["train"] == four_queries["train"]
    assert one_query["test"] == four_queries["test"][:1]


def test_each_difficulty_band_retains_an_exact_canonical_profile_anchor():
    gen = _generator()
    canonical_profiles = {(9, 11, 5), (9, 12, 5), (11, 13, 5)}
    for band in ("easy", "medium", "hard"):
        observed = set()
        for sample_index in range(20):
            grid = gen.generate(8000 + sample_index, sample_index, difficulty=band)
            observed.add(
                (len(grid), len(grid[0]), len({cell for row in grid for cell in row}))
            )
        assert observed & canonical_profiles, (band, observed)
