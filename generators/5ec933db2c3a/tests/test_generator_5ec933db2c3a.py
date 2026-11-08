"""Source-linked regressions for rotated exact-two-hole template repair."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import itertools
from pathlib import Path
import random
import sys
from typing import Any

import pytest

TASK_ID = "5ec933db2c3a"
HOME = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "shared" / "runtime"))

from reviewer_support import canonical_pairs, find_root  # noqa: E402


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        f"reviewed_{TASK_ID}", HOME / "generator.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()
ROOT = find_root(__file__)


def _pairs():
    return canonical_pairs(TASK_ID, root=ROOT)


def _rotate_cw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def _rotations(grid: list[list[int]]) -> list[list[list[int]]]:
    variants: list[list[list[int]]] = []
    current = deepcopy(grid)
    for _ in range(4):
        if current not in variants:
            variants.append(deepcopy(current))
        current = _rotate_cw(current)
    return variants


def _split_and_crop(grid: list[list[int]]) -> tuple[list[list[int]], list[list[int]]]:
    h, w = len(grid), len(grid[0])
    dividers = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    assert len(dividers) == 1
    divider = dividers[0]
    left = [row[:divider] for row in grid]
    board = [row[divider + 1 :] for row in grid]
    cells = [
        (r, c)
        for r, row in enumerate(left)
        for c, value in enumerate(row)
        if value not in (0, 9)
    ]
    assert cells
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    template = [row[c0 : c1 + 1] for row in left[r0 : r1 + 1]]
    return template, board


def _compatible_windows(
    grid: list[list[int]], *, rotations: bool = True
) -> list[dict[str, Any]]:
    template, board = _split_and_crop(grid)
    variants = _rotations(template) if rotations else [template]
    matches: list[dict[str, Any]] = []
    for rotation_index, variant in enumerate(variants):
        th, tw = len(variant), len(variant[0])
        for r0 in range(len(board) - th + 1):
            for c0 in range(len(board[0]) - tw + 1):
                missing: list[tuple[int, int, int]] = []
                compatible = True
                for r, row in enumerate(variant):
                    for c, expected in enumerate(row):
                        actual = board[r0 + r][c0 + c]
                        if expected == 0:
                            if actual != 0:
                                compatible = False
                                break
                        elif actual == expected:
                            continue
                        elif actual == 0:
                            missing.append((r0 + r, c0 + c, expected))
                        else:
                            compatible = False
                            break
                    if not compatible:
                        break
                if compatible:
                    matches.append(
                        {
                            "rotation": rotation_index,
                            "row": r0,
                            "col": c0,
                            "missing": tuple(missing),
                        }
                    )
    return matches


def independent_rule(grid: list[list[int]]) -> list[list[int]]:
    """Independent mirror of the selected Racket authority."""
    _template, board = _split_and_crop(grid)
    output = deepcopy(board)
    for match in _compatible_windows(grid):
        if len(match["missing"]) != 2:
            continue
        for r, c, color in match["missing"]:
            output[r][c] = color
    return output


def _profile(grid: list[list[int]]) -> tuple[int, int, int]:
    return len(grid), len(grid[0]), len({v for row in grid for v in row})


def _pinned_seed(band: str, index: int) -> int:
    digest = hashlib.sha256(
        f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
    ).hexdigest()
    return int(digest[:12], 16)


def test_declares_small_source_bound_contract():
    assert gen.GENERATOR_ID == TASK_ID
    assert gen.TASK_ID == TASK_ID
    assert gen.VERSION == "3.0.0"
    assert gen.RULE_HASH == "009a49ded011"
    assert gen.EXAMPLES_NEEDED == 3
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert set(gen.AXES) == {"grid_h", "grid_w"}


def test_all_canonical_pairs_are_accepted_and_match_independent_oracle():
    pairs = _pairs()
    assert len(pairs) == 3
    for pair in pairs:
        original = deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert independent_rule(pair["input"]) == pair["output"]
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("grid_h,grid_w", itertools.product((7, 10), (12, 16)))
def test_boundary_overrides_are_exact_and_constructive(difficulty, grid_h, grid_w):
    requested = {"grid_h": grid_h, "grid_w": grid_w}
    grid = gen.generate(701 + grid_h, 19 + grid_w, difficulty=difficulty, **requested)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == requested
    assert independent_rule(grid) == gen.rule_mirror(grid)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"typo": 1},
        {"grid_h": 6},
        {"grid_h": 11},
        {"grid_w": 11},
        {"grid_w": 17},
        {"grid_h": True},
        {"grid_w": 12.0},
        {"grid_h": "7"},
        {"difficulty": "expert"},
    ],
)
def test_rejects_unknown_out_of_range_and_wrong_type_requests(kwargs):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **kwargs)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_generated_inputs_have_exact_targets_and_all_three_counterexamples(band):
    for index in range(80):
        grid = gen.generate(5000 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        assert independent_rule(grid) == gen.rule_mirror(grid)

        matches = _compatible_windows(grid)
        counts = [len(match["missing"]) for match in matches]
        exact = [match for match in matches if len(match["missing"]) == 2]
        assert len(exact) == 2
        assert 1 in counts
        assert 3 in counts
        assert any(match["rotation"] != 0 for match in exact)
        assert any(
            any(color == 7 for _r, _c, color in match["missing"])
            for match in exact
        )

        authority = independent_rule(grid)
        for name, rival in gen.SEMANTIC_RIVALS.items():
            assert rival(grid) != authority, name
        for name, witness in gen.SEMANTIC_WITNESSES.items():
            assert witness(grid), name


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("start", range(8))
def test_every_three_demo_window_refutes_all_declared_competitors(band, start):
    demos = []
    for offset in range(gen.EXAMPLES_NEEDED):
        index = start + offset
        grid = gen.generate(6100 + start, index, difficulty=band)
        demos.append({"input": grid, "output": independent_rule(grid)})
    assert gen.lesson_identifiable(demos, demos[0]["input"]) == []
    for name, rival in gen.LESSON_COMPETITORS.items():
        assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


def test_pinned_profile_floor_has_exact_support_in_every_band():
    canonical_profiles = {_profile(pair["input"]) for pair in _pairs()}
    for band in ("easy", "medium", "hard"):
        grids = []
        for index in range(20):
            seed = _pinned_seed(band, index)
            grids.append(gen.generate(seed, seed % 7919 + index, difficulty=band))
        assert any(_profile(grid) in canonical_profiles for grid in grids)
        assert all(gen.strict_canonical_like(grid) == [] for grid in grids)


def test_default_distribution_is_deterministic_diverse_and_fresh():
    state = random.getstate()
    signatures = set()
    for band in ("easy", "medium", "hard"):
        for index in range(40):
            first = gen.generate(8000 + index, index, difficulty=band)
            second = gen.generate(8000 + index, index, difficulty=band)
            assert first == second
            assert first is not second
            assert all(a is not b for a, b in zip(first, second))
            signatures.add(tuple(map(tuple, first)))
    assert random.getstate() == state
    assert len(signatures) >= 90


def test_rule_and_rivals_do_not_mutate_input():
    grid = gen.generate(42, 17, difficulty="hard")
    original = deepcopy(grid)
    gen.rule_mirror(grid)
    for rival in gen.SEMANTIC_RIVALS.values():
        rival(grid)
    assert grid == original


@pytest.mark.parametrize(
    "bad",
    [None, [], [[]], [[0], [0, 0]], [[True] * 12 for _ in range(7)]],
)
def test_malformed_grids_return_diagnostics_not_exceptions(bad):
    assert gen.self_check(bad)
    assert gen.strict_canonical_like(bad)
