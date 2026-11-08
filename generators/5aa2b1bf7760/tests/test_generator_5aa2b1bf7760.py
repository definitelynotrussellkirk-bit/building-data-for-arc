"""Focused regressions for the 5aa2b1bf7760 connected-component packer."""
from __future__ import annotations

import copy
import hashlib
import json
import random
from collections import Counter
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.base import set_ctx_observer
from scripts.generator_module_loader import load_module_from_path
from scripts.rule_smoke import purity_body, rule_application

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "5aa2b1bf7760"
GENERATOR_PATH = ROOT / "puzzle_generators/per_puzzle" / TASK_ID / "generator.py"
BASE_PATH = (
    ROOT
    / "data/base/solutions/banks/9a66c53abf7f"
    / "M128__5aa2b1bf7760.json"
)
MODULE = load_module_from_path(f"test_generator_{TASK_ID}_module", GENERATOR_PATH)


def _canonical_row() -> dict:
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"missing canonical row for {TASK_ID}")


def _norm_grid(grid) -> list[list[int]]:
    return [
        [int(value) for value in row] if isinstance(row, str) else [int(value) for value in row]
        for row in grid
    ]


def _all_pairs() -> list[dict]:
    row = _canonical_row()
    test = row["test"]
    pairs = list(row["train"]) + (list(test) if isinstance(test, list) else [test])
    return [
        {"input": _norm_grid(pair["input"]), "output": _norm_grid(pair["output"])}
        for pair in pairs
    ]


def _frozen(grid):
    return tuple(tuple(row) for row in grid)


def _normalized_rule_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _lesson(seed: int, start: int, difficulty: str) -> tuple[list[dict], dict]:
    pairs = []
    for sample_index in range(start, start + 4):
        grid = MODULE.generate(seed, sample_index, difficulty=difficulty)
        pairs.append({"input": grid, "output": MODULE.rule_mirror(grid)})
    return pairs[:3], pairs[3]


def test_metadata_rule_hash_and_task_local_authority_are_exact() -> None:
    row = _canonical_row()
    canonical = row["program_solution"]
    base = json.loads(BASE_PATH.read_text(encoding="utf-8"))
    target = base["racket_target"]

    assert MODULE.VERSION == "3.0.0"
    assert MODULE.RULE_HASH == "ed659d688832"
    assert MODULE.RULE_HASH == _normalized_rule_hash(canonical)
    assert target["target_code"] == canonical
    assert target["raw_code"] == canonical


def test_all_canonical_pairs_are_accepted_mirrored_and_input_pure() -> None:
    pairs = _all_pairs()
    assert len(pairs) == 5
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert MODULE.self_check(pair["input"]) == []
        assert MODULE.strict_canonical_like(pair["input"]) == []
        assert MODULE.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_canonical_racket_parity_input_purity_and_a_b_a() -> None:
    source = _canonical_row()["program_solution"]
    pairs = _all_pairs()
    bridge = RacketBridge(max_calls_before_restart=64)
    try:
        for pair in pairs:
            before = copy.deepcopy(pair["input"])
            actual = bridge.eval_text(rule_application(source, pair["input"]))
            assert actual == pair["output"]
            assert pair["input"] == before
        probe = bridge.eval_text(purity_body(source, pairs[0]["input"], pairs[1]["input"]))
        assert probe[0] == pairs[0]["output"]
        assert probe[1] == pairs[0]["output"]
        assert probe[2] == pairs[0]["input"]
    finally:
        bridge.shutdown()


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_exact_override_boundaries_are_observable(difficulty: str) -> None:
    cases = [
        {"grid_h": 9},
        {"grid_h": 10},
        {"grid_w": 13},
        {"grid_w": 15},
        *({"palette_kind": value} for value in MODULE.PALETTE_KINDS),
        *({"shape_set": value} for value in MODULE.SHAPE_SETS),
        *({"scene_profile": value} for value in MODULE.SCENE_PROFILES),
        {
            "grid_h": 10,
            "grid_w": 15,
            "palette_kind": "varied",
            "shape_set": "mixed",
            "scene_profile": "diagonal5",
        },
    ]
    for index, overrides in enumerate(cases):
        grid = MODULE.generate(
            10_000 + index,
            500 + index,
            difficulty=difficulty,
            **overrides,
        )
        assert MODULE.self_check(grid) == []
        observed = MODULE.observe_overrides(grid)
        for name, requested in overrides.items():
            assert observed[name] == requested


