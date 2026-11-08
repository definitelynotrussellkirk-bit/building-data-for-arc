"""Regression and semantic-contract tests for 20b53e0c4957."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import os
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "20b53e0c4957"
HOME = Path(__file__).resolve().parents[1]
GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", GENERATOR_PATH)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def _split(grid):
    h, w = len(grid), len(grid[0])
    assert (w - 2) % 3 == 0
    pw = (w - 2) // 3
    return [
        [list(row[:pw]) for row in grid],
        [list(row[pw + 1 : 2 * pw + 1]) for row in grid],
        [list(row[2 * pw + 2 :]) for row in grid],
    ]


def _cells(panel):
    return {(r, c) for r, row in enumerate(panel) for c, value in enumerate(row) if value != 0}


def _bbox(cells):
    return (
        min(r for r, _ in cells),
        min(c for _, c in cells),
        max(r for r, _ in cells),
        max(c for _, c in cells),
    )


def intended_output(grid):
    """Independent transcription of the pinned Racket authority."""
    a, b, c = _split(grid)
    cells_a = _cells(a)
    cells_b = _cells(b)
    ar0, ac0, _, _ = _bbox(cells_a)
    cr0, cc0, _, _ = _bbox(_cells(c))
    removed = {(r - ar0, col - ac0) for r, col in cells_a - cells_b}
    out = deepcopy(c)
    for rr, cc in removed:
        row, col = cr0 + rr, cc0 + cc
        if 0 <= row < len(out) and 0 <= col < len(out[0]):
            out[row][col] = 0
    return out


def recolor_b_absolute(grid):
    """Canonical-fitting shortcut: ignore A/C geometry and recolor panel B."""
    _, b, c = _split(grid)
    color = next(value for row in c for value in row if value)
    return [[color if value else 0 for value in row] for row in b]


def copy_b_to_c_bbox(grid):
    """Canonical-fitting shortcut: normalize B and paste it at C's bbox."""
    _, b, c = _split(grid)
    b_cells = _cells(b)
    c_cells = _cells(c)
    br0, bc0, br1, bc1 = _bbox(b_cells)
    cr0, cc0, _, _ = _bbox(c_cells)
    color = next(value for row in c for value in row if value)
    out = [[0 for _ in row] for row in c]
    for r, col in b_cells:
        rr, cc = cr0 + (r - br0), cc0 + (col - bc0)
        if 0 <= rr < len(out) and 0 <= cc < len(out[0]):
            out[rr][cc] = color
    return out


def absolute_removed_positions(grid):
    """Canonical-fitting shortcut: use A/B panel coordinates, not bbox transfer."""
    a, b, c = _split(grid)
    out = deepcopy(c)
    for r, col in _cells(a) - _cells(b):
        if 0 <= r < len(out) and 0 <= col < len(out[0]):
            out[r][col] = 0
    return out


def _panel_facts(grid):
    a, b, c = _split(grid)
    a_cells, b_cells, c_cells = _cells(a), _cells(b), _cells(c)
    abox, cbbox = _bbox(a_cells), _bbox(c_cells)
    query_bbox_area = (cbbox[2] - cbbox[0] + 1) * (cbbox[3] - cbbox[1] + 1)
    return {
        "a_bbox": abox,
        "c_bbox": cbbox,
        "removed": len(a_cells - b_cells),
        "query_holes": query_bbox_area - len(c_cells),
    }


def test_rule_pin_and_minimal_exact_axis_contract():
    assert GEN.RULE_HASH == "9217dc891941"
    assert GEN.EXAMPLES_NEEDED == 3
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert set(GEN.AXES) == {"panel_h", "panel_w", "n_removed", "palette_id"}


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "panel_h,panel_w,n_removed,palette_id",
    [(4, 4, 1, 0), (4, 7, 6, 2), (8, 4, 6, 1), (8, 7, 1, 2)],
)
def test_exact_overrides_are_constructive_and_observable(
    band, panel_h, panel_w, n_removed, palette_id
):
    grid = GEN.generate(
        183,
        7,
        difficulty=band,
        panel_h=panel_h,
        panel_w=panel_w,
        n_removed=n_removed,
        palette_id=palette_id,
    )
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == {
        "panel_h": panel_h,
        "panel_w": panel_w,
        "n_removed": n_removed,
        "palette_id": palette_id,
    }
    assert intended_output(grid) == GEN.rule_mirror(grid)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"panel_h": 3},
        {"panel_h": 9},
        {"panel_w": 3},
        {"panel_w": 8},
        {"n_removed": 0},
        {"n_removed": 7},
        {"palette_id": -1},
        {"palette_id": 3},
        {"panel_h": True},
        {"panel_w": 4.5},
        {"n_removed": "2"},
        {"unknown_axis": 1},
    ],
)
def test_invalid_controls_are_rejected(kwargs):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **kwargs)


