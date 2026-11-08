"""Focused regression tests for the area-rank recoloring generator."""
from __future__ import annotations

import copy
import importlib
import importlib.util
import sys
import random
from pathlib import Path

import pytest

TASK_ID = "996fc37f49d9"
# This file is tested both in the library and in the copied legacy runtime.
LIBRARY = next((p for p in Path(__file__).resolve().parents
                if (p / "shared/runtime/puzzle_generators").is_dir()), None)
if LIBRARY is not None:
    ROOT = LIBRARY / "shared"
    sys.path.insert(0, str(ROOT / "runtime"))
    _path = LIBRARY / "generators" / TASK_ID / "generator.py"
    _spec = importlib.util.spec_from_file_location("area_rank_generator", _path)
    GEN = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(GEN)
else:
    ROOT = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(ROOT))
    GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")

from reviewer_support import canonical_pairs as _canonical_pairs, find_root


def canonical_pairs():
    return _canonical_pairs(TASK_ID, root=find_root(__file__))


def test_rule_hash_and_all_canonical_pairs():
    assert GEN.RULE_HASH == "b8683f5eb534"
    pairs = canonical_pairs()
    assert len(pairs) == 5
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_public_signature_bank_is_derived_from_all_five_inputs():
    signatures = {GEN._linked_signature(pair["input"]) for pair in canonical_pairs()}
    assert set(GEN._PUBLIC_SIGNATURES) == signatures
    assert set(GEN._PUBLIC_SIGNATURES.values()) == set(GEN.PUBLIC_PROFILES)


def test_default_prior_reaches_every_public_profile_in_every_band():
    for band in ("easy", "medium", "hard"):
        counts = {profile: 0 for profile in GEN.PUBLIC_PROFILES}
        for seed in range(800):
            grid = GEN.generate(seed, 0, difficulty=band)
            assert GEN.self_check(grid, difficulty=band) == []
            profile = GEN.observe_overrides(grid)["scene_profile"]
            if profile in counts:
                counts[profile] += 1
        assert all(count > 0 for count in counts.values()), (band, counts)
        assert sum(counts.values()) >= 350, (band, counts)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("profile", GEN.SCENE_PROFILES)
@pytest.mark.parametrize("color_mode", GEN.COLOR_MODES)
def test_exact_overrides_are_observable(band, profile, color_mode):
    grid = GEN.generate(
        991,
        17,
        difficulty=band,
        scene_profile=profile,
        color_mode=color_mode,
    )
    assert GEN.self_check(grid, difficulty=band) == []
    assert GEN.observe_overrides(grid) == {
        "scene_profile": profile,
        "color_mode": color_mode,
    }