def test_unknown_invalid_and_wrong_typed_overrides_fail_loudly() -> None:
    with pytest.raises(ValueError, match="unknown override"):
        MODULE.generate(1, 2, obsolete_axis=3)
    with pytest.raises(ValueError):
        MODULE.generate(1, 2, grid_h=8)
    with pytest.raises(ValueError):
        MODULE.generate(1, 2, grid_w=16)
    with pytest.raises(ValueError):
        MODULE.generate(1, 2, palette_kind="neon")
    with pytest.raises(ValueError):
        MODULE.generate(1, 2, shape_set="square")
    with pytest.raises(ValueError):
        MODULE.generate(1, 2, scene_profile="identity")


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_default_draw_provenance_matches_exact_observer(difficulty: str) -> None:
    for offset in range(30):
        captured = []
        set_ctx_observer(captured.append)
        try:
            grid = MODULE.generate(73_000 + offset, offset, difficulty=difficulty)
        finally:
            set_ctx_observer(None)
        assert len(captured) == 1
        assert set(captured[0].recorded_draws()) == set(MODULE.AXES)
        assert captured[0].recorded_draws() == MODULE.observe_overrides(grid)
        assert captured[0].overrides_used() == {}


def test_determinism_fresh_returns_and_global_rng_purity() -> None:
    random.seed(987_654_321)
    state = random.getstate()
    first = MODULE.generate(901, 17, difficulty="hard")
    assert random.getstate() == state
    replay = MODULE.generate(901, 17, difficulty="hard")
    assert random.getstate() == state
    assert replay == first
    assert replay is not first
    assert all(a is not b for a, b in zip(replay, first))
    replay[0][0] = 9 if replay[0][0] != 9 else 8
    assert MODULE.generate(901, 17, difficulty="hard") == first


def test_sequential_schedule_makes_every_four_pair_lesson_identifiable() -> None:
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for lesson_index in range(20):
            start = 100 + lesson_index * 11
            demos, query = _lesson(81_000 + band_index, start, band)
            profiles = [MODULE.observe_overrides(pair["input"])["scene_profile"] for pair in demos]
            assert "diagonal5" in profiles
            assert MODULE.lesson_identifiable(demos, query) == []


def test_linked_semantic_census_200_per_band_and_disjoint_stability() -> None:
    pooled_profiles = Counter()
    for band_index, band in enumerate(("easy", "medium", "hard")):
        grids = [
            MODULE.generate(120_000 + band_index * 10_000 + seed, seed, difficulty=band)
            for seed in range(200)
        ]
        assert all(MODULE.self_check(grid) == [] for grid in grids)
        assert all(MODULE.rule_mirror(grid) != grid for grid in grids)
        assert all(MODULE.rule_mirror(grid) != MODULE._color_only_rival(grid) for grid in grids)
        assert all(MODULE.rule_mirror(grid) != MODULE._spatial_rival(grid) for grid in grids)
        assert all(MODULE.rule_mirror(grid) != MODULE._bbox_area_rival(grid) for grid in grids)
        assert all(MODULE.rule_mirror(grid) != MODULE._filled_bbox_rival(grid) for grid in grids)
        assert len({_frozen(grid) for grid in grids}) >= 150
        assert len({_frozen(MODULE.rule_mirror(grid)) for grid in grids}) >= 150
        profiles = Counter(MODULE.observe_overrides(grid)["scene_profile"] for grid in grids)
        assert set(profiles) == set(MODULE.SCENE_PROFILES)
        pooled_profiles.update(profiles)

        stability = [
            MODULE.generate(220_000 + band_index * 10_000 + seed, 1_000 + seed, difficulty=band)
            for seed in range(100)
        ]
        assert len({_frozen(grid) for grid in stability}) >= 75
        assert set(MODULE.observe_overrides(grid)["scene_profile"] for grid in stability) == set(
            MODULE.SCENE_PROFILES
        )
    assert set(pooled_profiles) == set(MODULE.SCENE_PROFILES)


