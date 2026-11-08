"""Portable regression tests for ARC generator a0ff437161da."""
from __future__ import annotations

import copy
import hashlib
import json
import random
from collections import Counter
from pathlib import Path

import pytest

from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
)


TASK_ID = "a0ff437161da"
ROOT = find_root(__file__)
GEN, GENERATOR_PATH, GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
PAIRS = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)


def _canonical_row() -> dict:
    rows = []
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    rows.append(row)
    assert len(rows) == 1
    return rows[0]


def _base_authority_path() -> Path:
    relative = Path("data/base/solutions/training/4a1cacc2__a0ff437161da.json")
    for candidate in (ROOT / relative, ROOT / "shared" / relative):
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(relative)


def _norm_rule(source: str) -> str:
    return " ".join(source.split())




def _generic_first_color_only(grid):
    """Mirror the shared bounded searched rival used by semantic review."""
    output = GEN.rule_mirror(grid)
    colors = sorted({value for row in grid for value in row if value})
    if not colors:
        return output
    selected = {colors[0]}
    for r, row in enumerate(output):
        for c, value in enumerate(row):
            if value != grid[r][c] and value not in selected:
                output[r][c] = grid[r][c]
    return output

def _filled_rectangle(grid, corner: str):
    h, w = len(grid), len(grid[0])
    marker = next(
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 8
    )
    r, c, color = marker
    rr, cc = {
        "ul": (0, 0),
        "ur": (0, w - 1),
        "ll": (h - 1, 0),
        "lr": (h - 1, w - 1),
    }[corner]
    out = copy.deepcopy(grid)
    for y in range(min(r, rr), max(r, rr) + 1):
        for x in range(min(c, cc), max(c, cc) + 1):
            out[y][x] = color
    return out


def test_all_canonical_pairs_and_exact_public_profiles():
    assert len(PAIRS) == 5
    for profile, pair in zip(GEN.PUBLIC_PROFILES, PAIRS, strict=True):
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert GEN.canonical_profile_signature(pair["input"]) == profile
        generated = GEN.generate(1, 2, scene_profile=profile)
        assert generated == pair["input"]
        assert generated is not GEN._PUBLIC_INPUTS[profile]


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_general_profile_and_band(band):
    expected = {
        "nearest_ul": "ul",
        "nearest_ur": "ur",
        "nearest_ll": "ll",
        "nearest_lr": "lr",
        "top_tie": "ul",
        "bottom_tie": "ll",
        "left_tie": "ul",
        "right_tie": "ur",
        "four_way_tie": "ul",
    }
    for profile in GEN.GENERAL_PROFILES:
        for seed in range(25):
            grid = GEN.generate(
                seed,
                seed * 19,
                difficulty=band,
                scene_profile=profile,
            )
            analysis = GEN._analysis(grid)
            assert analysis["errors"] == []
            assert analysis["scene_profile"] == profile
            assert analysis["nearest_corner"] == expected[profile]
            assert GEN.observe_overrides(grid) == {"scene_profile": profile}


def test_rectangle_semantics():
    for profile in GEN.GENERAL_PROFILES:
        for seed in range(40):
            grid = GEN.generate(seed, seed * 23, scene_profile=profile)
            analysis = GEN._analysis(grid)
            assert analysis["output"] == _filled_rectangle(
                grid, analysis["nearest_corner"]
            )


def test_broad_first_marker_row_major():
    grid = [[8] * 7 for _ in range(6)]
    grid[1][5] = 3
    grid[4][1] = 6
    expected = copy.deepcopy(grid)
    for row in range(0, 2):
        for col in range(5, 7):
            expected[row][col] = 3
    assert GEN.rule_mirror(grid) == expected
    assert GEN.self_check(grid)


