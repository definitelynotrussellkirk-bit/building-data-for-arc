from __future__ import annotations

import copy
import hashlib
import importlib
import random

import pytest

from reviewer_support import canonical_pairs, find_root


TASK_ID = "88ce0ac7322b"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
CANONICAL = canonical_pairs(TASK_ID, root=find_root(__file__))
PROFILES = ("canonical3", "mixed3", "mixed4", "mixed5")
SCHEDULE = ("canonical3", "mixed3", "canonical3", "mixed4", "mixed5")
ORDERS = ("reverse", "rotate", "zigzag")


def _split(grid: list[list[int]]) -> list[list[list[int]]]:
    width = len(grid[0])
    assert (width + 1) % 4 == 0
    return [
        [row[start : start + 3] for row in grid]
        for start in range(0, width, 4)
    ]


def _count(tile: list[list[int]]) -> int:
    return sum(value != 0 for row in tile for value in row)


def _assemble(tiles: list[list[list[int]]]) -> list[list[int]]:
    result = [[] for _ in range(3)]
    for index, tile in enumerate(tiles):
        if index:
            for row in result:
                row.append(9)
        for row_index, row in enumerate(tile):
            result[row_index].extend(row)
    return result


def _intended(grid: list[list[int]]) -> list[list[int]]:
    return _assemble(sorted(_split(grid), key=_count))


def _profile(grid: list[list[int]]) -> str:
    tiles = _split(grid)
    colors = {value for tile in tiles for row in tile for value in row if value != 0}
    if len(tiles) == 3 and colors == {2}:
        return "canonical3"
    return f"mixed{len(tiles)}"


def _rank_pattern(grid: list[list[int]]) -> tuple[int, ...]:
    counts = [_count(tile) for tile in _split(grid)]
    order = {count: rank for rank, count in enumerate(sorted(counts))}
    return tuple(order[count] for count in counts)


def _expected_rank_pattern(n: int, name: str) -> tuple[int, ...]:
    if name == "reverse":
        return tuple(range(n - 1, -1, -1))
    if name == "rotate":
        return tuple(range(1, n)) + (0,)
    if name == "zigzag":
        result: list[int] = []
        lo, hi = 0, n - 1
        while lo <= hi:
            result.append(hi)
            hi -= 1
            if lo <= hi:
                result.append(lo)
                lo += 1
        return tuple(result)
    raise AssertionError(name)


def test_authority_pin_and_truthful_axis_surface():
    assert GEN.RULE_HASH == "53d8281899b9"
    assert GEN.VERSION == "2.0.0"
    assert set(GEN.AXES) == {"profile", "order_pattern"}
    assert tuple(GEN.SCHEDULE_PROFILES) == SCHEDULE
    assert GEN.EXAMPLES_NEEDED == 3
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


def test_canonical_inputs_are_accepted_and_match_independent_oracle():
    assert len(CANONICAL) == 3
    for pair in CANONICAL:
        original = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert _profile(pair["input"]) == "canonical3"
        assert _intended(pair["input"]) == pair["output"]
        assert pair["input"] == original


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_five_residue_schedule_has_canonical_support_and_shortcut_witnesses(band):
    observed: list[str] = []
    for index in range(30):
        grid = GEN.generate(1009, index, difficulty=band)
        assert GEN.self_check(grid) == []
        assert GEN.strict_canonical_like(grid) == []
        assert grid != _intended(grid)
        assert GEN.schedule_profile(1009, index, band) == SCHEDULE[index % len(SCHEDULE)]
        stats = GEN.observe_overrides(grid)
        observed.append(stats["profile"])
        assert stats["profile"] == SCHEDULE[index % len(SCHEDULE)]
        assert stats["order_pattern"] in ORDERS
        if stats["profile"].startswith("mixed"):
            assert {value for row in grid for value in row} == {0, 1, 2, 9}
            expected = _intended(grid)
            assert GEN.SEMANTIC_WITNESSES["mixed_palette_refutes_shortcuts"](grid)
            assert all(rival(grid) != expected for rival in GEN.SEMANTIC_RIVALS.values())
    assert observed.count("canonical3") == 12
    assert set(observed) == set(PROFILES)
    for start in range(len(SCHEDULE)):
        window = [SCHEDULE[(start + offset) % len(SCHEDULE)] for offset in range(4)]
        assert sum(profile.startswith("mixed") for profile in window) >= 2


def test_pinned_profile_floor_census_has_at_least_25_percent_canonical_envelope():
    exact = 0
    total = 0
    for band in ("easy", "medium", "hard"):
        for index in range(20):
            digest = hashlib.sha256(
                f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
            ).hexdigest()
            seed = int(digest[:12], 16)
            sample_index = seed % 7919 + index
            grid = GEN.generate(seed, sample_index, difficulty=band)
            exact += int(len(grid) == 3 and len(grid[0]) == 11 and len({c for row in grid for c in row}) == 3)
            total += 1
    assert exact >= total / 4


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("profile", PROFILES)
@pytest.mark.parametrize("order_pattern", ORDERS)
def test_exact_overrides_are_observable_in_every_band(band, profile, order_pattern):
    grid = GEN.generate(
        217,
        19,
        difficulty=band,
        profile=profile,
        order_pattern=order_pattern,
    )
    assert GEN.self_check(grid) == []
    observed = GEN.observe_overrides(grid)
    assert observed == {"profile": profile, "order_pattern": order_pattern}
    assert _profile(grid) == profile
    assert _rank_pattern(grid) == _expected_rank_pattern(len(_split(grid)), order_pattern)


