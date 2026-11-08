"""Task-local regression tests for the L-triomino rotation sampler.

The oracle below is deliberately independent of generator implementation and of
Racket source.  It reconstructs monochrome 4-connected objects from pixels and
rotates each tight object bounding box clockwise.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import json
import os
import subprocess
import sys

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "371eb0221101"
ROOT = find_root(__file__)
gen, SOURCE_PATH, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and
                            (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append((color, tuple(sorted(cells))))
    return result


def _rotate_component_cw(cells):
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    r1 = max(r for r, _ in cells)
    # For local (r,c) in an h x w box, CW90 is (c, h-1-r).
    h = r1 - r0 + 1
    raw = [(c - c0, h - 1 - (r - r0)) for r, c in cells]
    min_r = min(r for r, _ in raw)
    min_c = min(c for _, c in raw)
    return tuple(sorted((r0 + r - min_r, c0 + c - min_c) for r, c in raw))


def oracle_output(grid, *, color_six_only=False):
    out = [[0 for _ in row] for row in grid]
    for color, cells in _components(grid):
        target = cells if color_six_only and color != 6 else _rotate_component_cw(cells)
        for r, c in target:
            out[r][c] = color
    return out


def observed(grid):
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_blobs": len(_components(grid)),
        "n_colors": len({v for row in grid for v in row if v}),
    }


def test_metadata_is_minimal_and_bound_to_selected_rule():
    assert gen.GENERATOR_ID == TASK_ID == gen.TASK_ID
    assert gen.RULE_HASH == "27c74d38508a"
    assert set(gen.AXES) == {"grid_h", "grid_w", "n_blobs", "n_colors"}
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


@pytest.mark.parametrize(
    "pair",
    canonical_pairs(TASK_ID, root=ROOT, labeled_only=True),
    ids=lambda p: f"{p['split']}{p['pair_index']}",
)
def test_canonical_inputs_are_lawful_and_independent_oracle_matches(pair):
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert oracle_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        {"grid_h": 7, "grid_w": 7, "n_blobs": 2, "n_colors": 1},
        {"grid_h": 7, "grid_w": 7, "n_blobs": 4, "n_colors": 2},
        {"grid_h": 14, "grid_w": 14, "n_blobs": 2, "n_colors": 2},
        {"grid_h": 14, "grid_w": 14, "n_blobs": 4, "n_colors": 1},
    ],
)
def test_every_advertised_override_combination_is_constructive_and_exact(band, options):
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options
    assert oracle_output(grid) == gen._rotate_all_objects_cw(grid)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"typo": 1},
        {"grid_h": 6}, {"grid_h": 15},
        {"grid_w": 6}, {"grid_w": 15},
        {"n_blobs": 1}, {"n_blobs": 5},
        {"n_colors": 0}, {"n_colors": 3},
        {"grid_h": True}, {"grid_w": 8.0},
        {"n_blobs": "2"}, {"n_colors": False},
    ],
)
def test_invalid_overrides_are_rejected(kwargs):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **kwargs)


@pytest.mark.parametrize(
    "seed,index,difficulty",
    [
        (True, 0, None),
        (0.0, 0, None),
        (0, True, None),
        (0, -1, None),
        (0, 0, "expert"),
        (0, 0, 0.5),
    ],
)
def test_invalid_call_metadata_is_rejected(seed, index, difficulty):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(seed, index, difficulty=difficulty)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_defaults_are_deterministic_lawful_and_cover_the_declared_manifold(band):
    shapes = set()
    counts = set()
    colors = set()
    orientations = set()
    for index in range(192):
        grid = gen.generate(3100 + index, index * 7, difficulty=band)
        assert grid == gen.generate(3100 + index, index * 7, difficulty=band)
        assert gen.self_check(grid) == []
        assert oracle_output(grid) == gen._rotate_all_objects_cw(grid)
        obs = observed(grid)
        shapes.add((obs["grid_h"], obs["grid_w"]))
        counts.add(obs["n_blobs"])
        colors.add(obs["n_colors"])
        for _, cells in _components(grid):
            r0 = min(r for r, _ in cells)
            c0 = min(c for _, c in cells)
            orientations.add(tuple(sorted((r-r0, c-c0) for r, c in cells)))
    assert len(shapes) >= 18
    assert counts == {2, 3, 4}
    assert colors == {1, 2}
    assert len(orientations) == 4


def test_profile_floor_shape_support_is_present_in_each_band():
    canonical_profiles = {(8, 10, 1), (9, 9, 1), (7, 11, 1)}
    envelope = lambda p: 7 <= p[0] <= 9 and 9 <= p[1] <= 11 and p[2] == 1
    pooled_exact = pooled_envelope = 0
    for band in ("easy", "medium", "hard"):
        profiles = []
        for index in range(20):
            grid = gen.generate(9700 + index, index, difficulty=band)
            obs = observed(grid)
            profiles.append((obs["grid_h"], obs["grid_w"], obs["n_colors"]))
        exact = sum(p in canonical_profiles for p in profiles)
        envelope_count = sum(envelope(p) for p in profiles)
        assert exact >= 1, (band, profiles)
        pooled_exact += exact
        pooled_envelope += envelope_count
    assert pooled_exact >= 3
    assert pooled_envelope >= 15


@pytest.mark.parametrize(
    "mutation",
    [
        "empty", "ragged", "bool_cell", "bad_color", "erase_cell",
        "extra_cell", "bridge_objects", "too_few_objects", "too_many_objects",
    ],
)
def test_validator_rejects_malformed_or_out_of_domain_grids(mutation):
    grid = gen.generate(71, 8, grid_h=9, grid_w=9, n_blobs=3, n_colors=2)
    if mutation == "empty":
        grid = []
    elif mutation == "ragged":
        grid[0].pop()
    elif mutation == "bool_cell":
        grid[0][0] = True
    elif mutation == "bad_color":
        grid[0][0] = 10
    elif mutation == "erase_cell":
        r, c = _components(grid)[0][1][0]
        grid[r][c] = 0
    elif mutation == "extra_cell":
        color, cells = _components(grid)[0]
        occupied = {p for _, comp in _components(grid) for p in comp}
        for r, c in cells:
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                p = (r+dr, c+dc)
                if 0 <= p[0] < len(grid) and 0 <= p[1] < len(grid[0]) and p not in occupied:
                    grid[p[0]][p[1]] = color
                    break
            else:
                continue
            break
    elif mutation == "bridge_objects":
        # An isolated valid L added diagonally adjacent to an existing object
        # violates the generator's one-cell separation contract.
        grid = [[0] * 9 for _ in range(9)]
        for r, c in ((1, 1), (2, 1), (2, 2)):
            grid[r][c] = 3
        for r, c in ((3, 3), (3, 4), (4, 3)):
            grid[r][c] = 4
    elif mutation == "too_few_objects":
        grid = [[0] * 9 for _ in range(9)]
        for r, c in ((1, 1), (2, 1), (2, 2)):
            grid[r][c] = 3
    elif mutation == "too_many_objects":
        grid = gen.generate(71, 8, grid_h=14, grid_w=14, n_blobs=4, n_colors=2)
        for r, c in ((11, 11), (12, 11), (12, 12)):
            grid[r][c] = 7
    assert gen.self_check(grid), mutation


def test_color_six_shortcut_fits_all_canonical_pairs_but_generated_witness_refutes_it():
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert all(oracle_output(p["input"], color_six_only=True) == p["output"] for p in pairs)

    grid = gen.generate(412, 3, grid_h=8, grid_w=10, n_blobs=3, n_colors=1)
    assert gen.self_check(grid) == []
    assert gen.SEMANTIC_WITNESSES["non_six_object"](grid)
    intended = oracle_output(grid)
    rival = gen.SEMANTIC_RIVALS["rotate_color_six_only"](grid)
    assert rival == oracle_output(grid, color_six_only=True)
    assert rival != intended
    assert gen.CANONICAL_SHORTCUTS["rotate_color_six_only"](grid) == rival
    assert gen.LESSON_COMPETITORS["rotate_color_six_only"](grid) == rival


def test_retained_color_six_counterexample_replays_exactly():
    # The portable task-test runtime loads the selected module from
    # puzzle_generators/per_puzzle/... while retaining reviewer artifacts under
    # generators/...; resolve through find_root rather than assuming siblings.
    path = ROOT / "generators" / TASK_ID / "counterexamples" / "rotate_color_six_only.json"
    record = json.loads(path.read_text(encoding="utf-8"))
    assert record["schema"] == "arcpuzzles-generator-counterexample-v1"
    assert record["task_id"] == TASK_ID
    assert record["generator_sha256"] == SOURCE_SHA256
    assert record["input"] == gen.generate(
        record["seed"], record["sample_index"], **record["overrides"]
    )
    assert gen.self_check(record["input"]) == []
    assert oracle_output(record["input"]) == record["racket_output"]
    assert oracle_output(record["input"], color_six_only=True) == record["rival_output"]
    assert record["racket_output"] != record["rival_output"]


def test_generation_does_not_mutate_and_python_hash_seed_is_irrelevant():
    grid = gen.generate(511, 9, difficulty="hard")
    before = deepcopy(grid)
    gen._rotate_all_objects_cw(grid)
    assert grid == before

    script = (
        "from reviewer_support import find_root,load_selected_generator;"
        "import json,sys;root=find_root(sys.argv[1]);"
        f"g=load_selected_generator('{TASK_ID}',root=root)[0];"
        "print(json.dumps(g.generate(511,9,difficulty='hard')))"
    )
    outputs = []
    for hash_seed in ("1", "98765"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        outputs.append(subprocess.check_output(
            [sys.executable, "-B", "-c", script, str(SOURCE_PATH)],
            cwd=str(ROOT), env=env, text=True,
        ))
    assert outputs[0] == outputs[1]
