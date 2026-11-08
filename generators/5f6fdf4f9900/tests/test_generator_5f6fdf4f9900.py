from __future__ import annotations

import hashlib
import importlib.util
import json
import random
from pathlib import Path

import pytest


TASK = "5f6fdf4f9900"


def _reviewer_support():
    """Load the helper from this test's own checkout or copied runtime."""
    for ancestor in Path(__file__).resolve().parents:
        for relative in ("reviewer_support.py", "shared/runtime/reviewer_support.py"):
            path = ancestor / relative
            if path.is_file():
                spec = importlib.util.spec_from_file_location(f"_reviewer_support_{TASK}", path)
                if spec is None or spec.loader is None:
                    raise ImportError(f"Cannot load local reviewer helper: {path}")
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                return module
    raise FileNotFoundError(f"No local reviewer_support.py ancestor for {__file__}")


SUPPORT = _reviewer_support()
ROOT = SUPPORT.find_root(__file__)
MODULE, _, _ = SUPPORT.load_selected_generator(TASK, root=ROOT)
CANONICAL = SUPPORT.canonical_path(ROOT)
DATA_ROOT = CANONICAL.parent.parent
BASE_FILES = (
    DATA_ROOT / "base/solutions/training/469497ad__5f6fdf4f9900.json",
    DATA_ROOT / "base/solutions/augmented/469497ad__5586a8e9c172.json",
)


def canonical_rows():
    rows = []
    for line in CANONICAL.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            rows.append(row)
    return rows


def independent_oracle(grid):
    scale = len({value for row in grid for value in row if value != 0})
    height, width = len(grid), len(grid[0])
    result = [[0] * (width * scale) for _ in range(height * scale)]
    directions = ((-1, -1), (-1, 1), (1, -1), (1, 1))
    corners = []
    for row in range(height):
        for col in range(width):
            value = grid[row][col]
            chosen = None
            if value == 0:
                for delta_row, delta_col in directions:
                    nr, nc = row + delta_row, col + delta_col
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] != 0
                        and grid[nr][col] == 0
                        and grid[row][nc] == 0
                    ):
                        chosen = delta_row, delta_col
                        break
            if chosen is not None:
                corners.append((row, col, "main" if chosen[0] == chosen[1] else "anti"))
            for local_row in range(scale):
                for local_col in range(scale):
                    if value:
                        out = value
                    elif chosen is None:
                        out = 0
                    elif chosen[0] == chosen[1]:
                        out = 2 if local_row == local_col else 0
                    else:
                        out = 2 if local_row == scale - 1 - local_col else 0
                    result[row * scale + local_row][col * scale + local_col] = out
    return result, corners


def frozen(grid):
    return tuple(tuple(row) for row in grid)


@pytest.mark.parametrize("index,profile", list(enumerate(MODULE.PUBLIC_PROFILES)))
def test_exact_training_public_replay(index, profile):
    training = next(row for row in canonical_rows() if row["source"] == "training")
    pair = (training["train"] + training["test"])[index]
    grid = MODULE.generate(100 + index, index, scene_profile=profile)
    assert grid == pair["input"]
    assert MODULE.rule_mirror(grid) == pair["output"]
    assert independent_oracle(grid)[0] == pair["output"]
    assert MODULE.canonical_profile_signature(grid) == profile
    assert MODULE.observe_overrides(grid) == {"scene_profile": profile}


