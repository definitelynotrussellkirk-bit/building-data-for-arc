"""Task-local regressions for the repaired channel-wall curriculum."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (
    analyze,
    authority_target_codes,
    canonical_pairs,
    canonical_program,
    load_generator,
    oracle_output,
    racket_outputs,
    rival_fill_entire_channel,
    rival_marker_required,
    rival_split_every_marker,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


@pytest.mark.parametrize("pair", canonical_pairs(), ids=lambda pair: hashlib.sha256(json.dumps(pair["input"]).encode()).hexdigest()[:8])
def test_accepts_every_canonical_input_and_oracle_matches(pair):
    assert gen.self_check(pair["input"]) == []
    assert analyze(pair["input"])["wall_match"]
    assert oracle_output(pair["input"]) == pair["output"]


def test_rule_hash_is_pinned_to_canonical_program():
    expected = hashlib.sha256(" ".join(canonical_program().split()).encode()).hexdigest()[:12]
    assert gen.RULE_HASH == expected == "b8c560eed7ae"


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        {"grid_h": 10, "grid_w": 10, "turn_count": 6, "marker_mode": "none"},
        {"grid_h": 10, "grid_w": 20, "turn_count": 2, "marker_mode": "straight"},
        {"grid_h": 20, "grid_w": 10, "turn_count": 5, "marker_mode": "turn"},
        {"grid_h": 20, "grid_w": 20, "turn_count": 4, "marker_mode": "turn"},
    ],
)
def test_exact_overrides_are_observable_in_every_band(band, options):
    grid = gen.generate(271, 13, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert analyze(grid)["wall_match"]
    assert gen.observe_overrides(grid) == options


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 9),
        ("grid_h", 21),
        ("grid_w", True),
        ("grid_w", 10.5),
        ("turn_count", 1),
        ("turn_count", 7),
        ("turn_count", "3"),
        ("marker_mode", "marker"),
        ("marker_mode", 1),
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(key, value):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_distribution_covers_branches_geometry_and_profiles(band):
    modes: set[str] = set()
    turns: set[int] = set()
    shapes: set[tuple[int, int]] = set()
    endpoints: set[tuple[tuple[bool, bool, bool, bool], ...]] = set()
    profile_hits = 0
    unique: set[str] = set()
    for index in range(180):
        grid = gen.generate(4000 + index, index, difficulty=band)
        assert grid == gen.generate(4000 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        info = analyze(grid)
        assert info["wall_match"]
        assert info["endpoints_on_boundary"]
        assert gen.observe_overrides(grid) == {
            "grid_h": info["grid_h"],
            "grid_w": info["grid_w"],
            "turn_count": info["turn_count"],
            "marker_mode": info["marker_mode"],
        }
        truth = oracle_output(grid)
        if info["marker_mode"] == "none":
            assert rival_marker_required(grid) != truth
        elif info["marker_mode"] == "turn":
            assert rival_fill_entire_channel(grid) != truth
        else:
            assert rival_split_every_marker(grid) != truth
        modes.add(info["marker_mode"])
        turns.add(info["turn_count"])
        shapes.add((info["grid_h"], info["grid_w"]))
        h, w = info["grid_h"], info["grid_w"]
        endpoints.add(tuple((r == 0, r == h - 1, c == 0, c == w - 1) for r, c in info["endpoints"]))
        profile_hits += (h, w) == (10, 10)
        unique.add(hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest())
    assert modes == {"none", "straight", "turn"}
    assert turns == set(range(2, 7))
    assert len(shapes) >= 40
    assert len(endpoints) >= 4
    assert profile_hits >= 10
    assert len(unique) >= 170


def test_every_three_consecutive_examples_cover_all_marker_branches():
    for start in range(24):
        modes = {
            analyze(gen.generate(811, start + offset))["marker_mode"]
            for offset in range(gen.EXAMPLES_NEEDED)
        }
        assert modes == {"none", "straight", "turn"}


@pytest.mark.parametrize("mutation", ["blank", "unknown", "missing_wall", "extra_wall", "duplicate_marker", "erase_channel"])
def test_validator_rejects_destructive_mutations(mutation):
    grid = gen.generate(83, 1, grid_h=12, grid_w=12, turn_count=4, marker_mode="straight")
    info = analyze(grid)
    if mutation == "blank":
        grid = [[0 for _ in row] for row in grid]
    elif mutation == "unknown":
        grid[0][0] = 6
    elif mutation == "missing_wall":
        r, c = next(iter(info["walls"]))
        grid[r][c] = 0
    elif mutation == "extra_wall":
        point = next(
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value == 0 and (r, c) not in info["channel"]
        )
        grid[point[0]][point[1]] = 7
    elif mutation == "duplicate_marker":
        point = next(point for point in info["path"] if grid[point[0]][point[1]] == 0)
        grid[point[0]][point[1]] = 9
    elif mutation == "erase_channel":
        marker = next((point for point in info["path"] if grid[point[0]][point[1]] == 9), None)
        point = next(point for point in info["path"][1:-1] if point != marker)
        grid[point[0]][point[1]] = 7
    assert gen.self_check(grid)


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 1]], [[True] * 10 for _ in range(10)]])
def test_malformed_grid_returns_diagnostics_not_exceptions(grid):
    assert gen.self_check(grid)


def test_semantic_contract_names_real_counterexamples():
    modes = {"none": 0, "straight": 1, "turn": 2}
    expected_rivals = {
        "none": "marker_required",
        "straight": "split_every_marker",
        "turn": "fill_entire_channel",
    }
    for mode, index in modes.items():
        grid = gen.generate(1729, index, grid_h=10, grid_w=10, turn_count=4, marker_mode=mode)
        truth = oracle_output(grid)
        witness = f"{mode}_branch"
        rival = expected_rivals[mode]
        assert gen.strict_canonical_like(grid) == []
        assert gen.SEMANTIC_WITNESSES[witness](grid)
        assert rival in gen.WITNESS_RIVALS[witness]
        assert gen.SEMANTIC_RIVALS[rival](grid) != truth
        assert gen.LESSON_COMPETITORS[rival](grid) != truth


def test_active_authority_target_codes_are_exact_canonical_text():
    program = canonical_program()
    assert authority_target_codes()
    assert all(code == program for code in authority_target_codes().values())


def test_keyed_rng_is_independent_of_python_hash_seed():
    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from reference_probe import load_generator;"
        "print(json.dumps(load_generator().generate(31,8,difficulty='hard')))"
    )
    outputs = []
    for hash_seed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        outputs.append(
            subprocess.check_output(
                [sys.executable, "-B", "-c", script, str(HOME / "workspace")],
                env=env,
                text=True,
            )
        )
    assert outputs[0] == outputs[1]


def _rot90(grid):
    return [list(row) for row in zip(*grid[::-1])]


@pytest.mark.parametrize("turns,reflect", [(turns, reflect) for turns in range(4) for reflect in (False, True)])
def test_marker_branches_are_dihedrally_equivariant(turns, reflect):
    def transform(grid):
        result = deepcopy(grid)
        if reflect:
            result = [list(reversed(row)) for row in result]
        for _ in range(turns):
            result = _rot90(result)
        return result

    # The authority's no-marker component choice is intentionally row-major and
    # therefore not globally dihedral.  Marker-selected channels are equivariant.
    for index in range(12):
        grid = gen.generate(990 + index, index, marker_mode=("straight", "turn")[index % 2])
        changed = transform(grid)
        assert gen.self_check(changed) == []
        assert oracle_output(changed) == transform(oracle_output(grid))


def test_real_racket_authority_matches_independent_oracle():
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()]
    grids.extend(gen.generate(513, index, marker_mode=("none", "straight", "turn")[index % 3]) for index in range(18))
    assert racket_outputs(grids) == [oracle_output(grid) for grid in grids]


@pytest.mark.parametrize(
    "seed,sample_index,difficulty",
    [
        (True, 0, None),
        (False, 0, "easy"),
        (1.0, 0, None),
        (1.75, 0, "hard"),
        ("1", 0, "medium"),
        (1, True, None),
        (1, False, "easy"),
        (1, -1, "hard"),
        (1, 0, True),
        (1, 0, False),
        (1, 0, 0),
        (1, 0, 1.0),
        (1, 0, "__invalid_difficulty__"),
    ],
)
def test_public_call_rejects_invalid_scalar_arguments(seed, sample_index, difficulty):
    with pytest.raises(ValueError):
        gen.generate(seed, sample_index, difficulty=difficulty)
