from __future__ import annotations

import copy
import importlib.util
import os
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root


TASK_ID = "105b239cb812"
RULE_HASH = "aa699e35aade"
TRANSFORMS = ("cw", "180", "ccw", "lr", "ud", "transpose")
SHAPE_KINDS = ("tetromino", "pentomino", "six_cell")
ROOT = find_root(__file__)


def _load_generator():
    home = Path(__file__).resolve().parents[1]
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", home / "generator.py")).resolve()
    spec = importlib.util.spec_from_file_location("reviewed_105b239cb812", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def transform(panel: list[list[int]], name: str) -> list[list[int]]:
    if name == "cw":
        return [list(row) for row in zip(*panel[::-1])]
    if name == "180":
        return [row[::-1] for row in panel[::-1]]
    if name == "ccw":
        return [list(row) for row in zip(*panel)][::-1]
    if name == "lr":
        return [row[::-1] for row in panel]
    if name == "ud":
        return [row[:] for row in panel[::-1]]
    if name == "transpose":
        return [list(row) for row in zip(*panel)]
    raise ValueError(name)


def split_panels(grid: list[list[int]]) -> tuple[list[list[int]], ...]:
    n = len(grid)
    assert len(grid[0]) == 3 * n + 2
    return tuple(
        [row[index * (n + 1): index * (n + 1) + n] for row in grid]
        for index in range(3)
    )


def independent_rule(grid: list[list[int]]) -> list[list[int]]:
    left, middle, query = split_panels(grid)
    matches = [name for name in TRANSFORMS if transform(left, name) == middle]
    assert len(matches) == 1, matches
    return transform(query, matches[0])


def test_rule_pin_and_all_canonical_pairs_are_owned() -> None:
    assert gen.RULE_HASH == RULE_HASH
    pairs = canonical_pairs(TASK_ID, root=ROOT, variant=0)
    assert len(pairs) == 3
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert independent_rule(pair["input"]) == pair["output"]
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("panel_size", [4, 5, 6, 7])
@pytest.mark.parametrize("transform_name", TRANSFORMS)
@pytest.mark.parametrize("shape_kind", SHAPE_KINDS)
def test_every_advertised_override_is_exact_and_authority_aligned(
    band: str, panel_size: int, transform_name: str, shape_kind: str
) -> None:
    grid = gen.generate(
        1701 + panel_size,
        3100 + TRANSFORMS.index(transform_name),
        difficulty=band,
        panel_size=panel_size,
        transform=transform_name,
        shape_kind=shape_kind,
    )
    assert gen.self_check(grid) == []
    left, middle, query = split_panels(grid)
    matches = [name for name in TRANSFORMS if transform(left, name) == middle]
    assert matches == [transform_name]
    assert gen.observe_overrides(grid) == {
        "panel_size": panel_size,
        "transform": transform_name,
        "shape_kind": shape_kind,
    }
    assert gen.rule_mirror(grid) == transform(query, transform_name)
    assert gen.rule_mirror(grid) != query


@pytest.mark.parametrize(
    "overrides",
    [
        {"invented_axis": 1},
        {"panel_size": 3},
        {"panel_size": 8},
        {"panel_size": True},
        {"transform": "identity"},
        {"transform": "anti"},
        {"transform": 1},
        {"shape_kind": "unknown"},
        {"shape_kind": 4},
    ],
)
def test_invalid_or_non_authoritative_overrides_are_rejected(overrides: dict) -> None:
    with pytest.raises(ValueError):
        gen.generate(1, 2, difficulty="easy", **overrides)


def test_default_distribution_is_deterministic_lawful_and_canonically_anchored() -> None:
    for band_index, band in enumerate(("easy", "medium", "hard")):
        observed_transforms = set()
        observed_sizes = set()
        observed_shapes = set()
        exact_profile_hits = 0
        for index in range(48):
            seed = 8000 + 1000 * band_index + index
            grid = gen.generate(seed, index, difficulty=band)
            replay = gen.generate(seed, index, difficulty=band)
            assert grid == replay
            assert grid is not replay
            assert all(left is not right for left, right in zip(grid, replay))
            assert gen.self_check(grid) == []
            observed = gen.observe_overrides(grid)
            observed_transforms.add(observed["transform"])
            observed_sizes.add(observed["panel_size"])
            observed_shapes.add(observed["shape_kind"])
            profile = (len(grid), len(grid[0]), len({v for row in grid for v in row}))
            exact_profile_hits += profile == (4, 14, 4)
        assert observed_transforms == set(TRANSFORMS)
        assert observed_sizes == {4, 5, 6, 7}
        assert observed_shapes == set(SHAPE_KINDS)
        assert exact_profile_hits >= 1


def test_validator_rejects_broken_or_ambiguous_panel_relations() -> None:
    grid = gen.generate(19, 7, panel_size=5, transform="cw", shape_kind="pentomino")
    assert gen.self_check(grid) == []
    n = len(grid)

    broken = copy.deepcopy(grid)
    middle_start = n + 1
    changed = False
    for row in range(n):
        for col in range(middle_start, middle_start + n):
            if broken[row][col] not in (0, 5):
                broken[row][col] = 0
                changed = True
                break
        if changed:
            break
    assert gen.self_check(broken)

    identity_pair = copy.deepcopy(grid)
    left, _, _ = split_panels(identity_pair)
    for row in range(n):
        identity_pair[row][middle_start:middle_start + n] = left[row]
    assert any("transform" in message for message in gen.self_check(identity_pair))

    extra_separator = copy.deepcopy(grid)
    for row in range(n):
        extra_separator[row][0] = 5
    assert gen.self_check(extra_separator)


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 1]], [[True] * 14 for _ in range(4)]])
def test_malformed_inputs_are_diagnostic_not_exceptions(grid) -> None:
    assert gen.self_check(grid)


