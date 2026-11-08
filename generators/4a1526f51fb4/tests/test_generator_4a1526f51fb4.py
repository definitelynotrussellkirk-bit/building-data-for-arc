from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest

from puzzle_generators.runner import _apply_rule, _load_bundle, _open_bridge_with_rule
from src.core.canonical_pairs import load_task_pairs

GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.4a1526f51fb4.generator"
)
TASK_ID = "4a1526f51fb4"
ROOT = Path(__file__).resolve().parents[1]
BASE_PATH = (
    ROOT
    / "data/base/solutions/banks/9a66c53abf7f/M131__4a1526f51fb4.json"
)


def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _expected_output(grid):
    palette = [value for value in grid[-1] if value != 0]
    frame_cells = {
        (row, col)
        for row in range(len(grid) - 1)
        for col, value in enumerate(grid[row])
        if value != 0
    }
    rows = [row for row, _ in frame_cells]
    cols = [col for _, col in frame_cells]
    r0, r1, c0, c1 = min(rows), max(rows), min(cols), max(cols)
    out = [[0 for _ in range(c1 - c0 + 1)] for _ in range(r1 - r0 + 1)]
    depth = 0
    while r0 + 2 * depth <= r1 - 2 * depth and c0 + 2 * depth <= c1 - 2 * depth:
        rr0, rr1 = r0 + 2 * depth, r1 - 2 * depth
        cc0, cc1 = c0 + 2 * depth, c1 - 2 * depth
        border = (
            [(rr0, col) for col in range(cc0, cc1 + 1)]
            + [(rr1, col) for col in range(cc0, cc1 + 1)]
            + [(row, cc0) for row in range(rr0, rr1 + 1)]
            + [(row, cc1) for row in range(rr0, rr1 + 1)]
        )
        if not all(grid[row][col] != 0 for row, col in border):
            break
        for row, col in border:
            out[row - r0][col - c0] = palette[depth]
        depth += 1
    return out


def _bridge():
    bundle = _load_bundle(TASK_ID)
    return _open_bridge_with_rule(bundle.rule_callable_text)


def test_metadata_rule_hash_and_task_local_authorities_are_exact():
    assert GEN.GENERATOR_ID == TASK_ID
    assert GEN.TASK_ID == TASK_ID
    assert GEN.VERSION == "3.0.0"
    canonical = None
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            canonical = row["program_solution"]
            break
    assert canonical is not None
    record = json.loads(BASE_PATH.read_text())
    target = record["racket_target"]
    assert target["raw_code"] == canonical
    assert target["target_code"] == canonical
    assert GEN.RULE_HASH == _normalized_hash(canonical) == "2e5956bb4999"


def test_all_canonical_pairs_match_rule_and_self_check():
    pairs = load_task_pairs(TASK_ID)
    assert len(pairs) == 5
    for pair in pairs:
        assert pair["output"] is not None
        assert GEN.self_check(pair["input"]) == []
        assert _expected_output(pair["input"]) == pair["output"]


def test_racket_exactness_input_purity_and_a_b_a_repeat():
    bridge, fn_name = _bridge()
    try:
        pairs = load_task_pairs(TASK_ID)
        for pair in pairs:
            source = copy.deepcopy(pair["input"])
            before = copy.deepcopy(source)
            assert _apply_rule(bridge, fn_name, source) == pair["output"]
            assert source == before

        grid_a = GEN.generate(
            901,
            11,
            difficulty="easy",
            scene_profile=GEN.CANON_D2_WIDE,
            frame_color=8,
            palette_relation="contains_frame",
            palette_tail="one_extra",
        )
        grid_b = GEN.generate(
            902,
            12,
            difficulty="hard",
            scene_profile=GEN.GENERAL_D4_DEEP,
            frame_color=3,
            palette_relation="excludes_frame",
            palette_tail="exact",
        )
        out_a1 = _apply_rule(bridge, fn_name, grid_a)
        out_b = _apply_rule(bridge, fn_name, grid_b)
        out_a2 = _apply_rule(bridge, fn_name, grid_a)
        assert out_a1 == _expected_output(grid_a)
        assert out_b == _expected_output(grid_b)
        assert out_a2 == out_a1
    finally:
        bridge.shutdown()


@pytest.mark.parametrize("profile", GEN.SCENE_PROFILES)
@pytest.mark.parametrize("frame_color", [1, 9])
@pytest.mark.parametrize("palette_relation", GEN.PALETTE_RELATIONS)
@pytest.mark.parametrize("palette_tail", GEN.PALETTE_TAILS)
def test_every_boundary_override_combination_is_structural_and_observable(
    profile, frame_color, palette_relation, palette_tail
):
    grid = GEN.generate(
        211,
        17,
        difficulty="hard",
        scene_profile=profile,
        frame_color=frame_color,
        palette_relation=palette_relation,
        palette_tail=palette_tail,
    )
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == {
        "scene_profile": profile,
        "frame_color": frame_color,
        "palette_relation": palette_relation,
        "palette_tail": palette_tail,
    }
    assert _expected_output(grid) != grid


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_default_draws_cover_canonical_and_generalized_profiles(difficulty):
    observations = [
        GEN.observe_overrides(GEN.generate(seed, 1000 + seed, difficulty=difficulty))
        for seed in range(160)
    ]
    profiles = {item["scene_profile"] for item in observations}
    assert profiles & GEN.CANONICAL_PROFILES
    assert profiles - GEN.CANONICAL_PROFILES
    assert {item["palette_relation"] for item in observations} == set(GEN.PALETTE_RELATIONS)
    assert {item["palette_tail"] for item in observations} == set(GEN.PALETTE_TAILS)
    assert 8 in {item["frame_color"] for item in observations}
    assert len({item["frame_color"] for item in observations}) >= 7


