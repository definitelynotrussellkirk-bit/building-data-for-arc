from __future__ import annotations

import copy
import importlib.util
import json
import random
import sys
from collections import Counter
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
RUNTIME_ROOT = REPO_ROOT / "shared" / "runtime"
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

MODULE_PATH = REPO_ROOT / "generators" / "f2818d6c50ce" / "generator.py"
SPEC = importlib.util.spec_from_file_location("review_generator_f2818d6c50ce", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def _canonical_pairs() -> list[dict]:
    path = REPO_ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != GEN.TASK_ID:
                continue
            train = row["train"] if isinstance(row["train"], list) else [row["train"]]
            test = row["test"] if isinstance(row["test"], list) else [row["test"]]
            return copy.deepcopy(train + test)
    raise AssertionError(f"canonical task {GEN.TASK_ID} not found")


def _reference_output(grid: list[list[int]]) -> list[list[int]]:
    points: dict[int, list[tuple[int, int]]] = {}
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value != 0:
                points.setdefault(value, []).append((row, col))
    lengths = sorted(
        max(abs(a[0] - b[0]), abs(a[1] - b[1])) + 1
        for cells in points.values()
        if len(cells) == 2
        for a, b in [cells]
    )
    assert lengths
    width = max(lengths)
    return [[8] * length + [0] * (width - length) for length in lengths]


def test_declares_rule_authority_and_accepts_all_canonical_inputs():
    assert GEN.RULE_HASH == "216362042c61"
    for pair in _canonical_pairs():
        grid = pair["input"]
        assert GEN.self_check(copy.deepcopy(grid)) == []
        assert GEN.strict_canonical_like(copy.deepcopy(grid)) == []
        assert GEN._expected_output(copy.deepcopy(grid)) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_exact_override_is_constructive_observable_and_band_independent(band):
    cases = (
        {"grid_h": 8, "grid_w": 8, "n_pairs": 6, "n_distractor_colors": 2},
        {"grid_h": 22, "grid_w": 22, "n_pairs": 1, "n_distractor_colors": 0},
        {"grid_h": 10, "grid_w": 12, "n_pairs": 3, "n_distractor_colors": 1},
    )
    for index, overrides in enumerate(cases):
        grid = GEN.generate(100 + index, 70 + index, difficulty=band, **overrides)
        assert GEN.self_check(grid, difficulty=band) == []
        observed = GEN.observe_overrides(grid)
        assert {name: observed[name] for name in overrides} == overrides


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("grid_h", 7),
        ("grid_h", 23),
        ("grid_w", 7),
        ("grid_w", 23),
        ("n_pairs", 0),
        ("n_pairs", 7),
        ("n_distractor_colors", -1),
        ("n_distractor_colors", 3),
        ("grid_h", True),
        ("n_pairs", 2.5),
        ("n_distractor_colors", "1"),
        ("typo_axis", 1),
    ],
)
def test_invalid_or_unknown_overrides_fail_loudly(name, value):
    with pytest.raises(ValueError):
        GEN.generate(1, 2, **{name: value})


def test_default_distribution_is_lawful_canonical_anchored_and_semantically_useful():
    for band in ("easy", "medium", "hard"):
        strict_hits = 0
        witness_hits = Counter()
        shapes: set[tuple[int, int]] = set()
        pair_counts: set[int] = set()
        distractor_counts: set[int] = set()
        for seed in range(120):
            sample_index = seed * 11 + 5
            grid = GEN.generate(seed, sample_index, difficulty=band)
            assert GEN.self_check(grid, difficulty=band) == []
            strict_hits += GEN.strict_canonical_like(grid) == []
            observed = GEN.observe_overrides(grid)
            shapes.add((observed["grid_h"], observed["grid_w"]))
            pair_counts.add(observed["n_pairs"])
            distractor_counts.add(observed["n_distractor_colors"])
            for name, witness in GEN.SEMANTIC_WITNESSES.items():
                witness_hits[name] += bool(witness(grid))

        assert strict_hits >= 30, (band, strict_hits)
        assert len(shapes) >= 8, (band, shapes)
        assert pair_counts == set(range(1, 7)), (band, pair_counts)
        assert distractor_counts == {0, 1, 2}, (band, distractor_counts)
        assert all(witness_hits[name] >= 20 for name in GEN.SEMANTIC_WITNESSES), (
            band,
            witness_hits,
        )


def test_distractor_colors_are_lawful_and_do_not_become_output_bars():
    grid = GEN.generate(
        701,
        33,
        grid_h=10,
        grid_w=12,
        n_pairs=3,
        n_distractor_colors=2,
    )
    counts = Counter(value for row in grid for value in row if value != 0)
    assert sorted(counts.values()).count(2) == 3
    assert sorted(counts.values()).count(1) + sum(v >= 3 for v in counts.values()) == 2
    assert GEN.self_check(grid) == []
    assert GEN._expected_output(grid) == _reference_output(grid)
    assert GEN.SEMANTIC_RIVALS["all_nonzero_colors_are_pairs"](grid) != _reference_output(grid)


def test_named_canonical_shortcut_fits_public_pairs_but_generated_witnesses_refute_it():
    shortcut = GEN.CANONICAL_SHORTCUTS["all_nonzero_colors_are_pairs"]
    assert all(shortcut(pair["input"]) == pair["output"] for pair in _canonical_pairs())

    witnesses = [
        GEN.generate(900 + index, index, difficulty="medium")
        for index in range(18)
        if GEN.schedule_profile(900 + index, index, difficulty="medium") != "canonical"
    ]
    assert witnesses
    assert all(GEN.SEMANTIC_WITNESSES["ignore_nonpairs"](grid) for grid in witnesses)
    assert any(shortcut(grid) != _reference_output(grid) for grid in witnesses)


def test_every_three_consecutive_examples_refute_declared_lesson_competitors():
    for band in ("easy", "medium", "hard"):
        for start in range(12):
            demos = []
            for offset in range(GEN.EXAMPLES_NEEDED):
                grid = GEN.generate(1234 + start, start + offset, difficulty=band)
                demos.append({"input": grid, "output": _reference_output(grid)})
            query_grid = GEN.generate(1234 + start, start + GEN.EXAMPLES_NEEDED, difficulty=band)
            query = {"input": query_grid, "output": _reference_output(query_grid)}
            assert GEN.lesson_identifiable(demos, query) == []
            for competitor in GEN.LESSON_COMPETITORS.values():
                assert any(competitor(demo["input"]) != demo["output"] for demo in demos)


def test_replay_is_deterministic_fresh_and_global_rng_pure():
    random.seed(90210)
    state = random.getstate()
    first = GEN.generate(23, 11, difficulty="medium")
    assert random.getstate() == state
    second = GEN.generate(23, 11, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 8
    assert GEN.generate(23, 11, difficulty="medium") == second


def test_equal_span_profile_never_makes_a_multirow_all_solid_output():
    grid = GEN.generate(
        44,
        2,  # mixed_distractors schedule branch
        grid_h=12,
        grid_w=18,
        n_pairs=2,
        n_distractor_colors=2,
    )
    output = GEN._expected_output(grid)
    assert len(output) == 2
    assert any(0 in row for row in output)