def test_semantic_contract_has_executable_witnesses_and_rivals() -> None:
    quarter = gen.generate(77, 0, panel_size=4, transform="cw", shape_kind="tetromino")
    self_inverse = gen.generate(77, 0, panel_size=4, transform="lr", shape_kind="tetromino")

    assert gen.SEMANTIC_WITNESSES["query_changes"](quarter)
    assert gen.SEMANTIC_WITNESSES["quarter_turn_direction"](quarter)
    assert not gen.SEMANTIC_WITNESSES["quarter_turn_direction"](self_inverse)

    authority = gen.rule_mirror(quarter)
    assert gen.SEMANTIC_RIVALS["copy_query"](quarter) != authority
    assert gen.SEMANTIC_RIVALS["reverse_pair"](quarter) != authority
    assert gen.SEMANTIC_RIVALS["reverse_pair"](self_inverse) == gen.rule_mirror(self_inverse)

    pair = {"input": quarter, "output": authority}
    assert gen.lesson_identifiable([pair], pair) == []
    bad_pair = {"input": quarter, "output": gen.SEMANTIC_RIVALS["copy_query"](quarter)}
    assert gen.lesson_identifiable([pair], bad_pair)

@pytest.mark.parametrize("sample_index", [True, False, -1, 1.0, "1"])
def test_sample_index_must_be_a_nonnegative_literal_integer(sample_index) -> None:
    with pytest.raises((TypeError, ValueError)):
        gen.generate(991, sample_index, difficulty="easy")


def _labeled_pair(seed: int, sample_index: int, **overrides) -> dict:
    grid = gen.generate(seed, sample_index, difficulty="medium", **overrides)
    return {"input": grid, "output": independent_rule(grid)}


def test_lesson_identifiable_names_reverse_direction_ambiguity() -> None:
    demos = [
        _labeled_pair(31001, 0, transform="180"),
        _labeled_pair(31001, 1, transform="lr"),
        _labeled_pair(31001, 2, transform="transpose"),
    ]
    query = _labeled_pair(31001, 3, transform="cw")

    reasons = gen.lesson_identifiable(demos, query)
    assert any("reverse_pair" in reason for reason in reasons), reasons


def test_every_cyclic_lesson_and_query_rotation_refutes_reverse_direction() -> None:
    assert gen.EXAMPLES_NEEDED == 3
    assert gen.LESSON_SCHEDULE_PERIOD == len(gen.TRANSFORM_SCHEDULE)
    assert set(gen.TRANSFORM_SCHEDULE) == set(TRANSFORMS)
    assert set(gen.SCHEDULE_PROFILES) == set(TRANSFORMS)

    lesson_size = gen.EXAMPLES_NEEDED + 1
    for start in range(gen.LESSON_SCHEDULE_PERIOD):
        pairs = [_labeled_pair(41000 + start, start + offset) for offset in range(lesson_size)]
        for query_index in range(lesson_size):
            query = pairs[query_index]
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert gen.lesson_identifiable(demos, query) == [], (start, query_index)

            reverse_fits_demos = all(
                gen.LESSON_COMPETITORS["reverse_pair"](pair["input"]) == pair["output"]
                for pair in demos
            )
            reverse_changes_query = (
                gen.LESSON_COMPETITORS["reverse_pair"](query["input"]) != query["output"]
            )
            assert not (reverse_fits_demos and reverse_changes_query), (start, query_index)
