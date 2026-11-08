"""Independent regressions for selecting a frame by raw filled-cell count."""
from __future__ import annotations

from collections import deque
from copy import deepcopy
import importlib
import json
from pathlib import Path

import pytest
from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root

TASK = "75be7448827f"
ROOT = find_root(__file__)
gen = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")


def parse_frames(grid):
    """Independent color-1 rectangular-frame parser used only by tests."""
    h, w = len(grid), len(grid[0])
    remaining = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 1}
    frames = []
    while remaining:
        start = min(remaining)
        queue = deque([start])
        remaining.remove(start)
        cells = {start}
        while queue:
            r, c = queue.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    cells.add(nxt)
                    queue.append(nxt)
        r0 = min(r for r, _ in cells)
        r1 = max(r for r, _ in cells)
        c0 = min(c for _, c in cells)
        c1 = max(c for _, c in cells)
        expected = {
            (r, c)
            for r in range(r0, r1 + 1)
            for c in range(c0, c1 + 1)
            if r in (r0, r1) or c in (c0, c1)
        }
        assert cells == expected
        crop = [row[c0 + 1 : c1] for row in grid[r0 + 1 : r1]]
        count = sum(value != 0 for row in crop for value in row)
        area = len(crop) * len(crop[0])
        frames.append(
            {
                "bbox": (r0, c0, r1, c1),
                "crop": crop,
                "count": count,
                "area": area,
                "density": count / area,
            }
        )
    return sorted(frames, key=lambda frame: frame["bbox"])


def count_output(grid):
    frames = parse_frames(grid)
    return max(frames, key=lambda frame: frame["count"])["crop"]


def density_output(grid):
    frames = parse_frames(grid)
    return max(frames, key=lambda frame: frame["density"])["crop"]


def largest_area_output(grid):
    frames = parse_frames(grid)
    return max(frames, key=lambda frame: frame["area"])["crop"]


def independent_observation(grid):
    frames = parse_frames(grid)
    counts = sorted((frame["count"] for frame in frames), reverse=True)
    assert counts[0] > counts[1]
    count_winner = max(frames, key=lambda frame: frame["count"])
    density_winner = max(frames, key=lambda frame: frame["density"])
    area_winner = max(frames, key=lambda frame: frame["area"])
    density_conflict = count_winner["bbox"] != density_winner["bbox"]
    area_conflict = count_winner["bbox"] != area_winner["bbox"]
    assert density_conflict != area_conflict
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_frames": len(frames),
        "winner_count": counts[0],
        "count_margin": counts[0] - counts[1],
        "rival_kind": "density" if density_conflict else "area",
    }


def frozen(grid):
    return json.dumps(grid, separators=(",", ":"))


def test_required_contract_and_authority_pin():
    assert gen.RULE_HASH == "6f03f2e69da2"
    assert gen.EXAMPLES_NEEDED == 3
    assert gen.MIN_STRICT_FRAC == 1.0
    assert set(gen.AXES) == {
        "grid_h",
        "grid_w",
        "n_frames",
        "winner_count",
        "count_margin",
        "rival_kind",
    }
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


def test_all_canonical_pairs_follow_raw_count_with_source_tie_break():
    pairs = canonical_pairs(TASK, root=ROOT)
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(pair["input"]) == [], (pair["split"], pair["pair_index"])
        assert gen.strict_canonical_like(pair["input"]) == []
        assert count_output(pair["input"]) == pair["output"]
    # One authoritative example specifically refutes density selection.
    assert any(density_output(pair["input"]) != pair["output"] for pair in pairs)


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("rival_kind", ["density", "area"])
def test_exact_controls_are_honored_in_every_band(difficulty, rival_kind):
    settings = {
        "grid_h": 13,
        "grid_w": 14,
        "n_frames": 3,
        "winner_count": 8,
        "count_margin": 2,
        "rival_kind": rival_kind,
    }
    grid = gen.generate(311, 7, difficulty=difficulty, **settings)
    assert gen.self_check(grid) == []
    assert gen.strict_canonical_like(grid) == []
    assert independent_observation(grid) == settings
    assert gen.observe_overrides(grid) == settings
    if rival_kind == "density":
        assert count_output(grid) != density_output(grid)
        assert count_output(grid) == largest_area_output(grid)
    else:
        assert count_output(grid) != largest_area_output(grid)
        assert count_output(grid) == density_output(grid)


@pytest.mark.parametrize(
    "overrides",
    [
        {"unknown_axis": 1},
        {"grid_h": 12},
        {"grid_h": 21},
        {"grid_w": 13},
        {"grid_w": 23},
        {"n_frames": 1},
        {"n_frames": 4},
        {"winner_count": 5},
        {"winner_count": 9},
        {"count_margin": 0},
        {"count_margin": 3},
        {"grid_h": True},
        {"grid_w": 14.0},
        {"n_frames": "2"},
        {"winner_count": 8.0},
        {"count_margin": False},
        {"rival_kind": "unknown"},
        {"rival_kind": 1},
    ],
)
def test_invalid_overrides_reject_instead_of_coercing_or_ignoring(overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **overrides)


@pytest.mark.parametrize("difficulty", ["trivial", 0.5, True])
def test_invalid_difficulty_rejects(difficulty):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, difficulty=difficulty)


@pytest.mark.parametrize("sample_index", [True, False, 1.0, "1", -1])
def test_invalid_sample_index_rejects(sample_index):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, sample_index)