def test_default_schedule_and_distribution():
    schedule = GEN.DEFAULT_PROFILE_SCHEDULE
    assert len(schedule) == 36
    assert set(schedule) == set(GEN.SCENE_PROFILES)
    tie_profiles = set(GEN.TIE_PROFILES)
    assert set(schedule[::2]) == tie_profiles
    force_nine = GEN.DEFAULT_FORCE_NINE_SCHEDULE
    assert len(force_nine) == len(schedule)
    for start in range(len(schedule)):
        window = [schedule[(start + offset) % len(schedule)] for offset in range(4)]
        flags = [force_nine[(start + offset) % len(schedule)] for offset in range(4)]
        assert sum(profile in tie_profiles for profile in window) == 2
        assert sum(flags) == 2

    profiles = Counter()
    inputs = set()
    outputs = set()
    shapes = set()
    areas = set()
    colors = set()
    corners = set()
    for seed in range(3000):
        grid = GEN.generate(
            seed,
            seed,
            difficulty=("easy", "medium", "hard")[seed % 3],
        )
        analysis = GEN._analysis(grid)
        assert analysis["errors"] == []
        profiles[analysis["scene_profile"]] += 1
        inputs.add(tuple(map(tuple, grid)))
        outputs.add(tuple(map(tuple, analysis["output"])))
        shapes.add((len(grid), len(grid[0])))
        areas.add(analysis["rectangle_area"])
        colors.add(analysis["marker_color"])
        corners.add(analysis["nearest_corner"])
    assert set(profiles) == set(GEN.SCENE_PROFILES)
    assert len(inputs) > 2200
    assert len(outputs) > 2200
    assert len(shapes) > 150
    assert len(areas) > 40
    assert colors == {0, 1, 2, 3, 4, 5, 6, 7, 9}
    assert corners == set(GEN._CORNERS)


def test_every_default_lesson_rotation_refutes_reverse_tie_shortcut():
    rival = GEN.CANONICAL_SHORTCUTS["reverse_tie_order"]
    period = len(GEN.DEFAULT_PROFILE_SCHEDULE)
    for start in range(period):
        grids = [GEN.generate(101, start + offset) for offset in range(4)]
        assert sum(
            GEN._analysis(grid)["scene_profile"] in GEN.TIE_PROFILES
            for grid in grids
        ) == 2
        for query_index, query in enumerate(grids):
            canonical_query = GEN.rule_mirror(query)
            rival_query = rival(query)
            if canonical_query == rival_query:
                continue
            demos = [grid for index, grid in enumerate(grids) if index != query_index]
            assert any(GEN.rule_mirror(grid) != rival(grid) for grid in demos)




def test_every_default_rotation_refutes_shared_first_color_only_search_rival():
    # These exact smoke seeds were retained by the shared semantic gate; the
    # bounded rival treats nonzero background color 8 as the first color and
    # therefore skips color-9 fills unless a demonstration refutes it.
    replays = (
        ("easy", 165496162248274),
        ("medium", 182982950335887),
        ("hard", 159730443585906),
    )
    period = len(GEN.DEFAULT_PROFILE_SCHEDULE)
    for band, seed in replays:
        for start in range(period):
            grids = [
                GEN.generate(seed, start + offset, difficulty=band)
                for offset in range(4)
            ]
            for query_index, query in enumerate(grids):
                if _generic_first_color_only(query) == GEN.rule_mirror(query):
                    continue
                demos = [grid for index, grid in enumerate(grids) if index != query_index]
                assert any(
                    _generic_first_color_only(grid) != GEN.rule_mirror(grid)
                    for grid in demos
                )


def test_semantic_shortcut_fits_canonical_and_has_generated_witnesses():
    rival = GEN.CANONICAL_SHORTCUTS["reverse_tie_order"]
    assert GEN.SEMANTIC_RIVALS["reverse_tie_order"] is rival
    assert all(rival(pair["input"]) == pair["output"] for pair in PAIRS)
    for band in ("easy", "medium", "hard"):
        for profile in (
            "top_tie",
            "bottom_tie",
            "left_tie",
            "right_tie",
            "four_way_tie",
        ):
            grid = GEN.generate(73, 11, difficulty=band, scene_profile=profile)
            assert GEN.strict_canonical_like(grid) == []
            assert GEN.SEMANTIC_WITNESSES["tie_break"](grid)
            assert rival(grid) != GEN.rule_mirror(grid)


