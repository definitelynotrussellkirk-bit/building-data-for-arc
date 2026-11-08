from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "6d19cd1698b1"
GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.6d19cd1698b1.generator"
)


def _canonical_row():
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"missing canonical row for {TASK_ID}")


def _normalized_hash(code: str) -> str:
    return hashlib.sha256(" ".join(code.split()).encode()).hexdigest()[:12]


def test_metadata_and_rule_hash_pin():
    row = _canonical_row()
    assert GEN.VERSION == "2.1.0"
    assert GEN.RULE_HASH == _normalized_hash(row["program_solution"])
    assert set(GEN.AXES) == {"grid_h", "grid_w", "scene_profile"}


def test_all_canonical_inputs_are_accepted_and_mirror_exactly():
    row = _canonical_row()
    pairs = list(row["train"]) + list(row["test"])
    assert len(pairs) == 4
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
@pytest.mark.parametrize("profile", GEN.SCENE_PROFILES)
@pytest.mark.parametrize("height,width", [(3, 7), (10, 14)])
def test_every_exact_profile_survives_both_dimension_boundaries(
    difficulty, profile, height, width
):
    grid = GEN.generate(
        1701,
        29,
        difficulty=difficulty,
        grid_h=height,
        grid_w=width,
        scene_profile=profile,
    )
    assert GEN.self_check(
        grid,
        difficulty=difficulty,
        meta={
            "overrides": {
                "grid_h": height,
                "grid_w": width,
                "scene_profile": profile,
            }
        },
    ) == []
    assert GEN.observe_overrides(grid) == {
        "grid_h": height,
        "grid_w": width,
        "scene_profile": profile,
    }
    assert GEN.rule_mirror(grid) != grid


def test_default_draws_are_valid_observable_and_seed_sensitive():
    seen = set()
    profiles = set()
    for difficulty in ("easy", "medium", "hard"):
        # A version bump changes the keyed seed stream. Use a broader census
        # instead of relying on 30 independent scene-profile draws.
        for seed in range(256):
            grid = GEN.generate(seed, seed + 5, difficulty=difficulty)
            assert GEN.self_check(grid, difficulty=difficulty) == []
            observed = GEN.observe_overrides(grid)
            profiles.add(observed["scene_profile"])
            seen.add(tuple(map(tuple, grid)))
    assert profiles == set(GEN.SCENE_PROFILES)
    assert len(seen) >= 300


def test_shared_flank_is_owned_by_the_right_hand_run():
    grid = GEN.generate(
        11,
        7,
        difficulty="medium",
        grid_h=5,
        grid_w=10,
        scene_profile="shared_flank",
    )
    analysis = GEN._analysis(grid)
    assert analysis["scene_profile"] == "shared_flank"
    assert len(analysis["shared_write_cells"]) == 1
    cell = tuple(analysis["shared_write_cells"][0])
    writes = [
        write
        for write in analysis["writes"]
        if (write["row"], write["col"]) == cell
    ]
    assert len(writes) == 2
    assert writes[0]["color"] != writes[1]["color"]
    assert analysis["output"][cell[0]][cell[1]] == writes[-1]["color"]


def test_adjacent_color_runs_do_not_create_a_shared_zero_flank():
    grid = GEN.generate(
        19,
        3,
        difficulty="hard",
        grid_h=6,
        grid_w=11,
        scene_profile="adjacent_colors",
    )
    analysis = GEN._analysis(grid)
    assert 0 in analysis["gaps"]
    assert analysis["shared_write_cells"] == []
    touching = [
        (left, right)
        for runs in analysis["row_runs"].values()
        for left, right in zip(runs, runs[1:])
        if right["start"] == left["end"] + 1
    ]
    assert touching
    assert all(left["color"] != right["color"] for left, right in touching)


