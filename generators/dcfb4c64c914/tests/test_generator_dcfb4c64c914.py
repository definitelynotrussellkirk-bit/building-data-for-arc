from __future__ import annotations

import copy
import importlib.util
import itertools
import os
from pathlib import Path
import random
import sys

import pytest

TASK_ID = "dcfb4c64c914"
TEST_DIR = Path(__file__).resolve().parent
GENERATOR_PATH = Path(
    os.environ.get("GENERATOR_UNDER_TEST", TEST_DIR.parent / "generator.py")
).resolve()

# Portable bootstrap: source tree and staged task-test runtime.
for candidate in (
    TEST_DIR.parents[2] / "shared" / "runtime",
    TEST_DIR.parents[3] / "shared" / "runtime",
    TEST_DIR.parents[2],
    TEST_DIR.parents[3],
):
    if (candidate / "reviewer_support.py").is_file() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from reviewer_support import canonical_pairs, find_root  # noqa: E402

SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", GENERATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
GEN = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GEN
SPEC.loader.exec_module(GEN)

PROBE_PATH = GENERATOR_PATH.parent / "workspace" / "reference_probe.py"
PROBE_SPEC = importlib.util.spec_from_file_location(f"probe_{TASK_ID}", PROBE_PATH)
assert PROBE_SPEC is not None and PROBE_SPEC.loader is not None
PROBE = importlib.util.module_from_spec(PROBE_SPEC)
sys.modules[PROBE_SPEC.name] = PROBE
PROBE_SPEC.loader.exec_module(PROBE)

ROOT = find_root(__file__)


def _pairs() -> list[dict]:
    return canonical_pairs(TASK_ID, root=ROOT)


def _demo(grid: list[list[int]]) -> dict:
    return {"input": copy.deepcopy(grid), "output": PROBE.authority_output(grid)}


def _freeze(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def test_rule_pin_contract_and_independent_oracle_match_every_canonical_pair():
    assert GEN.VERSION == "3.0.0"
    assert GEN.RULE_HASH == "53fe6f709bdc"
    assert set(GEN.AXES) == {
        "layout",
        "profile_case",
        "geometry_mode",
        "placement_mode",
        "color_pair",
    }
    pairs = _pairs()
    assert len(pairs) == 3
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        before = copy.deepcopy(source)
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert PROBE.authority_output(source) == pair["output"]
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == before


def test_canvas_alignment_is_a_real_canonical_shortcut_and_generated_counterexample_exists():
    shortcut = GEN.CANONICAL_SHORTCUTS["canvas_row_alignment"]
    assert all(shortcut(pair["input"]) == pair["output"] for pair in _pairs())

    witnesses = [GEN.generate(1701, index, difficulty="medium") for index in range(8)]
    witness = next(grid for grid in witnesses if GEN.SEMANTIC_WITNESSES["staggered_alignment"](grid))
    assert GEN.self_check(witness) == []
    assert shortcut(witness) != GEN.rule_mirror(witness)


def test_default_four_slot_schedule_has_canonical_profiles_and_redundant_semantics():
    expected_profiles = list(GEN.SCHEDULE_PROFILES)
    for difficulty in (None, "easy", "medium", "hard"):
        grids = [GEN.generate(7001, index, difficulty=difficulty) for index in range(4)]
        assert [GEN.schedule_profile(7001, index, difficulty) for index in range(4)] == expected_profiles
        assert [(len(grid), len(grid[0])) for grid in grids[:3]] == [(8, 15), (9, 15), (9, 17)]
        assert all(GEN.self_check(grid) == [] for grid in grids)
        assert all(PROBE.authority_output(grid) == GEN.rule_mirror(grid) for grid in grids)

        fired = {
            name: sum(bool(predicate(grid)) for grid in grids)
            for name, predicate in GEN.SEMANTIC_WITNESSES.items()
        }
        assert all(count > 0 for count in fired.values()), fired

        # Every single-example holdout leaves three labelled demonstrations.
        labelled = [_demo(grid) for grid in grids]
        for query_index in range(4):
            demos = [pair for index, pair in enumerate(labelled) if index != query_index]
            assert GEN.lesson_identifiable(demos, labelled[query_index]) == []


def test_every_declared_override_cross_is_exact_observable_and_lawful():
    names = ("layout", "profile_case", "geometry_mode", "placement_mode", "color_pair")
    domains = (
        tuple(GEN.LAYOUTS),
        tuple(GEN.PROFILE_CASES),
        tuple(GEN.GEOMETRY_MODES),
        tuple(GEN.PLACEMENT_MODES),
        tuple(GEN.COLOR_PAIRS),
    )
    for index, values in enumerate(itertools.product(*domains)):
        requested = dict(zip(names, values))
        grid = GEN.generate(10_000 + index, index, difficulty="medium", **requested)
        assert GEN.observe_overrides(grid) == requested
        assert GEN.self_check(grid) == []
        assert GEN.rule_mirror(grid) == PROBE.authority_output(grid)

    boundary = dict(
        layout=GEN.LAYOUTS[-1],
        profile_case=GEN.PROFILE_CASES[-1],
        geometry_mode=GEN.GEOMETRY_MODES[-1],
        placement_mode=GEN.PLACEMENT_MODES[-1],
        color_pair=GEN.COLOR_PAIRS[-1],
    )
    for difficulty in (None, "easy", "medium", "hard"):
        grid = GEN.generate(222, 17, difficulty=difficulty, **boundary)
        assert GEN.observe_overrides(grid) == boundary


@pytest.mark.parametrize(
    "kwargs",
    [
        {"difficulty": "expert"},
        {"layout": "missing"},
        {"profile_case": 3},
        {"geometry_mode": None, "typo_axis": "x"},
        {"placement_mode": True},
        {"color_pair": "2-2"},
        {"__override_contract_unknown_axis__": 1},
    ],
)
def test_invalid_difficulty_types_values_and_unknown_axes_fail_loudly(kwargs):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 2, **kwargs)