def test_tail_palette_color_is_a_true_unused_distractor():
    grid = GEN.generate(
        501,
        2,
        scene_profile=GEN.CANON_D3_COMPACT,
        frame_color=8,
        palette_relation="excludes_frame",
        palette_tail="exact",
    )
    positions = [col for col, value in enumerate(grid[-1]) if value != 0]
    used_colors = {grid[-1][col] for col in positions}
    extra = next(color for color in range(1, 10) if color not in used_colors and color != 8)
    extended = copy.deepcopy(grid)
    extended[-1][positions[-1] + 1] = extra
    assert GEN.observe_overrides(extended)["palette_tail"] == "one_extra"

    bridge, fn_name = _bridge()
    try:
        assert _apply_rule(bridge, fn_name, grid) == _apply_rule(bridge, fn_name, extended)
    finally:
        bridge.shutdown()


def test_determinism_fresh_returns_and_global_rng_isolation():
    state = random.getstate()
    first = GEN.generate(444, 19, difficulty="medium")
    assert random.getstate() == state
    second = GEN.generate(444, 19, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 1
    assert GEN.generate(444, 19, difficulty="medium") == second


@pytest.mark.parametrize(
    "overrides",
    [
        {"scene_profile": "unknown"},
        {"frame_color": 0},
        {"frame_color": 10},
        {"palette_relation": "mixed"},
        {"palette_tail": "two_extra"},
        {"texture": "warm"},
    ],
)
def test_invalid_or_unknown_overrides_fail_loudly(overrides):
    with pytest.raises(ValueError):
        GEN.generate(1, 1, **overrides)


def test_self_check_rejects_targeted_semantic_impostors():
    base = GEN.generate(
        71,
        8,
        scene_profile=GEN.CANON_D3_COMPACT,
        frame_color=8,
        palette_relation="excludes_frame",
        palette_tail="one_extra",
    )

    # 1. A new replacement color is absent from every remaining scene part.
    alien_frame = copy.deepcopy(base)
    frame_palette = set(alien_frame[-1])
    replacement = next(color for color in range(1, 10) if color not in frame_palette and color != 8)
    changed = False
    for row in range(len(alien_frame) - 1):
        for col, value in enumerate(alien_frame[row]):
            if value == 8:
                alien_frame[row][col] = replacement
                changed = True
                break
        if changed:
            break
    assert any("share one color" in error for error in GEN.self_check(alien_frame))

    # 2. A missing border cell destroys the complete depth grammar.
    broken_border = copy.deepcopy(base)
    broken_border[1][1] = 0
    assert any("identify exactly one" in error for error in GEN.self_check(broken_border))

    # 3. Duplicate palette colors erase the ordered depth-to-color mapping.
    duplicate_palette = copy.deepcopy(base)
    positions = [col for col, value in enumerate(duplicate_palette[-1]) if value != 0]
    duplicate_palette[-1][positions[1]] = duplicate_palette[-1][positions[0]]
    assert any("must be distinct" in error for error in GEN.self_check(duplicate_palette))

    # 4. Removing two palette entries leaves too few colors for three frames.
    short_palette = copy.deepcopy(base)
    for col in positions[-2:]:
        short_palette[-1][col] = 0
    errors = GEN.self_check(short_palette)
    assert any("two to five" in error or "one color per frame" in error for error in errors)

    # 5. A filled interior pixel is not part of any allowed outline.
    interior_noise = copy.deepcopy(base)
    interior_noise[2][2] = 8
    assert any("identify exactly one" in error for error in GEN.self_check(interior_noise))

    # 6. Irregular palette spacing creates an unstable reading-order cue.
    irregular_palette = copy.deepcopy(base)
    color = irregular_palette[-1][positions[-1]]
    irregular_palette[-1][positions[-1]] = 0
    irregular_palette[-1][positions[-1] + 2] = color
    assert any("constant stride" in error for error in GEN.self_check(irregular_palette))


def test_single_depth_old_degenerate_is_rejected():
    grid = [[0 for _ in range(12)] for _ in range(8)]
    for col in range(2, 9):
        grid[1][col] = grid[5][col] = 8
    for row in range(1, 6):
        grid[row][2] = grid[row][8] = 8
    grid[-1][0] = 4
    assert GEN.self_check(grid)