@pytest.mark.parametrize(
    "profile,left,right",
    [
        ("left_edge", True, False),
        ("right_edge", False, True),
        ("both_edges", True, True),
    ],
)
def test_edge_profiles_expose_the_promised_branch(profile, left, right):
    grid = GEN.generate(
        23,
        41,
        difficulty="medium",
        grid_h=6,
        grid_w=9,
        scene_profile=profile,
    )
    analysis = GEN._analysis(grid)
    assert analysis["left_edge"] is left
    assert analysis["right_edge"] is right


def test_mixed_profile_combines_same_row_runs_with_at_least_one_edge():
    grid = GEN.generate(23, 41, difficulty="medium", grid_h=6, grid_w=9, scene_profile="mixed")
    analysis = GEN._analysis(grid)
    assert any(len(runs) >= 2 for runs in analysis["row_runs"].values())
    assert analysis["left_edge"] or analysis["right_edge"]


def test_replay_is_deterministic_but_returns_fresh_objects():
    kwargs = dict(
        difficulty="hard",
        grid_h=8,
        grid_w=12,
        scene_profile="mixed",
    )
    first = GEN.generate(991, 4, **kwargs)
    second = GEN.generate(991, 4, **kwargs)
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9
    assert second == GEN.generate(991, 4, **kwargs)


def test_generation_does_not_touch_process_global_random_state():
    random.seed(8821)
    before = random.getstate()
    GEN.generate(77, 88, difficulty="medium")
    after = random.getstate()
    assert after == before


def test_unknown_controls_and_difficulty_reject_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 1, texture="warm")
    with pytest.raises(ValueError, match="unknown difficulty"):
        GEN.generate(1, 1, difficulty="extreme")
    with pytest.raises(ValueError):
        GEN.generate(1, 1, grid_h=2)
    with pytest.raises(ValueError):
        GEN.generate(1, 1, scene_profile="not-a-profile")


def test_self_check_rejects_targeted_structural_impostors():
    impostors = {
        "all_background": [[0] * 7 for _ in range(3)],
        "one_run": [
            [0] * 7,
            [0, 2, 2, 0, 0, 0, 0],
            [0] * 7,
        ],
        "solid_2x2": [
            [0] * 7,
            [0, 2, 2, 0, 0, 0, 0],
            [0, 2, 2, 0, 0, 0, 0],
        ],
        "no_rule_fire": [
            [2] * 7,
            [3] * 7,
            [0] * 7,
        ],
        "no_blank_row": [
            [0, 2, 2, 0, 0, 0, 0],
            [0, 3, 3, 0, 0, 0, 0],
            [0, 4, 4, 0, 0, 0, 0],
        ],
    }
    for name, grid in impostors.items():
        assert GEN.self_check(grid), name


def test_negative_recombination_is_rejected_while_oracle_mirror_executes():
    grid = GEN.generate(
        31,
        12,
        difficulty="easy",
        grid_h=3,
        grid_w=8,
        scene_profile="independent",
    )
    existing = {value for row in grid for value in row}
    replacement_color = next(color for color in range(1, 10) if color not in existing)
    blank_row = next(index for index, row in enumerate(grid) if all(value == 0 for value in row))
    impostor = copy.deepcopy(grid)
    impostor[blank_row] = [replacement_color] * len(impostor[blank_row])
    assert replacement_color not in {
        value
        for index, row in enumerate(impostor)
        if index != blank_row
        for value in row
    }
    assert GEN.self_check(impostor)
    original = copy.deepcopy(impostor)
    output = GEN.rule_mirror(impostor)
    assert output
    assert impostor == original


def test_rule_mirror_returns_fresh_rows_and_preserves_input():
    grid = GEN.generate(44, 55, difficulty="medium", scene_profile="wide_gap")
    original = copy.deepcopy(grid)
    output = GEN.rule_mirror(grid)
    assert grid == original
    assert output is not grid
    assert all(a is not b for a, b in zip(output, grid))