def test_generated_inputs_match_the_racket_authority():
    from arcpuzzles import Catalog

    grids = [
        GEN.generate(51_000 + band_index, index, difficulty=band)
        for band_index, band in enumerate(("easy", "medium", "hard"))
        for index in range(4)
    ]
    receipt = Catalog(ROOT).apply(TASK_ID, grids, reference="canonical", timeout=180)
    assert receipt["rule_hash_matches_catalog"]
    assert [row["output"] for row in receipt["results"]] == [
        PROBE.authority_output(grid) for grid in grids
    ]


def test_self_check_rejects_structural_mutations_without_crashing():
    grid = GEN.generate(91, 2, difficulty="hard")
    analysis = PROBE.analyze(grid)

    broken_divider = copy.deepcopy(grid)
    broken_divider[0][analysis["divider"]] = 0
    assert GEN.self_check(broken_divider)

    extra_divider = copy.deepcopy(grid)
    for row in extra_divider:
        row[0] = 5
    assert GEN.self_check(extra_divider)

    multicolor = copy.deepcopy(grid)
    cell = analysis["left"]["global_cells"][0]
    multicolor[cell[0]][cell[1]] = 9 if multicolor[cell[0]][cell[1]] != 9 else 7
    assert GEN.self_check(multicolor)

    disconnected = copy.deepcopy(grid)
    target = next(
        (r, c)
        for r in range(len(grid))
        for c in range(analysis["divider"])
        if disconnected[r][c] == 0
        and all(
            not (0 <= r + dr < len(grid) and 0 <= c + dc < analysis["divider"])
            or disconnected[r + dr][c + dc] == 0
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
        )
    )
    disconnected[target[0]][target[1]] = analysis["left"]["color"]
    assert GEN.self_check(disconnected)

    identical_profiles = GEN.generate(
        19,
        3,
        profile_case="equal_left_dominant",
        geometry_mode="contiguous",
    )
    info = PROBE.analyze(identical_profiles)
    # Replace the right object by a translated copy of the left object.
    for r, c in info["right"]["global_cells"]:
        identical_profiles[r][c] = 0
    right_start = info["divider"] + 1
    shape = info["left"]["shape"]
    top = info["right"]["top"]
    for dr, dc in shape:
        identical_profiles[top + dr][right_start + 1 + dc] = info["right"]["color"]
    assert any("difference" in message for message in GEN.self_check(identical_profiles))

    for malformed in (None, [], [[]], [[0], [0, 1]], [[True] * 15 for _ in range(8)]):
        assert GEN.self_check(malformed)


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    random.seed(20261007)
    state = random.getstate()
    first = GEN.generate(73, 19, difficulty="hard")
    middle = random.getstate()
    second = GEN.generate(73, 19, difficulty="hard")
    after = random.getstate()
    assert state == middle == after
    assert _freeze(first) == _freeze(second)
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 8 if first[0][0] != 8 else 7
    assert first != second


def test_generated_difference_profiles_are_not_a_small_fixed_bank():
    outputs = {
        _freeze(GEN.rule_mirror(GEN.generate(30_000 + index, index, difficulty="medium")))
        for index in range(160)
    }
    assert len(outputs) >= 60


def test_difficulty_bands_change_latent_profile_complexity_without_changing_axes():
    for index in range(4):
        grids = [GEN.generate(81_000, index, difficulty=band) for band in ("easy", "medium", "hard")]
        assert len({_freeze(grid) for grid in grids}) >= 2
        observed = [GEN.observe_overrides(grid) for grid in grids]
        assert observed[0] == observed[1] == observed[2]
