from __future__ import annotations

import copy
import json
import random
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, load_selected_generator


ROOT = find_root(__file__)
gen, SOURCE, SOURCE_SHA256 = load_selected_generator("cf5ccd73cfe5", root=ROOT)


def _canonical_rows():
    rows = []
    with canonical_path(ROOT).open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                rows.append(row)
    return rows


def test_rule_hash_and_all_canonical_inputs_are_accepted():
    assert gen.RULE_HASH == "50b927c3200b"
    rows = _canonical_rows()
    assert {row["source"] for row in rows} == {"training", "augmented"}
    pairs = [
        pair
        for row in rows
        for split in ("train", "test")
        for pair in row.get(split, [])
    ]
    assert len(pairs) == 8
    assert all(gen.self_check(pair["input"]) == [] for pair in pairs)


def test_exact_boundary_and_semantic_overrides_survive_easy_band():
    grid = gen.generate(
        71,
        9,
        difficulty="easy",
        grid_h=26,
        grid_w=26,
        marker_h=3,
        marker_w=2,
        scale_h=4,
        scale_w=3,
        palette_kind="cool",
    )
    facts = gen.observe_overrides(grid)
    assert facts == {
        "grid_h": 26,
        "grid_w": 26,
        "marker_h": 3,
        "marker_w": 2,
        "scale_h": 4,
        "scale_w": 3,
    }
    assert gen.self_check(grid, difficulty="easy") == []


def test_small_dimension_boundaries_are_exact_when_feasible():
    for band in ("easy", "medium", "hard"):
        grid = gen.generate(13, 4, difficulty=band, grid_h=8, grid_w=8)
        assert (len(grid), len(grid[0])) == (8, 8)
        assert gen.self_check(grid, difficulty=band) == []


def test_jointly_ambiguous_one_by_one_marker_rejects_loudly():
    with pytest.raises(ValueError, match="incompatible exact override combination"):
        gen.generate(1, 0, marker_h=1, marker_w=1)


def test_helpful_texture_alias_changes_the_palette_distribution():
    warm = [gen.generate(seed, 0, texture="warm") for seed in range(12)]
    cool = [gen.generate(seed, 0, texture="cool") for seed in range(12)]
    assert any(left != right for left, right in zip(warm, cool))
    for grid in warm + cool:
        assert gen.self_check(grid) == []


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(99117)
    before = random.getstate()
    first = gen.generate(101, 17, difficulty="hard")
    after = random.getstate()
    second = gen.generate(101, 17, difficulty="hard")
    assert first == second
    assert first is not second
    assert first[0] is not second[0]
    assert before == after

    damaged = copy.deepcopy(first)
    damaged[0][0] = (damaged[0][0] + 1) % 10
    assert gen.generate(101, 17, difficulty="hard") == first


def test_self_check_rejects_targeted_structural_impostors():
    grid = gen.generate(
        211,
        5,
        marker_h=3,
        marker_w=3,
        scale_h=2,
        scale_w=2,
        grid_h=18,
        grid_w=18,
    )
    facts, errors = gen._analyze(grid)
    assert not errors

    all_background = [[0 for _ in row] for row in grid]
    full_one_color = [[1 for _ in row] for row in grid]

    broken_frame = copy.deepcopy(grid)
    fr1, fc1, _fr2, _fc2 = facts["frame_bbox"]
    broken_frame[fr1][fc1] = 0

    marker_inside = copy.deepcopy(grid)
    marker_inside[fr1 + 1][fc1 + 1] = facts["marker_color"]

    third_marker_color = copy.deepcopy(grid)
    mr1, mc1, mr2, mc2 = facts["marker_bbox"]
    marker_cell = next(
        (r, c)
        for r in range(mr1, mr2 + 1)
        for c in range(mc1, mc2 + 1)
        if third_marker_color[r][c] == facts["marker_color"]
    )
    replacement = next(
        color
        for color in range(1, 10)
        if color not in (facts["frame_color"], facts["marker_color"])
    )
    third_marker_color[marker_cell[0]][marker_cell[1]] = replacement

    impostors = {
        "all_background": all_background,
        "full_one_color": full_one_color,
        "broken_frame": broken_frame,
        "marker_inside": marker_inside,
        "third_marker_color": third_marker_color,
    }
    failures = {name: gen.self_check(candidate) for name, candidate in impostors.items()}
    assert all(messages for messages in failures.values()), failures


def test_task_local_authorities_are_exactly_synchronized_to_canonical():
    canonical = _canonical_rows()[0]["program_solution"]
    data_root = canonical_path(ROOT).parent.parent
    paths = [data_root / "base/solutions/augmented/6b9890af__4284b17d920f.json",
             data_root / "base/solutions/training/6b9890af__cf5ccd73cfe5.json"]
    for path in paths:
        row = json.loads(path.read_text())
        target = row["racket_target"]
        # Archive formatting is historical; selected execution text is exact.
        assert " ".join(target["raw_code"].split()) == " ".join(canonical.split())
        assert target["target_code"] == canonical
        assert target["rule_hash"] == gen.RULE_HASH