def test_unknown_and_invalid_overrides_are_rejected():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, typo_axis="mixed3")
    for bad in (None, True, 3, "other"):
        if bad is None:
            continue
        with pytest.raises(ValueError):
            GEN.generate(1, 0, profile=bad)
    for bad in (True, 1, "sorted", "other"):
        with pytest.raises(ValueError):
            GEN.generate(1, 0, order_pattern=bad)
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(1, 0, difficulty="extreme")


def test_self_check_rejects_targeted_malformed_and_rule_hiding_inputs():
    valid = GEN.generate(31, 7, profile="mixed4", order_pattern="zigzag")
    assert GEN.self_check(valid) == []

    ragged = copy.deepcopy(valid)
    ragged[-1].pop()
    bad_separator = copy.deepcopy(valid)
    bad_separator[0][3] = 0
    payload_nine = copy.deepcopy(valid)
    payload_nine[0][0] = 9
    tied = copy.deepcopy(valid)
    tied_tiles = _split(tied)
    tied_tiles[1] = copy.deepcopy(tied_tiles[0])
    tied = _assemble(tied_tiles)
    sorted_grid = _intended(valid)
    empty_tile = copy.deepcopy(valid)
    for row in empty_tile:
        row[:3] = [0, 0, 0]
    full_tile = copy.deepcopy(valid)
    for row in full_tile:
        row[:3] = [1, 1, 1]
    bad_cell = copy.deepcopy(valid)
    bad_cell[0][0] = 10

    for grid in (
        None,
        [],
        [[]],
        ragged,
        bad_separator,
        payload_nine,
        tied,
        sorted_grid,
        empty_tile,
        full_tile,
        bad_cell,
    ):
        assert GEN.self_check(grid), grid


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    random.seed(90210)
    state = random.getstate()
    first = GEN.generate(73, 18, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(73, 18, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 0
    assert GEN.generate(73, 18, difficulty="hard") == second


def test_declared_shortcuts_fit_every_canonical_pair_and_mixed_draws_refute_them():
    assert set(GEN.CANONICAL_SHORTCUTS) == {
        "color_2_count",
        "dominant_color_count",
        "raw_color_sum",
    }
    assert set(GEN.CANONICAL_SHORTCUTS) == set(GEN.SEMANTIC_RIVALS)
    assert set(GEN.CANONICAL_SHORTCUTS) == set(GEN.LESSON_COMPETITORS)
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in CANONICAL), name

    for profile in PROFILES[1:]:
        for order_pattern in ORDERS:
            grid = GEN.generate(
                443,
                5,
                profile=profile,
                order_pattern=order_pattern,
            )
            expected = _intended(grid)
            for name, rival in GEN.CANONICAL_SHORTCUTS.items():
                assert rival(grid) != expected, (profile, order_pattern, name)


def test_every_four_pair_schedule_and_every_query_rotation_is_identifiable():
    for band in ("easy", "medium", "hard"):
        for start in range(15):
            grids = [GEN.generate(8001, start + offset, difficulty=band) for offset in range(4)]
            pairs = [{"input": grid, "output": _intended(grid)} for grid in grids]
            for query_index in range(4):
                query = pairs[query_index]
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                assert GEN.lesson_identifiable(demos, query) == [], (band, start, query_index)
                for rival in GEN.LESSON_COMPETITORS.values():
                    assert any(rival(demo["input"]) != demo["output"] for demo in demos)


def test_lesson_hook_rejects_bad_labels_invalid_inputs_and_shortcut_only_demos():
    grids = [GEN.generate(91, index, difficulty="medium") for index in range(4)]
    pairs = [{"input": grid, "output": _intended(grid)} for grid in grids]

    bad_label = copy.deepcopy(pairs[:3])
    bad_label[0]["output"] = bad_label[0]["input"]
    assert any("authoritative occupancy sort" in reason for reason in GEN.lesson_identifiable(bad_label, pairs[3]))

    bad_query = copy.deepcopy(pairs[3])
    bad_query["input"] = [row[:-1] for row in bad_query["input"]]
    assert any("query input" in reason for reason in GEN.lesson_identifiable(pairs[:3], bad_query))

    canonical_demos = [copy.deepcopy(pair) for pair in CANONICAL]
    mixed_query = {
        "input": GEN.generate(5, 1, profile="mixed3"),
    }
    reasons = GEN.lesson_identifiable(canonical_demos, mixed_query)
    assert any("survives every demonstration" in reason for reason in reasons)