def test_every_profile_rebuts_named_shortcuts() -> None:
    for profile in MODULE.SCENE_PROFILES:
        grid = MODULE.generate(
            300_000,
            7,
            difficulty="medium",
            scene_profile=profile,
            shape_set="mixed",
            palette_kind="varied",
        )
        official = MODULE.rule_mirror(grid)
        assert official != MODULE._color_only_rival(grid)
        assert official != MODULE._spatial_rival(grid)
        assert official != MODULE._bbox_area_rival(grid)
        assert official != MODULE._filled_bbox_rival(grid)
        if profile == "diagonal5":
            assert official != MODULE._color_group_rival(grid)


def test_self_check_rejects_five_targeted_impostors() -> None:
    source = MODULE.generate(
        400_000,
        0,
        difficulty="hard",
        scene_profile="diagonal5",
        shape_set="mixed",
        palette_kind="default",
    )
    assert MODULE.self_check(source) == []

    # 1. Too few components.
    too_few = copy.deepcopy(source)
    for component in MODULE._components(too_few)[2:]:
        for r, c in component["cells"]:
            too_few[r][c] = 0
    assert MODULE.self_check(too_few)

    # 2. Equal-size filled rectangles hide both the area order and crop texture.
    all_equal = [[0] * 13 for _ in range(9)]
    for color, (r0, c0) in zip((2, 4, 7), ((0, 0), (0, 5), (5, 10))):
        all_equal[r0][c0] = color
        all_equal[r0][c0 + 1] = color
    assert MODULE.self_check(all_equal)

    # 3. Repeated color has the wrong component multiplicity/shape.
    wrong_repeat = copy.deepcopy(source)
    singleton_parts = [part for part in MODULE._components(wrong_repeat) if part["area"] == 1]
    large_color = next(part["color"] for part in MODULE._components(wrong_repeat) if part["area"] > 1)
    r, c = next(iter(singleton_parts[0]["cells"]))
    wrong_repeat[r][c] = large_color
    assert MODULE.self_check(wrong_repeat)

    # 4. Different colors touch diagonally, violating the blank-buffer grammar.
    touching = copy.deepcopy(source)
    first_large = next(part for part in MODULE._components(touching) if part["area"] > 1)
    foreign_color = next(part["color"] for part in MODULE._components(touching) if part is not first_large)
    placed = False
    for r, c in first_large["cells"]:
        for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < len(touching) and 0 <= nc < len(touching[0]) and touching[nr][nc] == 0:
                touching[nr][nc] = foreign_color
                placed = True
                break
        if placed:
            break
    assert placed
    assert MODULE.self_check(touching)

    # 5. Negative recombination: replace one repeated singleton by a color
    # absent from every remaining component. The oracle can still execute it,
    # but the teaching distribution must reject it.
    absent_feature = copy.deepcopy(source)
    existing = {value for row in absent_feature for value in row if value}
    replacement = next(color for color in range(1, 10) if color not in existing)
    singleton_parts = [part for part in MODULE._components(absent_feature) if part["area"] == 1]
    r, c = next(iter(singleton_parts[0]["cells"]))
    absent_feature[r][c] = replacement
    assert replacement not in {
        value
        for rr, row in enumerate(absent_feature)
        for cc, value in enumerate(row)
        if (rr, cc) != (r, c)
    }
    assert MODULE.self_check(absent_feature)
    assert MODULE.rule_mirror(absent_feature)