def test_every_fourth_default_sample_is_a_canonical_input_profile_in_each_band():
    canonical_profiles = {
        (len(pair["input"]), len(pair["input"][0]),
         len({value for row in pair["input"] for value in row}))
        for pair in canonical_pairs(TASK, root=ROOT)
    }
    for difficulty in (None, "easy", "medium", "hard"):
        for sample_index in (0, 4, 8, 12):
            grid = gen.generate(731, sample_index, difficulty=difficulty)
            profile = (
                len(grid),
                len(grid[0]),
                len({value for row in grid for value in row}),
            )
            assert profile in canonical_profiles
            assert gen.self_check(grid) == []


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_default_distribution_has_unique_count_winners_and_two_shortcut_counterexamples(difficulty):
    seen = set()
    shapes = set()
    frame_counts = set()
    winner_counts = set()
    rival_kinds = set()
    for index in range(64):
        sample_index = index * 7
        grid = gen.generate(900 + index, sample_index, difficulty=difficulty)
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        frames = parse_frames(grid)
        counts = [frame["count"] for frame in frames]
        assert counts.count(max(counts)) == 1
        observation = independent_observation(grid)
        assert observation["rival_kind"] == ("density" if sample_index % 2 == 0 else "area")
        if observation["rival_kind"] == "density":
            assert gen.SEMANTIC_WITNESSES["count_over_density"](grid)
            assert count_output(grid) != density_output(grid)
            assert count_output(grid) == largest_area_output(grid)
        else:
            assert gen.SEMANTIC_WITNESSES["count_over_area"](grid)
            assert count_output(grid) != largest_area_output(grid)
            assert count_output(grid) == density_output(grid)
        assert gen.SEMANTIC_RIVALS["highest_density"](grid) == density_output(grid)
        assert gen.SEMANTIC_RIVALS["largest_area"](grid) == largest_area_output(grid)
        assert gen.observe_overrides(grid) == observation
        seen.add(frozen(grid))
        shapes.add((len(grid), len(grid[0])))
        frame_counts.add(observation["n_frames"])
        winner_counts.add(observation["winner_count"])
        rival_kinds.add(observation["rival_kind"])
    assert len(seen) >= 60
    assert len(shapes) >= 8
    assert frame_counts == {2, 3}
    assert winner_counts == {6, 7, 8}
    assert rival_kinds == {"density", "area"}


def test_generation_is_deterministic_and_call_order_independent():
    expected = gen.generate(412, 111, difficulty="hard")
    for index in range(200):
        gen.generate(index, index * 3, difficulty=("easy", "medium", "hard")[index % 3])
    assert gen.generate(412, 111, difficulty="hard") == expected


def test_public_racket_authority_matches_independent_count_oracle():
    canonical = canonical_pairs(TASK, root=ROOT)
    generated = [gen.generate(728, index, difficulty=("easy", "medium", "hard")[index % 3])
                 for index in range(12)]
    grids = [pair["input"] for pair in canonical] + generated
    report = Catalog(ROOT).apply(TASK, grids, timeout=180, allow_unapproved=True)
    assert report["rule_hash_matches_catalog"] is True
    assert report["executed_rule_hash"] == gen.RULE_HASH
    assert all(row["error"] is None for row in report["results"]), report
    outputs = [row["output"] for row in report["results"]]
    assert outputs[: len(canonical)] == [pair["output"] for pair in canonical]
    assert outputs[len(canonical) :] == [count_output(grid) for grid in generated]


def test_semantic_contract_and_lesson_hook_refute_density_and_area_shortcuts():
    assert gen.CANONICAL_SHORTCUTS["highest_density"] is gen.SEMANTIC_RIVALS["highest_density"]
    assert gen.CANONICAL_SHORTCUTS["largest_area"] is gen.SEMANTIC_RIVALS["largest_area"]
    assert gen.LESSON_COMPETITORS == gen.CANONICAL_SHORTCUTS
    assert gen.WITNESS_RIVALS == {
        "count_over_density": ["highest_density"],
        "count_over_area": ["largest_area"],
    }
    pairs = []
    for index in range(4):
        grid = gen.generate(55, index)
        pairs.append({"input": grid, "output": count_output(grid)})
    for query_index in range(4):
        query = pairs[query_index]
        demos = pairs[:query_index] + pairs[query_index + 1 :]
        assert gen.lesson_identifiable(demos, query) == []


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0, 0], [0]],
        [[True]],
        [[1.0]],
        [[10]],
        [[-1]],
        [[0] * 13 for _ in range(12)],
    ],
)
def test_malformed_inputs_reject_without_crashing(grid):
    assert gen.self_check(grid)
    assert gen.strict_canonical_like(grid)


@pytest.mark.parametrize(
    "mutation",
    ["erase_border", "stray_foreground", "mixed_interior_colors", "fill_frame_hole"],
)
def test_structural_mutations_are_rejected(mutation):
    grid = deepcopy(gen.generate(31, 8, n_frames=3))
    frames = parse_frames(grid)
    r0, c0, r1, c1 = frames[0]["bbox"]
    if mutation == "erase_border":
        grid[r0][c0] = 0
    elif mutation == "stray_foreground":
        for r, row in enumerate(grid):
            for c, value in enumerate(row):
                if value == 0 and not any(fr["bbox"][0] < r < fr["bbox"][2]
                                          and fr["bbox"][1] < c < fr["bbox"][3]
                                          for fr in frames):
                    grid[r][c] = 9
                    break
            else:
                continue
            break
    elif mutation == "mixed_interior_colors":
        for r in range(r0 + 1, r1):
            for c in range(c0 + 1, c1):
                if grid[r][c] != 0:
                    grid[r][c] = 9 if grid[r][c] != 9 else 8
                    break
            else:
                continue
            break
    elif mutation == "fill_frame_hole":
        grid[r0 + 1][c0 + 1] = 1
    else:
        raise AssertionError(mutation)
    assert gen.self_check(grid)
    assert gen.strict_canonical_like(grid)
