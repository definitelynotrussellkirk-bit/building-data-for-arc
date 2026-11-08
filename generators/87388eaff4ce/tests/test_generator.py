"""Source-bound regressions for ARC task 87388eaff4ce.

The canonical Racket program remains the label authority.  The Python mirror is
only an authoring aid and is checked against every labeled canonical pair and
against real Catalog applications before semantic probes rely on it.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
import sys

import pytest
from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root

TASK_ID = "87388eaff4ce"
ROOT = find_root(__file__)
TASK_DIR = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

spec = importlib.util.spec_from_file_location(
    f"review_{TASK_ID}_generator", TASK_DIR / "generator.py"
)
assert spec and spec.loader
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

BANDS = (None, "easy", "medium", "hard")


def accepted(result):
    return result is True or result == []


@pytest.fixture(scope="module")
def canonical():
    return canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)


@pytest.fixture(scope="module")
def minimal_witness():
    """Three lawful objects exposing both primary ordering and the tie-break.

    Color 5 is the tall 4x1 object.  The equal-height short objects are an
    earlier color-9 U (five cells, width three) and a later color-2 square.
    Thus height-only row order, cell-count-first, width-first, and ascending
    height all disagree with the authority.
    """
    grid = [[0] * 12 for _ in range(9)]
    for r in range(4):
        grid[1 + r][8] = 5
    for r, c in ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2)):
        grid[1 + r][1 + c] = 9
    for r, c in ((0, 0), (0, 1), (1, 0), (1, 1)):
        grid[6 + r][4 + c] = 2
    return grid


def test_rule_pin_summary_and_canonical_pairs_are_exact(canonical):
    assert gen.RULE_HASH == "c701ff882260"
    text = gen.SUMMARY.lower()
    assert "height" in text and "color ascending" in text
    assert callable(getattr(gen, "strict_canonical_like", None))
    assert callable(getattr(gen, "rule_mirror", None))
    for pair in canonical:
        original = deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert accepted(gen.strict_canonical_like(pair["input"]))
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


@pytest.mark.parametrize("band", BANDS)
def test_canonical_inputs_are_not_rejected_by_difficulty(canonical, band):
    for pair in canonical:
        assert gen.self_check(pair["input"], difficulty=band) == []
        assert accepted(gen.strict_canonical_like(pair["input"]))


def test_minimal_counterexample_refutes_every_declared_rival(minimal_witness):
    intended = gen.rule_mirror(minimal_witness)
    assert gen.self_check(minimal_witness) == []
    assert set(gen.SEMANTIC_RIVALS) == {
        "height_only_row_major",
        "cell_count_first",
        "width_first",
        "height_ascending",
    }
    for name, rival in gen.SEMANTIC_RIVALS.items():
        assert rival(minimal_witness) != intended, name
    for witness in gen.SEMANTIC_WITNESSES.values():
        assert witness(minimal_witness)


@pytest.mark.parametrize("band", BANDS)
def test_exact_axes_are_honored_and_observable_in_every_band(band):
    for grid_h in (9, 10):
        for grid_w in (12, 13):
            options = {"grid_h": grid_h, "grid_w": grid_w}
            grid = gen.generate(9182, 17, difficulty=band, **options)
            assert gen.observe_overrides(grid) == options
            assert gen.self_check(grid, difficulty=band) == []
            assert len(gen._object_infos(grid)) == 3
            assert len(gen.rule_mirror(grid)) > len(grid)
            for witness in gen.SEMANTIC_WITNESSES.values():
                assert witness(grid)


@pytest.mark.parametrize(
    "key,value",
    [
        ("grid_h", 8), ("grid_h", 11), ("grid_w", 11), ("grid_w", 14),
        ("grid_h", True), ("grid_h", 9.0), ("grid_w", "12"),
        ("texture", "default"), ("palette_kind", "warm"),
        ("palette_size", 3), ("n_objs", 3),
        ("n_distinct_colors", 3), ("position_bias", "scattered"),
        ("density", "sparse"), ("unknown_axis", 1),
    ],
)
def test_invalid_or_retired_controls_are_rejected(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize(
    "seed,sample_index",
    [(True, 0), (1.5, 0), ("1", 0), (1, True), (1, -1)],
)
def test_seed_and_sample_index_are_strict(seed, sample_index):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(seed, sample_index)


@pytest.mark.parametrize("difficulty", [False, "unknown", 1])
def test_difficulty_is_strict(difficulty):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 0, difficulty=difficulty)


def test_none_override_values_keep_default_semantics():
    assert gen.generate(22, 1, grid_h=None, grid_w=None) == gen.generate(22, 1)


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True] * 12 for _ in range(9)],
        [[0] * 12],
        [[0] * 12 for _ in range(9)],
        [[0] * 11 + [10] for _ in range(9)],
        ["000000000000"] * 9,
    ],
)
def test_malformed_self_check_reports_reasons_without_exception(grid):
    result = gen.self_check(grid)
    assert isinstance(result, list) and result


@pytest.fixture(scope="module")
def default_lessons():
    return {
        band: [gen.generate(761, i, difficulty=band) for i in range(12)]
        for band in ("easy", "medium", "hard")
    }


def test_default_lessons_are_deterministic_lawful_and_counterexample_rich(default_lessons):
    for band, grids in default_lessons.items():
        for index, grid in enumerate(grids):
            assert grid == gen.generate(761, index, difficulty=band)
            assert gen.self_check(grid, difficulty=band) == []
            assert len(gen.rule_mirror(grid)) > len(grid)
            for name, witness in gen.SEMANTIC_WITNESSES.items():
                assert witness(grid), (band, index, name)
            intended = gen.rule_mirror(grid)
            for name, rival in gen.SEMANTIC_RIVALS.items():
                assert rival(grid) != intended, (band, index, name)


def test_schedule_supplies_both_canonical_input_profiles(default_lessons):
    wanted = {(9, 12, 3), (10, 13, 3)}
    for band, grids in default_lessons.items():
        observed = {
            (len(grid), len(grid[0]), len(gen._object_infos(grid))) for grid in grids
        }
        assert wanted <= observed, (band, observed)


def test_every_three_demo_rotation_refutes_all_declared_rivals(default_lessons):
    assert gen.EXAMPLES_NEEDED == 3
    for band, grids in default_lessons.items():
        outputs = [gen.rule_mirror(grid) for grid in grids]
        for start in range(len(grids) - gen.EXAMPLES_NEEDED):
            window = list(range(start, start + gen.EXAMPLES_NEEDED + 1))
            for query in window:
                demos = [i for i in window if i != query]
                for name, rival in gen.LESSON_COMPETITORS.items():
                    assert any(rival(grids[i]) != outputs[i] for i in demos), (
                        band, start, query, name
                    )


def test_lesson_identifiable_checks_declared_competitors(default_lessons):
    grids = default_lessons["medium"][:4]
    pairs = [{"input": grid, "output": gen.rule_mirror(grid)} for grid in grids]
    for query_index in range(4):
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        assert gen.lesson_identifiable(demos, pairs[query_index]) == []


def test_self_check_rejects_destructive_mutations():
    grid = gen.generate(31415, 2, difficulty="medium")
    mutations = []

    blank = [[0 for _ in row] for row in grid]
    mutations.append(blank)

    dropped = deepcopy(grid)
    first = next((r, c) for r, row in enumerate(dropped) for c, v in enumerate(row) if v)
    dropped[first[0]][first[1]] = 0
    mutations.append(dropped)

    duplicate_color = deepcopy(grid)
    infos = gen._object_infos(duplicate_color)
    for r, c in infos[1].cells:
        duplicate_color[r][c] = infos[0].color
    mutations.append(duplicate_color)

    bad_cell = deepcopy(grid)
    bad_cell[first[0]][first[1]] = True
    mutations.append(bad_cell)

    extra = deepcopy(grid)
    empty = next((r, c) for r, row in enumerate(extra) for c, v in enumerate(row) if v == 0)
    extra[empty[0]][empty[1]] = 9 if all(i.color != 9 for i in infos) else 8
    mutations.append(extra)

    for mutation in mutations:
        assert gen.self_check(mutation), mutation


def test_real_racket_matches_local_mirror(canonical, minimal_witness, default_lessons):
    grids = [pair["input"] for pair in canonical]
    grids += [minimal_witness]
    grids += default_lessons["medium"][:4]
    applied = Catalog().apply(TASK_ID, grids, timeout=180)
    assert applied["rule_hash_matches_catalog"]
    assert all(r["valid_output"] and r["error"] is None for r in applied["results"])
    for result in applied["results"]:
        assert result["output"] == gen.rule_mirror(result["input"])


def test_declared_schedule_profiles_are_exactly_reachable():
    observed = {
        gen.schedule_profile(0, index, difficulty=band)
        for band in ("easy", "medium", "hard")
        for index in range(8)
    }
    assert observed == set(gen.SCHEDULE_PROFILES)


def test_reusable_height_lesson_probe_iterates_declared_contract():
    probe_path = TASK_DIR / "workspace" / "verify_height_lesson.py"
    assert probe_path.exists(), "authoring probe has not been implemented"
    probe_spec = importlib.util.spec_from_file_location(
        f"review_{TASK_ID}_height_probe", probe_path
    )
    assert probe_spec and probe_spec.loader
    probe = importlib.util.module_from_spec(probe_spec)
    probe_spec.loader.exec_module(probe)
    report = probe.build_report(run_racket=False)
    assert report["canonical"]["all_mirror_exact"]
    assert report["generated"]["all_lawful"]
    assert report["generated"]["all_witnesses_fire"]
    assert report["generated"]["every_declared_rival_refuted"]
    assert report["counterexample"]["intended_differs_from_every_declared_rival"]