def test_augmented_public_replay_is_the_same_semantic_set():
    augmented = next(row for row in canonical_rows() if row["source"] == "augmented")
    assert len(augmented["train"]) == 4 and augmented["test"] == []
    canonical_pairs = {
        frozen(MODULE.generate(1, 0, scene_profile=profile)): MODULE.rule_mirror(
            MODULE.generate(1, 0, scene_profile=profile)
        )
        for profile in MODULE.PUBLIC_PROFILES
    }
    for pair in augmented["train"]:
        assert frozen(pair["input"]) in canonical_pairs
        assert pair["output"] == canonical_pairs[frozen(pair["input"])]


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("profile", MODULE.GENERAL_PROFILES)
def test_every_general_profile_in_every_difficulty(profile, difficulty):
    grid = MODULE.generate(20_000 + len(profile), 7, difficulty=difficulty, scene_profile=profile)
    analysis = MODULE._analysis(grid)
    expected, corners = independent_oracle(grid)
    assert analysis["errors"] == []
    assert analysis["scene_profile"] == profile
    assert analysis["output"] == expected == MODULE.rule_mirror(grid)
    assert len(analysis["facts"]["colors"]) == int(profile[1])
    height, width = analysis["facts"]["shape"]
    density = profile.split("_", 1)[1]
    assert analysis["facts"]["foreground_count"] == MODULE._foreground_target(height, width, density)
    assert {corner[2] for corner in corners} == {"main", "anti"}
    assert MODULE.observe_overrides(grid) == {"scene_profile": profile}
    if difficulty == "easy":
        assert len(corners) == 2
    if difficulty == "hard":
        assert len(corners) >= 3


@pytest.mark.parametrize("count", range(2, 6))
@pytest.mark.parametrize("density", ["sparse", "balanced", "dense"])
def test_profile_axes_are_literal_and_recoverable(count, density):
    profile = f"n{count}_{density}"
    grid = MODULE.generate(31_000 + count, count, scene_profile=profile)
    facts = MODULE._analysis(grid)["facts"]
    assert facts["scale"] == count
    height, width = facts["shape"]
    assert facts["foreground_count"] == MODULE._foreground_target(height, width, density)
    assert len(MODULE.rule_mirror(grid)) == height * count
    assert len(MODULE.rule_mirror(grid)[0]) == width * count
    for color in facts["colors"]:
        assert MODULE._color_is_connected(grid, color)


def test_first_eligible_corner_wins_even_when_later_corner_is_also_eligible():
    grid = [[0] * 5 for _ in range(5)]
    grid[1][1] = 3  # NW of (2,2): first candidate, main diagonal.
    grid[1][3] = 4  # NE of (2,2): later candidate, anti diagonal.
    assert MODULE._corner_direction(grid, 2, 2) == (-1, -1)
    output = MODULE.rule_mirror(grid)
    block = [row[4:6] for row in output[4:6]]
    assert block == [[2, 0], [0, 2]]


def test_nonzero_cells_expand_to_solid_blocks_and_zero_corners_to_red_diagonals():
    grid = MODULE.generate(43, 4, scene_profile="n5_sparse")
    output = MODULE.rule_mirror(grid)
    scale = 5
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            block = [values[col * scale : (col + 1) * scale] for values in output[row * scale : (row + 1) * scale]]
            if grid[row][col] != 0:
                assert {value for values in block for value in values} == {grid[row][col]}
            else:
                direction = MODULE._corner_direction(grid, row, col)
                assert {value for values in block for value in values} <= {0, 2}
                assert sum(value == 2 for values in block for value in values) == (scale if direction else 0)


def test_determinism_fresh_returns_and_global_rng_independence():
    random.seed(991)
    state = random.getstate()
    first = MODULE.generate(73, 6, difficulty="medium", scene_profile="n4_dense")
    assert random.getstate() == state
    second = MODULE.generate(73, 6, difficulty="medium", scene_profile="n4_dense")
    assert first == second and first is not second and first[0] is not second[0]
    first[0][0] = 2
    assert MODULE.generate(73, 6, difficulty="medium", scene_profile="n4_dense") == second