def _color_envelope_rival(grid):
    """Wrong rule: grow only the two outer ends of each color in each row."""
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        colors = sorted(set(row) - {0}, key=row.index)
        for color in colors:
            positions = [c for c, value in enumerate(row) if value == color]
            for c in (positions[0] - 1, positions[-1] + 1):
                if 0 <= c < len(row) and row[c] == 0:
                    out[r][c] = color
    return out


def _two_runs_rival(grid):
    out = [row[:] for row in grid]
    _, rows = GEN._scan_runs(grid)
    for r, runs in rows.items():
        for run in runs[:2]:
            for c in (run["start"] - 1, run["end"] + 1):
                if 0 <= c < len(grid[r]) and grid[r][c] == 0:
                    out[r][c] = run["color"]
    return out


def test_new_rivals_really_fit_every_canonical_demonstration():
    for pair in _canonical_row()["train"]:
        assert _color_envelope_rival(pair["input"]) == pair["output"]
        assert _two_runs_rival(pair["input"]) == pair["output"]


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("height,width", [(3, 7), (10, 14)])
@pytest.mark.parametrize("profile,rival", [
    ("repeated_color", _color_envelope_rival),
    ("three_runs", _two_runs_rival),
])
def test_contrast_profiles_guarantee_a_counterexample(difficulty, height, width, profile, rival):
    for seed in range(8):
        kwargs = {"grid_h": height, "grid_w": width, "scene_profile": profile}
        grid = GEN.generate(seed, 19, difficulty=difficulty, **kwargs)
        assert GEN.self_check(grid, difficulty=difficulty, meta={"overrides": kwargs}) == []
        assert GEN.observe_overrides(grid) == kwargs
        assert rival(grid) != GEN.rule_mirror(grid), (seed, kwargs, grid)
        facts = GEN._analysis(grid)
        if profile == "repeated_color":
            assert any(len({run["color"] for run in runs}) < len(runs)
                       for runs in facts["row_runs"].values())
        else:
            assert any(len(runs) == 3 for runs in facts["row_runs"].values())


def test_default_distribution_actually_refutes_both_blind_spots():
    killed = {"color_envelope": 0, "two_runs": 0}
    for seed in range(160):
        grid = GEN.generate(seed, 0, difficulty="medium")
        expected = GEN.rule_mirror(grid)
        killed["color_envelope"] += _color_envelope_rival(grid) != expected
        killed["two_runs"] += _two_runs_rival(grid) != expected
    assert all(count >= 5 for count in killed.values()), killed


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_each_band_retains_canonical_scale_and_large_tail(band):
    profiles = {(len(p["input"]), len(p["input"][0]),
                 len({v for row in p["input"] for v in row}))
                for p in _canonical_row()["train"] + _canonical_row()["test"]}
    hits, large = 0, 0
    for seed in range(256):
        grid = GEN.generate(seed, 11, difficulty=band)
        hits += (len(grid), len(grid[0]), len({v for row in grid for v in row})) in profiles
        large += len(grid) >= 8 or len(grid[0]) >= 12
    assert hits >= 20, (band, hits)
    assert large >= 10, (band, large)


def test_semantic_contract_refutes_the_named_canonical_shortcuts():
    assert set(GEN.CANONICAL_SHORTCUTS) == {"color_envelope", "first_two_runs"}
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        for pair in _canonical_row()["train"]:
            assert rival(pair["input"]) == pair["output"]
    for profile in ("repeated_color", "three_runs"):
        grid = GEN.generate(1, 3, scene_profile=profile)
        assert GEN.SEMANTIC_WITNESSES[profile](grid) is True
        for name in GEN.WITNESS_RIVALS[profile]:
            assert GEN.SEMANTIC_RIVALS[name](grid) != GEN.rule_mirror(grid)


@pytest.mark.parametrize("key,value", [("grid_h", True), ("grid_w", 9.0), ("grid_h", "3")])
def test_dimension_overrides_reject_nonintegers(key, value):
    with pytest.raises(ValueError, match="must be an integer"):
        GEN.generate(1, 0, **{key: value})