def test_deterministic_replay_fresh_returns_and_global_rng_purity():
    random.seed(123456)
    state = random.getstate()
    first = GEN.generate(77, 5, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(77, 5, difficulty="hard")
    assert second == first
    assert second is not first
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert GEN.generate(77, 5, difficulty="hard") == second


def test_self_check_rejects_targeted_impostors():
    base = GEN.generate(
        12,
        3,
        difficulty="medium",
        scene_profile="general_2",
        color_mode="canonical7",
    )
    components = GEN._components(base)

    removed = copy.deepcopy(base)
    for row, col in components[0]:
        removed[row][col] = 0
    assert any("two or three" in reason for reason in GEN.self_check(removed))

    forbidden_color = copy.deepcopy(base)
    row, col = components[0][0]
    forbidden_color[row][col] = 2
    reasons = GEN.self_check(forbidden_color)
    assert any("output-rank" in reason for reason in reasons)

    multicolor = copy.deepcopy(base)
    row, col = components[0][0]
    multicolor[row][col] = 1
    reasons = GEN.self_check(multicolor)
    assert any("monochrome" in reason for reason in reasons)

    merged = copy.deepcopy(base)
    left, right = sorted(components, key=lambda cells: min(c for _, c in cells))
    a = min(left, key=lambda p: min(abs(p[0] - q[0]) + abs(p[1] - q[1]) for q in right))
    b = min(right, key=lambda q: abs(a[0] - q[0]) + abs(a[1] - q[1]))
    row, col = a
    while col != b[1]:
        col += 1 if b[1] > col else -1
        merged[row][col] = 7
    while row != b[0]:
        row += 1 if b[0] > row else -1
        merged[row][col] = 7
    assert any("two or three" in reason for reason in GEN.self_check(merged))

    tied = [[0] * 11 for _ in range(9)]
    for row, col in ((1, 1), (1, 2), (2, 1)):
        tied[row][col] = 7
    for row, col in ((6, 7), (6, 8), (7, 7)):
        tied[row][col] = 7
    assert any("strictly distinct" in reason for reason in GEN.self_check(tied))


def test_every_rotated_four_sample_lesson_rebuts_declared_competitors():
    for offset in range(4):
        pairs = []
        for sample_index in range(offset, offset + 4):
            grid = GEN.generate(200, sample_index, difficulty="medium")
            pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
        demos, query = pairs[:3], pairs[3]
        assert GEN.lesson_identifiable(demos, query) == []


# Regression gates added by review-8d7412087342e122. These are fixed-seed
# distribution checks, not claims of statistical independence or training gains.
def _bbox_area(cells):
    rows, cols = zip(*cells)
    return (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)


def _bbox_rank(grid):
    out = [[0] * len(grid[0]) for _ in grid]
    for rank, cells in enumerate(sorted(GEN._components(grid),
                                       key=lambda cells: (_bbox_area(cells), min(cells)))):
        for row, col in cells:
            out[row][col] = rank + 2
    return out


@pytest.mark.parametrize("profile,n", [("general_2", 2), ("general_3", 3)])
def test_each_input_colour_can_occupy_every_area_rank(profile, n):
    seen = [set() for _ in range(n)]
    for seed in range(180):
        grid = GEN.generate(seed, 0, scene_profile=profile, color_mode="component_colors")
        for rank, cells in enumerate(sorted(GEN._components(grid), key=len)):
            seen[rank].add(grid[cells[0][0]][cells[0][1]])
    assert all(colors == set(GEN._INPUT_COLORS) for colors in seen), seen


@pytest.mark.parametrize("profile", ["general_2", "general_3"])
def test_general_profiles_break_bbox_rank_at_a_material_rate(profile):
    inversions = 0
    for seed in range(160):
        grid = GEN.generate(seed, 0, scene_profile=profile, color_mode="canonical7")
        boxes = [_bbox_area(cells) for cells in sorted(GEN._components(grid), key=len)]
        inversions += boxes != sorted(boxes)
    assert inversions >= 50, inversions


@pytest.mark.parametrize("profile", ["general_2", "general_3"])
def test_general_sizes_dimensions_and_context_are_not_a_tiny_lookup_table(profile):
    sizes, dimensions, area_roles = set(), set(), {}
    for seed in range(200):
        grid = GEN.generate(seed, 0, scene_profile=profile)
        dimensions.add((len(grid), len(grid[0])))
        for rank, cells in enumerate(sorted(GEN._components(grid), key=len)):
            sizes.add(len(cells))
            area_roles.setdefault(len(cells), set()).add(rank)
    assert len(sizes) >= 12, sizes
    assert len(dimensions) >= 30, dimensions
    n = int(profile[-1])
    assert sum(len(roles) == n for roles in area_roles.values()) >= 5, area_roles


def test_lesson_gate_names_the_canonical_bbox_shortcut():
    demos = canonical_pairs()[:4]
    assert all(_bbox_rank(p["input"]) == p["output"] for p in demos)
    # Exact valid two-component counterexample: a sparse 5-cell L in a 3x3
    # bounding box, versus a dense 6-cell 2x3 rectangle.
    query = [[0] * 14 for _ in range(13)]
    for r, c in ((1, 1), (2, 1), (3, 1), (3, 2), (3, 3)):
        query[r][c] = 7
    for r in (8, 9):
        for c in (8, 9, 10):
            query[r][c] = 7
    assert GEN.self_check(query) == []
    assert _bbox_rank(query) != GEN.rule_mirror(query)
    reasons = GEN.lesson_identifiable(demos, {"input": query})
    assert any("bounding" in reason.lower() for reason in reasons), reasons


def test_semantic_witnesses_are_bound_to_executable_rivals_or_branch_coverage():
    # The strict after-phase gate must not mistake feature presence for a
    # counterexample. Every witness has an explicit, independently checkable role.
    assert hasattr(GEN, "WITNESS_RIVALS"), "missing executable rival claims"
    assert set(GEN.SEMANTIC_WITNESSES) == set(GEN.WITNESS_RIVALS) | set(GEN.BRANCH_WITNESSES)
    assert all(GEN.CANONICAL_SHORTCUTS["bounding_box"](p["input"]) == p["output"]
               for p in canonical_pairs())
    for seed in range(60):
        grid = GEN.generate(seed, 0)
        for name, rivals in GEN.WITNESS_RIVALS.items():
            if GEN.SEMANTIC_WITNESSES[name](grid):
                for rival in rivals:
                    assert GEN.SEMANTIC_RIVALS[rival](grid) != GEN.rule_mirror(grid)
