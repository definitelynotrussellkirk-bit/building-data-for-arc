from __future__ import annotations

import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, canonical_path, find_root


TASK_ID = "3ffc7ef20035"
GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.3ffc7ef20035.generator"
)
ROOT = find_root(__file__)


def _has_reason(errors, text: str) -> bool:
    return any(text in error for error in errors)


def _blue_bbox(grid):
    cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 1
    ]
    return (
        min(row for row, _col in cells),
        min(col for _row, col in cells),
        max(row for row, _col in cells),
        max(col for _row, col in cells),
    )


def test_canonical_inputs_are_accepted_and_rule_mirror_matches_outputs():
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert len(pairs) == 5
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_every_declared_canonical_shortcut_fits_every_canonical_pair():
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert "canonical_shape_whitelist" in GEN.CANONICAL_SHORTCUTS
    for name, shortcut in GEN.CANONICAL_SHORTCUTS.items():
        assert all(
            shortcut(pair["input"]) == pair["output"]
            for pair in pairs
        ), name


def test_rule_hash_matches_whitespace_normalized_canonical_authority():
    canonical = None
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                canonical = row["program_solution"]
                break
    assert canonical is not None
    actual = hashlib.sha256(" ".join(canonical.split()).encode()).hexdigest()[:12]
    assert GEN.RULE_HASH == actual


@pytest.mark.parametrize("profile", GEN.SHAPE_PROFILES)
def test_shape_profile_overrides_are_exact_and_observable(profile):
    grid = GEN.generate(
        101,
        7,
        difficulty="hard",
        grid_h=12,
        grid_w=12,
        shape_profile=profile,
        distractor_size=3,
        distractor_color=9,
    )
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == {
        "grid_h": 12,
        "grid_w": 12,
        "shape_profile": profile,
        "distractor_size": 3,
        "distractor_color": 9,
    }


@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": 8, "grid_w": 9, "distractor_size": 1, "distractor_color": 2},
        {"grid_h": 12, "grid_w": 12, "distractor_size": 3, "distractor_color": 9},
    ],
)
def test_boundary_overrides_survive_generation(overrides):
    grid = GEN.generate(17, 2, difficulty="easy", **overrides)
    observed = GEN.observe_overrides(grid)
    for key, value in overrides.items():
        assert observed[key] == value


def test_unknown_override_is_rejected_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(0, 0, typo_axis="ignored-by-old-generator")


def test_self_check_rejects_targeted_structural_impostors():
    base = GEN.generate(
        301,
        0,
        grid_h=10,
        grid_w=10,
        shape_profile="zigzag5_3x3",
        distractor_size=2,
        distractor_color=6,
    )
    assert GEN.self_check(base) == []

    has_cyan = [row[:] for row in base]
    has_cyan[0][0] = 8
    assert _has_reason(GEN.self_check(has_cyan), "reserved output color 8")

    solid_bbox = [row[:] for row in base]
    r0, c0, r1, c1 = _blue_bbox(solid_bbox)
    for row in range(r0, r1 + 1):
        for col in range(c0, c1 + 1):
            solid_bbox[row][col] = 1
    assert _has_reason(GEN.self_check(solid_bbox), "background gap")

    one_row = [[0] * 10 for _ in range(10)]
    one_row[3][2:5] = [1, 1, 1]
    one_row[9][9] = 6
    assert _has_reason(GEN.self_check(one_row), "span at least two rows")

    disconnected = [[0] * 10 for _ in range(10)]
    disconnected[1][1] = disconnected[1][2] = 1
    disconnected[6][6] = 1
    disconnected[9][9] = 6
    assert _has_reason(GEN.self_check(disconnected), "8-connected")

    distractor_inside = [row[:] for row in base]
    distractor_color = GEN.observe_overrides(base)["distractor_color"]
    for row, values in enumerate(distractor_inside):
        for col, value in enumerate(values):
            if value == distractor_color:
                distractor_inside[row][col] = 0
    r0, c0, r1, c1 = _blue_bbox(distractor_inside)
    gap = next(
        (row, col)
        for row in range(r0, r1 + 1)
        for col in range(c0, c1 + 1)
        if distractor_inside[row][col] == 0
    )
    distractor_inside[gap[0]][gap[1]] = distractor_color
    assert _has_reason(GEN.self_check(distractor_inside), "outside the blue bounding box")

    two_colors = [row[:] for row in base]
    two_colors[0][0] = 7 if distractor_color != 7 else 5
    assert _has_reason(GEN.self_check(two_colors), "exactly one distractor color")


def test_ordinary_schedule_refutes_each_canonical_shortcut():
    disagreements = {name: 0 for name in GEN.CANONICAL_SHORTCUTS}
    for sample_index in range(len(GEN.SHAPE_PROFILES) * 2):
        grid = GEN.generate(501, sample_index, difficulty="medium")
        expected = GEN.rule_mirror(grid)
        assert GEN.self_check(grid) == []
        for name, competitor in GEN.CANONICAL_SHORTCUTS.items():
            disagreements[name] += competitor(grid) != expected
    assert all(count > 0 for count in disagreements.values()), disagreements


def test_lesson_contract_includes_every_semantic_rival():
    assert GEN.LESSON_COMPETITORS == GEN.SEMANTIC_RIVALS
    assert GEN.LESSON_SCHEDULE_PERIOD == len(GEN.SHAPE_PROFILES)


def test_diagonal_profile_refutes_four_connected_component_shortcut():
    grid = GEN.generate(
        71,
        0,
        shape_profile="diagonal3_3x2",
        distractor_size=1,
        distractor_color=4,
    )
    assert GEN.SEMANTIC_WITNESSES["diagonal_only_blue_link"](grid)
    assert (
        GEN.SEMANTIC_RIVALS["first_4_connected_blue_component"](grid)
        != GEN.rule_mirror(grid)
    )


def test_every_sliding_lesson_window_is_identifiable():
    for start in range(len(GEN.SHAPE_PROFILES)):
        demos = []
        for sample_index in range(start, start + GEN.EXAMPLES_NEEDED):
            grid = GEN.generate(911, sample_index, difficulty="hard")
            demos.append({"input": grid, "output": GEN.rule_mirror(grid)})
        query_grid = GEN.generate(
            911, start + GEN.EXAMPLES_NEEDED, difficulty="hard"
        )
        query = {"input": query_grid, "output": GEN.rule_mirror(query_grid)}
        assert GEN.lesson_identifiable(demos, query) == []

        for name, competitor in GEN.SEMANTIC_RIVALS.items():
            fits_demos = all(
                competitor(pair["input"]) == pair["output"] for pair in demos
            )
            changes_query = competitor(query["input"]) != query["output"]
            assert not (fits_demos and changes_query), (
                start,
                GEN.schedule_profile(911, start + GEN.EXAMPLES_NEEDED, "hard"),
                name,
            )


def test_generate_is_deterministic_fresh_and_global_rng_pure():
    random.seed(123456)
    before = random.getstate()
    left = GEN.generate(44, 5, difficulty="medium")
    after = random.getstate()
    right = GEN.generate(44, 5, difficulty="medium")

    assert before == after
    assert left == right
    assert left is not right
    assert all(lrow is not rrow for lrow, rrow in zip(left, right))
    left[0][0] = 9
    assert left != right
