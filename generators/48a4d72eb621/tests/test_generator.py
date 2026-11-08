from __future__ import annotations

from collections import Counter

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "48a4d72eb621"
ROOT = find_root(__file__)
GEN, GENERATOR_SOURCE, GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def _facts(grid: list[list[int]]) -> dict[str, int]:
    counts = Counter(value for row in grid for value in row if value != 0)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_colors": len(counts),
    }


def test_canonical_inputs_are_lawful() -> None:
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)
    assert len(pairs) == 5
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []


def test_exact_axes_are_observable_and_bad_keys_fail_loudly() -> None:
    assert GEN.RULE_HASH == "ea16ba808d09"
    assert set(GEN.AXES) == {"grid_h", "grid_w", "n_colors"}
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []

    requested = {"grid_h": 5, "grid_w": 12, "n_colors": 5}
    for difficulty in (None, "easy", "medium", "hard"):
        grid = GEN.generate(123, 7, difficulty=difficulty, **requested)
        assert GEN.self_check(grid) == []
        assert _facts(grid) == requested
        assert GEN.observe_overrides(grid) == requested

    for key, value in (
        ("grid_h", True),
        ("grid_w", 6.0),
        ("n_colors", "3"),
        ("n_colors", 1),
        ("n_colors", 6),
        ("unknown_axis", 1),
    ):
        with pytest.raises((TypeError, ValueError)):
            GEN.generate(0, 0, **{key: value})


def _answer(grid: list[list[int]]) -> list[list[int]]:
    values = sorted(value for row in grid for value in row if value != 0)
    return [values or [0]]


def _pair(grid: list[list[int]]) -> dict[str, list[list[int]]]:
    return {"input": grid, "output": _answer(grid)}


def test_sliding_lessons_refute_declared_rivals_under_every_query_rotation() -> None:
    expected_rivals = {"cap_two", "drop_five", "distinct_only", "row_major"}
    assert set(GEN.SEMANTIC_RIVALS) == expected_rivals
    assert set(GEN.LESSON_COMPETITORS) == expected_rivals

    for difficulty in ("easy", "medium", "hard"):
        for start in range(8):
            grids = [GEN.generate(10_000 + start, start + offset, difficulty=difficulty) for offset in range(4)]
            assert sum(GEN.SEMANTIC_WITNESSES["count_three"](grid) for grid in grids) >= 2
            assert sum(GEN.SEMANTIC_WITNESSES["color_five"](grid) for grid in grids) >= 2
            assert all(GEN.SEMANTIC_WITNESSES["duplicate_count"](grid) for grid in grids)
            assert all(GEN.SEMANTIC_WITNESSES["sorting_matters"](grid) for grid in grids)

            pairs = [_pair(grid) for grid in grids]
            for query_index in range(4):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                assert GEN.lesson_identifiable(demos, pairs[query_index]) == []


def test_semantic_witnesses_are_real_counterexamples() -> None:
    grids = [GEN.generate(22_222, index, difficulty="medium") for index in range(4)]
    witness_to_rival = {
        "count_three": "cap_two",
        "color_five": "drop_five",
        "duplicate_count": "distinct_only",
        "sorting_matters": "row_major",
    }
    for witness_name, rival_name in witness_to_rival.items():
        candidates = [grid for grid in grids if GEN.SEMANTIC_WITNESSES[witness_name](grid)]
        assert candidates, witness_name
        assert any(GEN.SEMANTIC_RIVALS[rival_name](grid) != _answer(grid) for grid in candidates)


def test_strict_profile_accepts_canonical_and_has_default_support() -> None:
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)
    assert all(GEN.strict_canonical_like(pair["input"]) == [] for pair in pairs)
    for difficulty in ("easy", "medium", "hard"):
        strict = sum(
            GEN.strict_canonical_like(GEN.generate(33_000 + index, index, difficulty=difficulty)) == []
            for index in range(40)
        )
        assert strict >= 8


@pytest.mark.parametrize(
    "kwargs",
    [
        {"seed": True, "sample_index": 0},
        {"seed": 1.0, "sample_index": 0},
        {"seed": "1", "sample_index": 0},
        {"seed": 1, "sample_index": True},
        {"seed": 1, "sample_index": -1},
        {"seed": 1, "sample_index": 0, "difficulty": 0},
        {"seed": 1, "sample_index": 0, "difficulty": "invalid"},
    ],
)
def test_invalid_call_scalars_fail_loudly(kwargs: dict) -> None:
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(**kwargs)


def test_difficulty_bands_change_the_sampled_population() -> None:
    triples = []
    for index in range(24):
        grids = tuple(GEN.generate(44_000 + index, index, difficulty=band) for band in ("easy", "medium", "hard"))
        assert all(GEN.self_check(grid) == [] for grid in grids)
        triples.append(grids)
    assert any(len({repr(grid) for grid in grids}) > 1 for grids in triples)


def test_retained_minimal_counterexample_refutes_every_declared_rival() -> None:
    import json
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / "counterexamples" / "all-rivals-minimal.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    grid = payload["input"]
    expected = payload["expected_output"]
    assert GEN.self_check(grid) == []
    assert _answer(grid) == expected
    assert payload["rule_hash"] == GEN.RULE_HASH
    assert set(payload["rival_outputs"]) == set(GEN.SEMANTIC_RIVALS)
    for name, output in payload["rival_outputs"].items():
        assert GEN.SEMANTIC_RIVALS[name](grid) == output
        assert output != expected
