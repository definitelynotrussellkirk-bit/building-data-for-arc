"""Focused regressions for the db89dc496d45 crop-largest curriculum."""
from __future__ import annotations

import copy
import importlib.util
import os
from pathlib import Path
import random
import sys

import pytest

# Portable bootstrap: packet tree and staged runtime both expose reviewer_support.
for ancestor in Path(__file__).resolve().parents:
    runtime = ancestor / "shared" / "runtime"
    if (runtime / "reviewer_support.py").is_file():
        sys.path.insert(0, str(runtime))
        break
    if (ancestor / "reviewer_support.py").is_file():
        sys.path.insert(0, str(ancestor))
        break

from reviewer_support import canonical_pairs, find_root  # noqa: E402

TASK_ID = "db89dc496d45"
ROOT = find_root(__file__)
DEFAULT_GENERATOR = ROOT / "generators" / TASK_ID / "generator.py"
if not DEFAULT_GENERATOR.is_file():
    DEFAULT_GENERATOR = (
        ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"
    )
GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", DEFAULT_GENERATOR))
SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", GENERATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
gen = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = gen
SPEC.loader.exec_module(gen)


def _pairs() -> list[dict]:
    return canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for start_r in range(h):
        for start_c in range(w):
            color = grid[start_r][start_c]
            if color == 0 or (start_r, start_c) in seen:
                continue
            stack = [(start_r, start_c)]
            seen.add((start_r, start_c))
            cells = set()
            while stack:
                r, c = stack.pop()
                cells.add((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
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


def _crop_largest(grid):
    components = _components(grid)
    sizes = [len(cells) for _, cells in components]
    assert sizes and sizes.count(max(sizes)) == 1
    _, cells = max(components, key=lambda item: len(item[1]))
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    return [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]


def _most_frequent_color_crop(grid):
    colors = sorted({value for row in grid for value in row if value})
    counts = {color: sum(value == color for row in grid for value in row) for color in colors}
    color = max(colors, key=lambda value: (counts[value], -value))
    cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    ]
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    return [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]


def test_public_contract_and_all_canonical_pairs():
    assert gen.RULE_HASH == "56bd46ef5a5e"
    assert gen.VERSION == "3.1.2"
    assert gen.EXAMPLES_NEEDED == 4
    assert gen.MIN_STRICT_FRAC == 1.0
    assert tuple(gen.SCHEDULE_PROFILES) == (
        "canonical_9x11",
        "canonical_10x12",
        "canonical_11x13",
        "canonical_12x12",
        "expanded_14x16",
        "expanded_16x18",
    )
    assert set(gen.AXES) == {"scene_profile"}
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == ()

    pairs = _pairs()
    assert len(pairs) == 5
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        assert gen.self_check(source) == []
        assert gen.strict_canonical_like(source) == []
        assert _crop_largest(source) == pair["output"]
        assert gen.rule_mirror(source) == pair["output"]
        assert source == pair["input"]


def test_declared_canonical_shortcut_really_fits_every_canonical_pair():
    expected = {
        "most_frequent_color",
        "largest_component_of_most_frequent_color",
        "second_color_when_top_disconnected",
        "largest_single_component_color",
    }
    assert set(gen.CANONICAL_SHORTCUTS) == expected
    assert set(gen.SEMANTIC_RIVALS) == expected
    assert set(gen.LESSON_COMPETITORS) == expected
    for pair in _pairs():
        assert _most_frequent_color_crop(pair["input"]) == pair["output"]
        for rival in gen.CANONICAL_SHORTCUTS.values():
            assert rival(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "profile",
    (
        "canonical_9x11",
        "canonical_10x12",
        "canonical_11x13",
        "canonical_12x12",
        "expanded_14x16",
        "expanded_16x18",
    ),
)
def test_scene_profile_override_is_exact_observable_and_lawful(profile, band):
    grid = gen.generate(8128, 37, difficulty=band, scene_profile=profile)
    assert gen.self_check(grid) == []
    assert gen.strict_canonical_like(grid) == []
    assert gen.observe_overrides(grid) == {"scene_profile": profile}
    assert grid == gen.generate(8128, 37, difficulty=band, scene_profile=profile)


@pytest.mark.parametrize(
    "overrides",
    (
        {"typo_axis": "canonical_9x11"},
        {"scene_profile": "unknown"},
        {"scene_profile": 1},
        {"scene_profile": None},
    ),
)
def test_unknown_and_invalid_overrides_fail_loudly(overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **overrides)


def test_schedule_is_public_deterministic_and_covers_every_profile():
    for band in (None, "easy", "medium", "hard"):
        for seed in (0, 7, 811):
            observed = [gen.schedule_profile(seed, index, band) for index in range(12)]
            assert observed == list(gen.SCHEDULE_PROFILES) * 2


def test_each_scene_profile_supports_both_semantic_witness_profiles():
    distractor_witness = "split_distractor_color_dominates_by_total"
    target_witness = "split_target_color_dominates_by_total"
    for sample_index, profile in enumerate(gen.SCHEDULE_PROFILES):
        fired = set()
        for seed in (20_000, 20_008):
            grid = gen.generate(seed, sample_index, difficulty="medium")
            assert gen.observe_overrides(grid) == {"scene_profile": profile}
            names = {
                name for name, predicate in gen.SEMANTIC_WITNESSES.items()
                if predicate(grid)
            }
            assert len(names) == 1
            fired.update(names)
        assert fired == {distractor_witness, target_witness}


def test_each_scene_profile_supports_every_target_size_across_seeds():
    expected_sizes = set(range(5, 13))
    for sample_index, profile in enumerate(gen.SCHEDULE_PROFILES):
        sizes = set()
        for seed in range(8):
            grid = gen.generate(seed, sample_index, difficulty="medium")
            assert gen.observe_overrides(grid) == {"scene_profile": profile}
            components = _components(grid)
            sizes.add(max(len(cells) for _, cells in components))
        assert sizes == expected_sizes


def test_every_default_draw_is_a_connected_component_counterexample():
    distractor_witness = "split_distractor_color_dominates_by_total"
    target_witness = "split_target_color_dominates_by_total"
    expected_rivals = {
        "most_frequent_color",
        "largest_component_of_most_frequent_color",
        "second_color_when_top_disconnected",
        "largest_single_component_color",
    }
    assert set(gen.SEMANTIC_WITNESSES) == {
        distractor_witness,
        target_witness,
    }
    assert gen.WITNESS_RIVALS == {
        distractor_witness: [
            "most_frequent_color",
            "largest_component_of_most_frequent_color",
        ],
        target_witness: [
            "most_frequent_color",
            "second_color_when_top_disconnected",
            "largest_single_component_color",
        ],
    }
    assert set(gen.SEMANTIC_RIVALS) == expected_rivals

    target_sizes = set()
    target_regions = set()
    profile_hits = {distractor_witness: 0, target_witness: 0}
    rival_mismatches = {name: 0 for name in expected_rivals}
    for band_index, band in enumerate((None, "easy", "medium", "hard")):
        seed = 50_000 + 100 * band_index
        for index in range(36):
            grid = gen.generate(seed, index, difficulty=band)
            assert gen.self_check(grid) == []
            assert gen.strict_canonical_like(grid) == []
            fired = {
                name for name, predicate in gen.SEMANTIC_WITNESSES.items()
                if predicate(grid)
            }
            expected_fired = {
                target_witness
                if ((seed // 8) + index) % 2 == 1
                else distractor_witness
            }
            assert fired == expected_fired
            profile_hits[next(iter(fired))] += 1
            intended = _crop_largest(grid)
            assert gen.rule_mirror(grid) == intended
            assert _most_frequent_color_crop(grid) != intended
            assert gen.SEMANTIC_RIVALS["most_frequent_color"](grid) != intended
            for name, rival in gen.SEMANTIC_RIVALS.items():
                rival_mismatches[name] += rival(grid) != intended

            components = _components(grid)
            target = max(components, key=lambda item: len(item[1]))
            target_sizes.add(len(target[1]))
            mean_r = sum(r for r, _ in target[1]) / len(target[1])
            mean_c = sum(c for _, c in target[1]) / len(target[1])
            target_regions.add(
                (mean_r >= len(grid) / 2, mean_c >= len(grid[0]) / 2)
            )

    assert target_sizes == set(range(5, 13))
    assert target_regions == {(False, False), (False, True), (True, False), (True, True)}
    assert profile_hits == {distractor_witness: 72, target_witness: 72}
    assert all(count > 0 for count in rival_mismatches.values())


def test_generated_target_crop_is_never_a_solid_rectangle():
    # Regression for defect-lint: medium seed/sample 5 previously produced a
    # solid 2x5 target crop, hiding the shape-preserving part of extraction.
    for band in ("easy", "medium", "hard"):
        for seed in range(1, 101):
            grid = gen.generate(seed, seed, difficulty=band)
            output = gen.rule_mirror(grid)
            palette = {value for row in output for value in row}
            assert 0 in palette and len(palette) == 2, (band, seed, output)


def test_every_rotated_lesson_refutes_every_declared_canonical_shortcut():
    for band in ("easy", "medium", "hard"):
        for start in range(12):
            pairs = []
            for offset in range(gen.EXAMPLES_NEEDED + 1):
                grid = gen.generate(91_000 + start, start + offset, difficulty=band)
                pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
            for query_index in range(len(pairs)):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                assert len(demos) == gen.EXAMPLES_NEEDED
                for name, rival in gen.LESSON_COMPETITORS.items():
                    assert any(
                        rival(pair["input"]) != pair["output"] for pair in demos
                    ), (band, start, query_index, name)


def test_determinism_freshness_and_global_rng_purity():
    random.seed(90210)
    state = random.getstate()
    first = gen.generate(9, 27, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(9, 27, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert second == gen.generate(9, 27, difficulty="hard")
    assert second != gen.generate(10, 27, difficulty="hard")
    assert second != gen.generate(9, 28, difficulty="hard")


def test_self_check_is_diagnostic_non_mutating_and_total_on_bad_inputs():
    malformed = [
        None,
        [],
        [1, 2],
        [[]],
        [[0, 0], [0]],
        [[0, "1"]],
        [[0, True]],
        [[0, 10]],
        [[0, -1]],
        [[0, 0], [0, 0]],
    ]
    for value in malformed:
        assert gen.self_check(value), value
        assert gen.strict_canonical_like(value), value

    grid = gen.generate(33, 44, difficulty="medium")
    before = copy.deepcopy(grid)
    gen.self_check(grid)
    gen.strict_canonical_like(grid)
    gen.observe_overrides(grid)
    gen.rule_mirror(grid)
    for predicate in gen.SEMANTIC_WITNESSES.values():
        predicate(grid)
    for rival in gen.SEMANTIC_RIVALS.values():
        rival(grid)
    assert grid == before
