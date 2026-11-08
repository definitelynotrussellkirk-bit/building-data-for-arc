"""Task-local regression suite for the clear-pair connector sampler."""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import random
import sys

import pytest

TASK_ID = "9686a12edc93"
HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import analyze, intended_output, load_generator  # noqa: E402

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def profile(grid):
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def test_rule_hash_pins_selected_authority():
    assert getattr(gen, "RULE_HASH", None) == "74f975abb98b"


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_exact_extreme_overrides_construct_and_are_observable(band):
    for requested in (
        {"grid_h": 7, "grid_w": 9, "n": 1},
        {"grid_h": 7, "grid_w": 9, "n": 5},
        {"grid_h": 16, "grid_w": 18, "n": 5},
    ):
        grid = gen.generate(17, 9, difficulty=band, **requested)
        assert gen.self_check(grid, difficulty=band, meta={"overrides": requested}) == []
        assert gen.observe_overrides(grid) == requested


@pytest.mark.parametrize(
    "kwargs",
    [
        {"sample_index": True},
        {"sample_index": -1},
        {"sample_index": 1.0},
        {"sample_index": "1"},
        {"difficulty": "expert"},
        {"overrides": {"typo": 1}},
        {"overrides": {"grid_h": 6}},
        {"overrides": {"grid_h": 17}},
        {"overrides": {"grid_w": True}},
        {"overrides": {"grid_w": 8.5}},
        {"overrides": {"n": 0}},
        {"overrides": {"n": 6}},
        {"overrides": {"n": "2"}},
    ],
)
def test_invalid_calls_are_rejected(kwargs):
    sample_index = kwargs.get("sample_index", 0)
    difficulty = kwargs.get("difficulty")
    overrides = kwargs.get("overrides", {})
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, sample_index, difficulty=difficulty, **overrides)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_explicit_axis_draw_contains_one_real_blocked_counterexample(band):
    # An override request is a direct single-instance API, so it always returns
    # the discriminating blocked lesson rather than relying on schedule context.
    for index in range(24):
        requested_n = 1 + index % 5
        grid = gen.generate(700 + index, index, difficulty=band, n=requested_n)
        facts = analyze(grid)
        assert facts["errors"] == []
        assert gen.self_check(grid) == []
        assert len(facts["clear"]) == requested_n
        assert len(facts["blocked"]) == 1
        assert not facts["unaligned"]
        assert all(len(cells) == 2 for cells in facts["by_color"].values())
        blockers = facts["blocked"][0]["blockers"]
        assert len(blockers) == 1
        assert any(blockers[0] in record["cells"] for record in facts["clear"])
        assert intended_output(grid) != intended_output(grid, ignore_blockers=True)


def test_default_schedule_interleaves_canonical_palette_roles_and_blocked_lessons():
    # Residues 0 and 2 mirror canonical examples: every input color survives.
    # Residues 1, 3 and 4 carry the blocker counterexample.  Thus every three
    # consecutive examples includes a blocker, while defect-lint also observes
    # canonical palette-role support.
    for band in (None, "easy", "medium", "hard"):
        expected_n = {0: 3, 1: 2, 2: 4, 3: {None: 4, "easy": 2, "medium": 3, "hard": 5}[band], 4: 1}
        for index in range(20):
            grid = gen.generate(1700 + index, index, difficulty=band)
            facts = analyze(grid)
            residue = index % 5
            assert len(facts["clear"]) == expected_n[residue]
            assert len(facts["blocked"]) == (0 if residue in {0, 2} else 1)
            output = intended_output(grid)
            input_colors = {value for row in grid for value in row if value}
            output_colors = {value for row in output for value in row if value}
            if residue in {0, 2}:
                assert input_colors == output_colors
            else:
                assert len(input_colors - output_colors) == 1
                assert output != intended_output(grid, ignore_blockers=True)


