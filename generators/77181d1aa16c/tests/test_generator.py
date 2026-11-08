"""Focused regression and semantic-contract tests for 77181d1aa16c."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "77181d1aa16c"
HOME = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", SOURCE)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def _largest_rect(grid):
    """Independent exhaustive mirror of the Racket scan/tie order."""
    height, width = len(grid), len(grid[0])
    prefix = [[0] * (width + 1) for _ in range(height + 1)]
    for row in range(height):
        for col in range(width):
            prefix[row + 1][col + 1] = (
                prefix[row][col + 1]
                + prefix[row + 1][col]
                - prefix[row][col]
                + int(grid[row][col] == 0)
            )
    best = (0, 0, 0, 0, 0)
    for top in range(height):
        for bottom in range(top, height):
            for left in range(width):
                for right in range(left, width):
                    area = (bottom - top + 1) * (right - left + 1)
                    zeros = (
                        prefix[bottom + 1][right + 1]
                        - prefix[top][right + 1]
                        - prefix[bottom + 1][left]
                        + prefix[top][left]
                    )
                    if area > best[0] and zeros == 0:
                        best = (area, top, left, bottom, right)
    return best[1:]


def _oracle(grid, *, rect=None, last=False, mirror=True, carry_missing=False):
    """Independent model of the selected Racket rule and deliberate rivals."""
    height, width = len(grid), len(grid[0])
    if rect is None:
        rect = _largest_rect(grid)
    top, left, bottom, right = rect
    ph, pw = bottom - top + 1, right - left + 1
    pattern = [row[left : right + 1] for row in grid[top : bottom + 1]]
    counts = Counter(value for row in pattern for value in row if value != 0)
    roles = [color for color, _ in sorted(counts.items(), key=lambda item: -item[1])[:2]]
    if len(roles) < 2:
        return [[0] * width for _ in range(height)]

    def block(row, col):
        return 2 * int(row >= top + ph) + int(col >= left + pw)

    def role_at(row, col):
        lower = row >= top + ph
        rightward = col >= left + pw
        local_row = row - (top + ph if lower else top)
        local_col = col - (left + pw if rightward else left)
        if not (0 <= local_row < ph and 0 <= local_col < pw):
            return None
        source_row = ph - 1 - local_row if lower and mirror else local_row
        source_col = pw - 1 - local_col if rightward and mirror else local_col
        value = pattern[source_row][source_col]
        return value if value in roles else None

    mappings = {}
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value == 0 or (top <= row <= bottom and left <= col <= right):
                continue
            role = role_at(row, col)
            if role is None:
                continue
            descriptor = (block(row, col), role)
            if last or descriptor not in mappings:
                mappings[descriptor] = value

    output = [[0] * width for _ in range(height)]
    for row in range(height):
        for col in range(width):
            role = role_at(row, col)
            if role is None:
                continue
            key = block(row, col)
            if key == 0:
                output[row][col] = role
            elif (key, role) in mappings:
                output[row][col] = mappings[(key, role)]
            elif carry_missing:
                output[row][col] = role
    return output


def _source_facts(grid):
    top, left, bottom, right = _largest_rect(grid)
    ph, pw = bottom - top + 1, right - left + 1
    pattern = [row[left : right + 1] for row in grid[top : bottom + 1]]
    counts = Counter(value for row in pattern for value in row)
    major, minor = [color for color, _ in sorted(counts.items(), key=lambda item: -item[1])]

    def role_at(row, col):
        lower = row >= top + ph
        rightward = col >= left + pw
        local_row = row - (top + ph if lower else top)
        local_col = col - (left + pw if rightward else left)
        if not (0 <= local_row < ph and 0 <= local_col < pw):
            return None
        return pattern[ph - 1 - local_row if lower else local_row][
            pw - 1 - local_col if rightward else local_col
        ]

    groups = Counter()
    group_colors = {}
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value == 0 or (top <= row <= bottom and left <= col <= right):
                continue
            key = 2 * int(row >= top + ph) + int(col >= left + pw)
            role = role_at(row, col)
            groups[(key, role)] += 1
            group_colors.setdefault((key, role), []).append(value)
    return {
        "rect": (top, left, bottom, right),
        "shape": (ph, pw),
        "pattern": pattern,
        "major": major,
        "minor": minor,
        "groups": groups,
        "group_colors": group_colors,
    }


def _pair(grid):
    return {"input": grid, "output": _oracle(grid)}


def _solutions_root():
    root = find_root(__file__)
    for relative in ("data/base/solutions", "shared/data/base/solutions"):
        candidate = root / relative
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError(f"No base solutions tree under {root}")


def test_selected_racket_target_is_exactly_synced_while_raw_source_is_preserved():
    solutions = _solutions_root()
    canonical = json.loads(
        (solutions / "training/cfb2ce5a__77181d1aa16c.json").read_text()
    )["racket_target"]
    selected = json.loads(
        (solutions / "augmented/cfb2ce5a__ff91516a094e.json").read_text()
    )["racket_target"]
    assert selected["target_code"] == canonical["target_code"]
    assert selected["raw_code"] != canonical["target_code"]


def test_rule_pin_and_repaired_contract():
    assert GEN.RULE_HASH == "76ff7f3a7ec0"
    assert GEN.VERSION == "4.0.0"
    assert GEN.EXAMPLES_NEEDED == 4
    assert GEN.LESSON_SCHEDULE_PERIOD == 6
    assert GEN.SCHEDULE_PROFILES == (0, 1, 2, 3, 4, 5)
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert set(GEN.AXES) == {
        "pattern_h",
        "pattern_w",
        "top_margin",
        "bottom_margin",
        "left_margin",
        "right_margin",
        "indicator_profile",
    }


def test_all_canonical_occurrences_are_accepted_and_oracle_exact():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert len(pairs) == 8
    for pair in pairs:
        before = deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert _oracle(pair["input"]) == pair["output"]
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_declared_canonical_shortcuts_really_fit_every_canonical_occurrence():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert set(GEN.CANONICAL_SHORTCUTS) == {
        "fixed_canonical_source",
        "force_square_source",
        "last_indicator_wins",
    }
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs), name


_OVERRIDE_CASES = (
    dict(pattern_h=3, pattern_w=3, top_margin=0, bottom_margin=0,
         left_margin=0, right_margin=0, indicator_profile=0),
    dict(pattern_h=5, pattern_w=5, top_margin=2, bottom_margin=2,
         left_margin=2, right_margin=2, indicator_profile=3),
    dict(pattern_h=3, pattern_w=5, top_margin=0, bottom_margin=2,
         left_margin=2, right_margin=0, indicator_profile=1),
    dict(pattern_h=5, pattern_w=3, top_margin=2, bottom_margin=0,
         left_margin=0, right_margin=2, indicator_profile=2),
)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("options", _OVERRIDE_CASES)
def test_exact_joint_overrides_are_constructive_observable_and_label_safe(band, options):
    grid = GEN.generate(913, 17, difficulty=band, **options)
    assert GEN.self_check(grid, meta={"overrides": options}) == []
    assert GEN.observe_overrides(grid) == options
    assert GEN.rule_mirror(grid) == _oracle(grid)
    assert len(grid) == options["top_margin"] + 2 * options["pattern_h"] + options["bottom_margin"]
    assert len(grid[0]) == options["left_margin"] + 2 * options["pattern_w"] + options["right_margin"]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"unknown": 1},
        {"pattern_h": 2}, {"pattern_h": 6},
        {"pattern_w": 2}, {"pattern_w": 6},
        {"top_margin": -1}, {"top_margin": 3},
        {"bottom_margin": -1}, {"bottom_margin": 3},
        {"left_margin": -1}, {"left_margin": 3},
        {"right_margin": -1}, {"right_margin": 3},
        {"indicator_profile": -1}, {"indicator_profile": 4},
        {"pattern_h": True}, {"pattern_w": 3.0},
        {"top_margin": "1"}, {"indicator_profile": None},
        {"difficulty": "expert"},
    ],
)
def test_invalid_controls_fail_loudly(kwargs):
    difficulty = kwargs.pop("difficulty", None)
    with pytest.raises(ValueError):
        GEN.generate(0, 0, difficulty=difficulty, **kwargs)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_six_profile_schedule_covers_geometry_and_every_rival_witness(band):
    grids = [GEN.generate(8801, index, difficulty=band) for index in range(12)]
    assert [GEN.schedule_profile(8801, index, difficulty=band) for index in range(6)] == list(range(6))
    observed = [GEN.observe_overrides(grid) for grid in grids]
    assert {item["pattern_h"] for item in observed} == {3, 4, 5}
    assert {item["pattern_w"] for item in observed} == {3, 4, 5}
    assert {item["top_margin"] for item in observed} == {0, 1, 2}
    assert {item["bottom_margin"] for item in observed} == {0, 1, 2}
    assert {item["left_margin"] for item in observed} == {0, 1, 2}
    assert {item["right_margin"] for item in observed} == {0, 1, 2}
    assert {item["indicator_profile"] for item in observed} == {0, 1, 2, 3}
    assert any((len(grid), len(grid[0]), len({v for row in grid for v in row})) == (10, 10, 9)
               for grid in grids)
    for grid in grids:
        assert GEN.self_check(grid) == []
        assert GEN.SEMANTIC_WITNESSES["conflicting_duplicate_indicator"](grid)
        assert GEN.SEMANTIC_WITNESSES["missing_role_mapping"](grid)
        assert GEN.SEMANTIC_WITNESSES["asymmetric_source_pattern"](grid)
        truth = _oracle(grid)
        assert GEN.SEMANTIC_RIVALS["last_indicator_wins"](grid) != truth
        assert GEN.SEMANTIC_RIVALS["carry_source_when_mapping_missing"](grid) != truth
        assert GEN.SEMANTIC_RIVALS["copy_without_mirroring"](grid) != truth


def test_noncanonical_frame_witness_only_claims_an_actual_fixed_frame_refutation():
    # Retained from the strict semantic gate: the true 3x4 source starts at
    # (2, 1), but this particular scene happens to give the same output under
    # the fixed-(1,1,4,4) shortcut.  Geometry alone is not a separating witness.
    accidental_agreement = GEN.generate(116417998598655, 4783, difficulty="easy")
    assert GEN._analysis(accidental_agreement)["rect"] == (2, 1, 4, 4)
    assert GEN._rival_fixed_canonical_source(accidental_agreement) == GEN.rule_mirror(accidental_agreement)
    assert not GEN.SEMANTIC_WITNESSES["noncanonical_source_frame"](accidental_agreement)

    witnessed = [
        GEN.generate(99173, index, difficulty="hard")
        for index in range(24)
        if GEN.SEMANTIC_WITNESSES["noncanonical_source_frame"](
            GEN.generate(99173, index, difficulty="hard")
        )
    ]
    assert witnessed
    assert all(
        GEN._rival_fixed_canonical_source(grid) != GEN.rule_mirror(grid)
        for grid in witnessed
    )


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_cyclic_five_pair_window_and_every_query_rotation_refutes_all_rivals(band):
    for start in range(12):
        pairs = [_pair(GEN.generate(1207 + start, start + offset, difficulty=band))
                 for offset in range(5)]
        for query_index, query in enumerate(pairs):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert GEN.lesson_identifiable(demos, query) == []
            for name, rival in GEN.LESSON_COMPETITORS.items():
                assert any(rival(item["input"]) != item["output"] for item in demos), (
                    band,
                    start,
                    query_index,
                    name,
                )


def test_default_distribution_is_deterministic_fresh_and_diverse():
    frozen = set()
    for band in (None, "easy", "medium", "hard"):
        for index in range(36):
            first = GEN.generate(4301, index, difficulty=band)
            second = GEN.generate(4301, index, difficulty=band)
            assert first == second
            assert first is not second
            assert all(left is not right for left, right in zip(first, second))
            assert GEN.self_check(first) == []
            before = deepcopy(first)
            assert GEN.rule_mirror(first) == _oracle(first)
            for fn in GEN.SEMANTIC_RIVALS.values():
                fn(first)
                assert first == before
            frozen.add(tuple(tuple(row) for row in first))
    # None intentionally aliases the medium curriculum; the three explicit bands
    # still provide at least 90 distinct scenes across 108 deterministic draws.
    assert len(frozen) >= 90


def test_validator_rejects_targeted_near_misses_without_crashing():
    valid = GEN.generate(700, 2, difficulty="hard")
    assert GEN.self_check(valid) == []
    facts = _source_facts(valid)

    third_pattern_color = deepcopy(valid)
    top, left, _, _ = facts["rect"]
    third_pattern_color[top][left] = next(color for color in range(1, 10) if color not in {facts["major"], facts["minor"]})
    assert GEN.self_check(third_pattern_color)

    outside_support = deepcopy(valid)
    outside_support[0][0] = next(color for color in range(1, 10) if color != outside_support[0][0])
    assert GEN.self_check(outside_support)

    erased_block = deepcopy(valid)
    top, left, bottom, right = facts["rect"]
    ph, pw = facts["shape"]
    for row in range(len(erased_block)):
        for col in range(len(erased_block[0])):
            if row >= top + ph and col >= left + pw and not (top <= row <= bottom and left <= col <= right):
                if erased_block[row][col] != 0:
                    erased_block[row][col] = 0
    assert GEN.self_check(erased_block)

    for malformed in (None, [], [[]], [[0], [0, 1]], [[True] * 8 for _ in range(8)], [[10] * 8 for _ in range(8)]):
        errors = GEN.self_check(malformed)
        assert isinstance(errors, list) and errors


def test_selected_racket_authority_matches_independent_oracle_on_generated_conflicts():
    from arcpuzzles import Catalog
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [
        GEN.generate(51000 + band_index, index, difficulty=band)
        for band_index, band in enumerate(("easy", "medium", "hard"))
        for index in range(6)
    ]
    receipt = Catalog(find_root(__file__)).apply(TASK_ID, grids, reference="canonical", timeout=180)
    assert receipt["rule_hash_matches_catalog"]
    assert all(item["error"] is None for item in receipt["results"])
    assert [item["output"] for item in receipt["results"]] == [_oracle(grid) for grid in grids]