@pytest.mark.parametrize("bad", [True, False, 1.0, 1.75, "1", -1, 2**63])
def test_rejects_invalid_seed_scalars(bad):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(bad, 0)


@pytest.mark.parametrize("bad", [True, False, 1.0, 1.75, "1", -1, 2**63])
def test_rejects_invalid_sample_index_scalars(bad):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, bad)


def test_malformed_inputs_are_diagnostic():
    grid = GEN.generate(7, 11, scene_profile="four_way_tie")
    ragged = copy.deepcopy(grid)
    ragged[0].pop()
    corner = [[8] * 6 for _ in range(6)]
    corner[0][0] = 2
    multi = copy.deepcopy(grid)
    multi[0][0] = 3
    for candidate in ([], [[8]], [[True]], [[10]], ragged, corner, multi):
        assert GEN.self_check(candidate)


def test_canonical_inputs_directly_witness_singleton_grammar():
    training = [pair for pair in PAIRS if pair["split"] == "train"]
    assert training
    assert all(
        sum(value != 8 for row in pair["input"] for value in row) == 1
        for pair in training
    )


def test_errors_determinism_and_global_rng_isolation():
    for overrides in (
        {"scene_profile": "bad"},
        {"texture": "no_cell"},
        {"grid_h": 8},
    ):
        with pytest.raises(ValueError):
            GEN.generate(1, 2, **overrides)
    with pytest.raises(ValueError):
        GEN.generate(1, 2, difficulty="extreme")
    random.seed(47)
    state = random.getstate()
    first = GEN.generate(17, 23, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(17, 23, difficulty="hard")
    assert first == second
    assert first is not second


def test_selected_authority_exactly_matches_canonical_and_preserves_raw_source():
    source = _canonical_row()["program_solution"]
    expected_hash = hashlib.sha256(_norm_rule(source).encode()).hexdigest()[:12]
    assert GEN.RULE_HASH == expected_hash
    base = json.loads(_base_authority_path().read_text(encoding="utf-8"))
    raw = base["racket_target"]["raw_code"]
    target = base["racket_target"]["target_code"]
    assert target == source
    assert _norm_rule(raw) == _norm_rule(source)
    assert raw != source  # archival formatting remains intact


def test_retained_reverse_tie_counterexample_replays_exactly():
    recipe = {
        "seed": 1730,
        "sample_index": 0,
        "difficulty": "easy",
        "overrides": {"scene_profile": "top_tie"},
    }
    expected_input = [[8] * 7 for _ in range(7)]
    expected_input[1][3] = 1
    expected_authoritative = copy.deepcopy(expected_input)
    expected_rival = copy.deepcopy(expected_input)
    for row in (0, 1):
        for col in range(4):
            expected_authoritative[row][col] = 1
        for col in range(3, 7):
            expected_rival[row][col] = 1

    grid = GEN.generate(
        recipe["seed"],
        recipe["sample_index"],
        difficulty=recipe["difficulty"],
        **recipe["overrides"],
    )
    assert grid == expected_input
    assert GEN.rule_mirror(grid) == expected_authoritative
    assert GEN.CANONICAL_SHORTCUTS["reverse_tie_order"](grid) == expected_rival
    assert expected_authoritative != expected_rival

    # Counterexamples are retained in a normal repository checkout, while the
    # portable task-test snapshot intentionally contains only executable task
    # inputs. Verify the source-bound JSON whenever that documentation layer is
    # available without making portable execution depend on it.
    retained_path = (
        GENERATOR_PATH.parent
        / "counterexamples"
        / "review-cac633488d9764e2"
        / "reverse_tie_order.json"
    )
    if retained_path.is_file():
        retained = json.loads(retained_path.read_text(encoding="utf-8"))
        assert retained["source_binding"]["generator_sha256"] == GENERATOR_SHA256
        assert retained["recipe"] == recipe
        assert retained["input"] == expected_input
        assert retained["authoritative_output"] == expected_authoritative
        assert retained["rival_output"] == expected_rival