def test_canonical_inputs_are_accepted_and_oracle_matches_labels():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert len(pairs) == 3
    for pair in pairs:
        original = deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert intended_output(pair["input"]) == pair["output"]
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_declared_shortcuts_really_fit_every_canonical_pair():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    independent = {
        "recolor_b_absolute": recolor_b_absolute,
        "copy_b_to_c_bbox": copy_b_to_c_bbox,
        "absolute_removed_positions": absolute_removed_positions,
    }
    assert set(GEN.CANONICAL_SHORTCUTS) == set(independent)
    for name, shortcut in independent.items():
        assert all(shortcut(pair["input"]) == pair["output"] for pair in pairs), name
        assert all(GEN.CANONICAL_SHORTCUTS[name](pair["input"]) == pair["output"] for pair in pairs), name


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_generated_example_is_a_bbox_transfer_witness(band):
    for index in range(32):
        grid = GEN.generate(900 + index, index, difficulty=band)
        truth = intended_output(grid)
        facts = _panel_facts(grid)
        assert GEN.self_check(grid) == []
        assert facts["a_bbox"][:2] != facts["c_bbox"][:2]
        assert facts["query_holes"] >= 1
        assert 1 <= facts["removed"] <= 6
        assert recolor_b_absolute(grid) != truth
        assert copy_b_to_c_bbox(grid) != truth
        assert absolute_removed_positions(grid) != truth
        assert GEN.rule_mirror(grid) == truth
        assert all(rival(grid) != truth for rival in GEN.SEMANTIC_RIVALS.values())
        assert all(witness(grid) for witness in GEN.SEMANTIC_WITNESSES.values())


def test_validator_rejects_the_two_retained_degenerate_controls():
    identical = [
        [4, 4, 4, 5, 4, 4, 4, 5, 6, 6, 6],
        [4, 4, 4, 5, 4, 4, 4, 5, 6, 6, 6],
        [4, 4, 4, 5, 4, 4, 4, 5, 6, 6, 6],
    ]
    no_panel_c = [
        [4, 4, 4, 5, 4, 0, 4, 5, 0, 0, 0],
        [4, 4, 4, 5, 4, 4, 4, 5, 0, 0, 0],
        [4, 4, 4, 5, 4, 4, 4, 5, 0, 0, 0],
    ]
    assert GEN.self_check(identical)
    assert GEN.self_check(no_panel_c)


def test_validator_rejects_relationship_and_geometry_near_misses():
    good = GEN.generate(41, 9, panel_h=6, panel_w=6, n_removed=3, palette_id=0)
    assert GEN.self_check(good) == []
    pw = (len(good[0]) - 2) // 3

    no_separator = deepcopy(good)
    no_separator[0][pw] = 0
    assert GEN.self_check(no_separator)

    extra_b_cell = deepcopy(good)
    a, b, _ = _split(extra_b_cell)
    target = next((r, c) for r in range(len(a)) for c in range(len(a[0])) if a[r][c] == 0)
    extra_b_cell[target[0]][pw + 1 + target[1]] = next(value for row in b for value in row if value)
    assert GEN.self_check(extra_b_cell)

    wrong_c_color = deepcopy(good)
    color_a = next(value for row in a for value in row if value)
    for r in range(len(good)):
        for c in range(2 * pw + 2, 3 * pw + 2):
            if wrong_c_color[r][c] != 0:
                wrong_c_color[r][c] = color_a
    assert GEN.self_check(wrong_c_color)


@pytest.mark.parametrize("bad", [None, [], [[]], [[0], [0, 1]], [[True] * 14 for _ in range(4)]])
def test_malformed_inputs_are_diagnostic_not_exceptions(bad):
    assert GEN.self_check(bad)


def test_default_distribution_hits_exact_canonical_profile_in_native_20_draw_census():
    canonical_profiles = {(3, 11, 4), (4, 14, 4)}
    for band in ("easy", "medium", "hard"):
        hits = 0
        for index in range(20):
            digest = hashlib.sha256(
                f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
            ).hexdigest()
            seed = int(digest[:12], 16)
            grid = GEN.generate(seed, seed % 7919 + index, difficulty=band)
            profile = (
                len(grid),
                len(grid[0]),
                len({value for row in grid for value in row}),
            )
            hits += profile in canonical_profiles
        assert hits >= 1, (band, hits)


def test_generation_is_deterministic_fresh_and_pure():
    for band in (None, "easy", "medium", "hard"):
        for index in range(20):
            first = GEN.generate(77, index, difficulty=band)
            second = GEN.generate(77, index, difficulty=band)
            assert first == second
            assert first is not second
            assert all(a is not b for a, b in zip(first, second))
            original = deepcopy(first)
            GEN.rule_mirror(first)
            for rival in GEN.SEMANTIC_RIVALS.values():
                rival(first)
            for witness in GEN.SEMANTIC_WITNESSES.values():
                witness(first)
            assert first == original


def test_packaged_repair_witnesses_replay_against_final_source():
    import json

    path = HOME / "counterexamples/review-67927c57be9a8517/repair_witnesses.json"
    witness = json.loads(path.read_text())
    assert witness["task_id"] == TASK_ID
    assert witness["baseline_generator_sha256"] == (
        "58a47cd3170341e7726dfc00d66f91319782b05c49ca8fb269eba692de902161"
    )
    assert witness["final_generator_sha256"] == hashlib.sha256(
        GENERATOR_PATH.read_bytes()
    ).hexdigest()
    for case in witness["validator_rejections"]:
        assert GEN.self_check(case["input"]), case["id"]

    args = witness["semantic_counterexample"]["generate"]
    grid = GEN.generate(
        args["seed"],
        args["sample_index"],
        difficulty=args["difficulty"],
        **args["overrides"],
    )
    assert grid == witness["semantic_counterexample"]["input"]
    truth = GEN.rule_mirror(grid)
    assert all(rival(grid) != truth for rival in GEN.SEMANTIC_RIVALS.values())