def test_declared_shortcut_fits_all_canonical_pairs_and_generated_witness_refutes_it():
    from reviewer_support import canonical_pairs, find_root

    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert pairs
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert intended_output(pair["input"]) == pair["output"]
        assert intended_output(pair["input"], ignore_blockers=True) == pair["output"]

    witness = gen.generate(91, 4, grid_h=7, grid_w=9, n=1)
    canonical = intended_output(witness)
    rival = intended_output(witness, ignore_blockers=True)
    assert canonical != rival
    assert gen.SEMANTIC_WITNESSES["blocked_pair"](witness)
    assert gen.SEMANTIC_RIVALS["ignore_clearance"](witness) == rival
    assert gen.CANONICAL_SHORTCUTS["ignore_clearance"](witness) == rival
    assert gen.LESSON_COMPETITORS["ignore_clearance"](witness) == rival
    assert gen.WITNESS_RIVALS == {"blocked_pair": ["ignore_clearance"]}


def test_every_three_demo_window_refutes_ignore_clearance():
    for band in ("easy", "medium", "hard"):
        for start in range(15):
            demos = [gen.generate(917263, start + offset, difficulty=band) for offset in range(3)]
            assert any(
                intended_output(grid) != intended_output(grid, ignore_blockers=True)
                for grid in demos
            )


def test_default_schedule_covers_exact_canonical_profiles_in_every_band():
    canonical_profiles = {(8, 9, 4), (9, 10, 4), (10, 10, 5)}
    for band in ("easy", "medium", "hard"):
        seen = set()
        counts = set()
        for index in range(40):
            grid = gen.generate(3100, index, difficulty=band)
            assert grid == gen.generate(3100, index, difficulty=band)
            assert gen.self_check(grid) == []
            seen.add(profile(grid))
            counts.add(gen.observe_overrides(grid)["n"])
        assert seen & canonical_profiles
        assert 1 in counts
        assert max(counts) >= {"easy": 2, "medium": 3, "hard": 5}[band]


def test_layout_varies_both_orientations_and_positions():
    clear_orientations = set()
    blocked_orientations = set()
    anchors = set()
    for index in range(96):
        grid = gen.generate(1119 + index, index, n=5)
        facts = analyze(grid)
        assert facts["errors"] == []
        for record in facts["clear"]:
            a, b = record["cells"]
            clear_orientations.add("h" if a[0] == b[0] else "v")
            anchors.add(min(record["cells"]))
        a, b = facts["blocked"][0]["cells"]
        blocked_orientations.add("h" if a[0] == b[0] else "v")
    assert clear_orientations == {"h", "v"}
    assert blocked_orientations == {"h", "v"}
    assert len(anchors) > 12


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0, 0], [0]],
        [[0, 11], [0, 0]],
        [[True, 0], [0, 0]],
        [[1, 0], [0, 0]],
        [[1, 1], [0, 0]],
    ],
)
def test_self_check_rejects_malformed_or_semantically_empty_inputs(grid):
    assert gen.self_check(grid)


def test_self_check_detects_destructive_mutations():
    grid = gen.generate(31, 8, grid_h=8, grid_w=9, n=3)
    assert gen.self_check(grid) == []

    extra = deepcopy(grid)
    color = next(value for row in grid for value in row if value)
    placed = False
    for r, row in enumerate(extra):
        for c, value in enumerate(row):
            if value == 0:
                extra[r][c] = color
                placed = True
                break
        if placed:
            break
    assert gen.self_check(extra)

    erased = deepcopy(grid)
    for r, row in enumerate(erased):
        for c, value in enumerate(row):
            if value:
                erased[r][c] = 0
                break
        else:
            continue
        break
    assert gen.self_check(erased)


def test_replay_is_fresh_and_global_random_state_is_untouched():
    random.seed(321)
    before = random.getstate()
    first = gen.generate(404, 5, difficulty="hard")
    after = random.getstate()
    second = gen.generate(404, 5, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 8 if first[0][0] != 8 else 7
    assert first != second


def test_selected_racket_authority_matches_independent_oracle():
    from arcpuzzles import Catalog
    from reviewer_support import canonical_pairs, find_root

    root = find_root(__file__)
    pairs = canonical_pairs(TASK_ID, root=root)
    grids = [pair["input"] for pair in pairs]
    grids += [
        gen.generate(51000 + band_index, index, difficulty=band)
        for band_index, band in enumerate(("easy", "medium", "hard"))
        for index in range(4)
    ]
    receipt = Catalog(root).apply(TASK_ID, grids, reference="canonical", timeout=180)
    assert receipt["rule_hash_matches_catalog"]
    assert all(item["error"] is None for item in receipt["results"])
    assert [item["output"] for item in receipt["results"]] == [
        intended_output(grid) for grid in grids
    ]
