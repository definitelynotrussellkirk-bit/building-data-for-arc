"""Portable regressions for the ce3c6d414140 generator repair."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import random

import pytest

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TASK_ID = "ce3c6d414140"
ROOT = find_root(__file__)
gen, SOURCE_PATH, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
BANDS = (None, "easy", "medium", "hard")
PROFILES = {
    "small_one": (8, 9, 1),
    "square_one": (10, 10, 1),
    "tall_two": (14, 9, 2),
}
DIRS8 = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != (0, 0)
)


def _components(grid):
    """Independent same-color 8-connected component reader."""
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            seen.add((r, c))
            stack = [(r, c)]
            cells = set()
            while stack:
                rr, cc = stack.pop()
                cells.add((rr, cc))
                for dr, dc in DIRS8:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append((color, cells))
    return result


def _canonical_rule_hash():
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        source = next(
            row["program_solution"]
            for row in map(json.loads, handle)
            if row.get("task_id") == TASK_ID
        )
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def test_rule_pin_python_mirror_and_validation_match_all_canonical_pairs():
    assert gen.RULE_HASH == _canonical_rule_hash() == "e5b989176419"
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == 3
    for pair in pairs:
        original = deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_only_advertised_profile_control_is_exact_in_every_band():
    assert set(gen.AXES) == {"profile"}
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    for band in BANDS:
        for profile, (height, width, n_objects) in PROFILES.items():
            for sample_index in (0, 7, 19):
                grid = gen.generate(
                    103,
                    sample_index,
                    difficulty=band,
                    profile=profile,
                )
                assert (len(grid), len(grid[0])) == (height, width)
                assert len(_components(grid)) == n_objects
                assert gen.observe_overrides(grid) == {"profile": profile}
                assert gen.self_check(grid) == []


def test_default_distribution_stays_on_canonical_profiles_and_never_noops():
    canonical_signatures = set(PROFILES.values())
    seen_profiles = {band: set() for band in BANDS}
    for band in BANDS:
        for sample_index in range(60):
            grid = gen.generate(17, sample_index, difficulty=band)
            observed = gen.observe_overrides(grid)["profile"]
            seen_profiles[band].add(observed)
            signature = (len(grid), len(grid[0]), len(_components(grid)))
            assert signature in canonical_signatures
            assert gen.self_check(grid) == []
            assert gen.rule_mirror(grid) != grid
    assert all(values == set(PROFILES) for values in seen_profiles.values())


def test_blank_grid_regression_is_fixed_for_original_replay_coordinates():
    grid = gen.generate(17, 17, difficulty="easy")
    assert any(value for row in grid for value in row)
    assert gen.self_check(grid) == []
    assert gen.rule_mirror(grid) != grid


def test_generated_objects_are_monochrome_parallelograms_and_8_separated():
    for profile, (_, _, n_objects) in PROFILES.items():
        for sample_index in range(24):
            grid = gen.generate(701, sample_index, profile=profile)
            components = _components(grid)
            assert len(components) == n_objects
            assert len({color for color, _ in components}) == n_objects
            for _, cells in components:
                rows = [r for r, _ in cells]
                cols = [c for _, c in cells]
                oh = max(rows) - min(rows) + 1
                bbox_w = max(cols) - min(cols) + 1
                ow = bbox_w - oh + 2
                normalized = {(r - min(rows), c - min(cols)) for r, c in cells}
                assert normalized == gen._parallelogram(oh, ow)
            for index, (_, left) in enumerate(components):
                for _, right in components[index + 1 :]:
                    assert all(
                        max(abs(r1 - r2), abs(c1 - c2)) >= 2
                        for r1, c1 in left
                        for r2, c2 in right
                    )


def test_invalid_requests_and_controls_fail_loudly():
    for bad in (True, 1.0, "1", None, [], {}):
        with pytest.raises((TypeError, ValueError)):
            gen.generate(bad, 0)
    for bad in (True, 1.0, "1", None, -1, [], {}):
        with pytest.raises((TypeError, ValueError)):
            gen.generate(1, bad)
    for bad in (True, 0, 0.5, "extreme", "", [], {}):
        with pytest.raises((TypeError, ValueError)):
            gen.generate(1, 0, difficulty=bad)
    for bad in (True, 1, "unknown", "", [], {}):
        with pytest.raises((TypeError, ValueError)):
            gen.generate(1, 0, profile=bad)
    with pytest.raises((TypeError, ValueError, KeyError)):
        gen.generate(1, 0, typo_profile="small_one")
    # None retains the package-wide no-override convention.
    assert gen.generate(1, 0, profile=None) == gen.generate(1, 0)


def test_self_check_rejects_malformed_and_structural_impostors_without_mutation():
    malformed = [
        None,
        3,
        "00",
        [],
        [[]],
        [[0], [0, 1]],
        [[True]],
        [[10]],
        [[-1]],
        [[1.0]],
        [["1"]],
        [[0] * 9 for _ in range(8)],
    ]
    solid = [[0] * 9 for _ in range(8)]
    for r in range(3):
        for c in range(4):
            solid[r][c] = 2
    malformed.append(solid)
    broken = gen.generate(5, 2, profile="small_one")
    first = next(cells for _, cells in _components(broken))
    r, c = next(iter(first))
    broken[r][c] = 0
    malformed.append(broken)
    for grid in malformed:
        original = deepcopy(grid)
        reasons = gen.self_check(grid)
        assert isinstance(reasons, list) and reasons, repr(grid)
        assert all(isinstance(reason, str) and reason for reason in reasons)
        assert grid == original


def test_semantic_witnesses_refute_each_named_partial_rule():
    for profile in PROFILES:
        grid = gen.generate(31, 4, profile=profile)
        truth = gen.rule_mirror(grid)
        assert gen.SEMANTIC_WITNESSES["right_edge_stays"](grid)
        assert gen.SEMANTIC_WITNESSES["bottom_edge_stays"](grid)
        assert gen.SEMANTIC_RIVALS["bottom_only"](grid) != truth
        assert gen.SEMANTIC_RIVALS["right_only"](grid) != truth
        assert gen.LESSON_COMPETITORS["shift_everything"](grid) != truth


def test_lesson_identifiability_scores_declared_competitors_against_labels():
    lesson = []
    for sample_index in range(gen.EXAMPLES_NEEDED + 1):
        inp = gen.generate(911, sample_index, difficulty="medium")
        lesson.append({"input": inp, "output": gen.rule_mirror(inp)})
    assert gen.lesson_identifiable(lesson[:-1], lesson[-1]) == []


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    random.seed(120_901)
    before = random.getstate()
    first = gen.generate(444, 9, difficulty="hard")
    after = random.getstate()
    second = gen.generate(444, 9, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert first[0] is not second[0]
    old = second[0][0]
    first[0][0] = 9 if old != 9 else 8
    assert first != second


def test_parametric_shift_distance_prototype_is_episode_consistent_and_distinguishable():
    import importlib.util

    path = ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"
    spec = importlib.util.spec_from_file_location("ce3_parametric_prototype", path)
    prototype = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(prototype)

    assert prototype.ALLOWED_SHIFT_DISTANCES == (1, 2)
    sources = {distance: prototype.rule_source(distance) for distance in (1, 2)}
    assert sources[1] != sources[2]
    assert all(source.startswith("(rule!") for source in sources.values())

    for distance in (1, 2):
        episode = prototype.build_episode(41 + distance, shift_distance=distance)
        assert episode["parameter"] == {"shift_distance": distance}
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 1
        for pair in episode["train"] + episode["test"]:
            assert pair["output"] == prototype.python_mirror(
                pair["input"], shift_distance=distance
            )
            rival = 2 if distance == 1 else 1
            assert prototype.python_mirror(
                pair["input"], shift_distance=rival
            ) != pair["output"]
