"""Regression and semantic-contract tests for generator 4b57f748d763."""
from __future__ import annotations

from collections import Counter
import copy
import hashlib
import importlib
import json
from pathlib import Path
import random

import pytest


TASK_ID = "4b57f748d763"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
ROOT = Path(__file__).resolve().parents[1]


def _canonical_row():
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError(f"missing canonical row {TASK_ID}")


def _normalized_hash(source):
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def test_all_canonical_pairs_rule_and_linked_profiles():
    row = _canonical_row()
    pairs = [*row["train"], *row["test"]]
    assert len(pairs) == 5
    observed = set()
    for pair in pairs:
        source = pair["input"]
        assert GEN.self_check(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert GEN.strict_canonical_like(source) == []
        profile = GEN.observe_overrides(source)["scene_profile"]
        assert profile in GEN.PUBLIC_PROFILES
        observed.add(profile)
    assert observed == set(GEN.PUBLIC_PROFILES)


def test_forced_profiles_are_exact_and_valid_in_every_band():
    for band in ("easy", "medium", "hard"):
        for profile in GEN.SCENE_PROFILES:
            for seed in range(30):
                grid = GEN.generate(
                    seed,
                    seed * 17 + 3,
                    difficulty=band,
                    scene_profile=profile,
                )
                assert GEN.observe_overrides(grid) == {"scene_profile": profile}
                assert GEN.self_check(
                    grid, meta={"overrides": {"scene_profile": profile}}
                ) == []


def test_default_and_disjoint_stability_censuses_cover_every_profile():
    for band in ("easy", "medium", "hard"):
        for seed_offset, index_offset in ((0, 0), (100_000, 50_000)):
            counts = Counter()
            for i in range(200):
                grid = GEN.generate(
                    seed_offset + i,
                    index_offset + i * 19 + 1,
                    difficulty=band,
                )
                assert GEN.self_check(grid) == []
                counts[GEN.observe_overrides(grid)["scene_profile"]] += 1
            assert set(counts) == set(GEN.SCENE_PROFILES)
            strict = sum(counts[name] for name in GEN.PUBLIC_PROFILES)
            assert strict >= 20


def test_python_oracle_paints_only_each_rectangle_border():
    for band in ("easy", "medium", "hard"):
        for seed in range(80):
            source = GEN.generate(seed + 7000, seed, difficulty=band)
            before = copy.deepcopy(source)
            output = GEN.rule_mirror(source)
            info = GEN._analysis(source)
            assert source == before
            assert output is not source
            expected = set()
            for item in info["rectangles"]:
                r0, c0, r1, c1 = item["box"]
                for r in range(r0, r1 + 1):
                    for c in range(c0, c1 + 1):
                        if r in (r0, r1) or c in (c0, c1):
                            expected.add((r, c, item["color"]))
                        elif source[r][c] == 0:
                            assert output[r][c] == 0
            for r, c, color in expected:
                assert output[r][c] == color


def test_self_check_rejects_nearest_impostors():
    grid = GEN.generate(313, 991, difficulty="hard", scene_profile="interior_two")
    info = GEN._analysis(grid)
    first = info["rectangles"][0]
    cell = first["cells"][0]

    two_corners = copy.deepcopy(grid)
    two_corners[cell[0]][cell[1]] = 0
    four_corners = copy.deepcopy(grid)
    mr, mc = first["missing_point"]
    four_corners[mr][mc] = first["color"]
    invalid_color = copy.deepcopy(grid)
    invalid_color[0][0] = 10
    boolean_color = copy.deepcopy(grid)
    boolean_color[0][0] = True
    ragged = copy.deepcopy(grid)
    ragged[0].pop()
    collinear = [[0] * 12 for _ in range(10)]
    collinear[2][1] = collinear[2][5] = collinear[2][9] = 4
    all_background = [[0] * 12 for _ in range(10)]
    single_rect = [[0] * 12 for _ in range(10)]
    for r, c in ((1, 1), (1, 5), (5, 1)):
        single_rect[r][c] = 6

    for mutation in (
        two_corners,
        four_corners,
        invalid_color,
        boolean_color,
        ragged,
        collinear,
        all_background,
        single_rect,
    ):
        assert GEN.self_check(mutation), mutation


def test_unknown_and_invalid_overrides_fail_closed():
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 2, grid_h=9)
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 2, scene_profile="unknown")
    with pytest.raises(ValueError):
        GEN.generate(1, 2, difficulty="impossible")


def test_determinism_fresh_returns_and_global_rng_isolation():
    random.seed(20260725)
    state = random.getstate()
    first = GEN.generate(97, 103, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(97, 103, difficulty="hard")
    assert first == second
    assert first is not second
    for left, right in zip(first, second):
        assert left is not right
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert first != second


def test_named_competitors_are_refuted_by_every_valid_demo():
    pairs = []
    for i in range(6):
        source = GEN.generate(400 + i, i, difficulty=("easy", "medium", "hard")[i % 3])
        pairs.append({"input": source, "output": GEN.rule_mirror(source)})
    assert GEN.lesson_identifiable(pairs[:3], pairs[3]) == []
    for name, rival in GEN.LESSON_COMPETITORS.items():
        assert any(rival(pair["input"]) != pair["output"] for pair in pairs[:3]), name


def test_rule_authorities_and_hash_pin():
    row = _canonical_row()
    base = json.loads((
        ROOT
        / "data/base/solutions/banks/db2a1cce4e4e/medium_76_recover_rectangles_from_three_corners__4b57f748d763.json"
    ).read_text())
    canonical = row["program_solution"]
    target = base["racket_target"]["target_code"]
    assert canonical == target
    assert GEN.RULE_HASH == _normalized_hash(canonical) == "b6d88eaf0a3f"
    # raw_code is a separate, richer archival search source and is intentionally
    # not rewritten to the canonical minified selected target.
    assert base["racket_target"]["raw_code"] != canonical