def test_difficulty_bands_change_default_corner_complexity():
    easy_counts = []
    hard_counts = []
    for seed in range(80):
        easy = MODULE.generate(80_000 + seed, seed, difficulty="easy")
        hard = MODULE.generate(80_000 + seed, seed, difficulty="hard")
        easy_facts = MODULE._analysis(easy)["facts"]
        hard_facts = MODULE._analysis(hard)["facts"]
        if easy_facts["scene_profile"] in MODULE.GENERAL_PROFILES:
            assert len(easy_facts["corners"]) == 2
            easy_counts.append(len(easy_facts["corners"]))
        if hard_facts["scene_profile"] in MODULE.GENERAL_PROFILES:
            assert len(hard_facts["corners"]) >= 3
            hard_counts.append(len(hard_facts["corners"]))
    assert len(easy_counts) >= 60 and len(hard_counts) >= 60


def test_generated_pool_has_high_structural_and_palette_diversity():
    grids = [MODULE.generate(seed, seed + 3, scene_profile="n4_balanced") for seed in range(160)]
    signatures = {frozen(grid) for grid in grids}
    geometries = {tuple(tuple(value != 0 for value in row) for row in grid) for grid in grids}
    palettes = {tuple(sorted({value for row in grid for value in row if value})) for grid in grids}
    shapes = {(len(grid), len(grid[0])) for grid in grids}
    assert len(signatures) >= 152
    assert len(geometries) >= 145
    assert len(palettes) >= 45
    assert len(shapes) == len(MODULE._DIMENSIONS[None]) - 1


@pytest.mark.parametrize(
    "grid",
    [
        [],
        [[]],
        [[0] * 5 for _ in range(4)],
        [[0] * 5 for _ in range(7)],
        [[0] * 3 for _ in range(5)],
        [[0] * 7 for _ in range(5)],
        [[0] * 5 for _ in range(4)] + [[0] * 4],
        [[False] * 5 for _ in range(5)],
        [[10] * 5 for _ in range(5)],
        [[2] + [0] * 4 for _ in range(5)],
    ],
)
def test_malformed_grids_fail_closed(grid):
    assert MODULE.self_check(grid)
    with pytest.raises(ValueError):
        MODULE.rule_mirror(grid)


def test_semantic_mutations_fail_closed():
    grid = MODULE.generate(89, 9, scene_profile="n3_balanced")

    missing_color = [row[:] for row in grid]
    victim = next(value for row in grid for value in row if value)
    for row in range(5):
        for col in range(5):
            if missing_color[row][col] == victim:
                missing_color[row][col] = 0
    assert MODULE.self_check(missing_color)

    wrong_density = [row[:] for row in grid]
    changed = False
    for row in range(5):
        for col in range(5):
            if wrong_density[row][col] == 0 and not changed:
                wrong_density[row][col] = next(value for value in grid[row] if value) if any(grid[row]) else 3
                changed = True
    assert MODULE.self_check(wrong_density)

    red_input = [row[:] for row in grid]
    red_input[0][0] = 2
    assert MODULE.self_check(red_input)


@pytest.mark.parametrize("kwargs", [{"scene_profile": "unknown"}, {"texture": "sparse"}, {"difficulty": "expert"}])
def test_unknown_controls_fail_closed(kwargs):
    with pytest.raises(ValueError):
        MODULE.generate(1, 0, **kwargs)


def test_axis_contract_is_literal_and_minimal():
    assert set(MODULE.AXES) == {"scene_profile"}
    assert tuple(MODULE.AXES["scene_profile"]["valid"].split("|")) == MODULE.SCENE_PROFILES
    assert MODULE.HELPFUL_TEXTURES == MODULE.DEGENERATE_TEXTURES == ()


def test_rule_hash_and_all_sources_are_exactly_synchronized():
    canonical = canonical_rows()
    sources = {row["program_solution"] for row in canonical}
    assert len(sources) == 1
    source = next(iter(sources))
    digest = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
    assert MODULE.RULE_HASH == digest == "9c543a96623c"
    for path in BASE_FILES:
        base = json.loads(path.read_text())
        assert base["racket_target"]["raw_code"] == source
        assert base["racket_target"]["target_code"] == source
