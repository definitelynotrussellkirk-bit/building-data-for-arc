"""Portable regressions for 10bc62b2de84.

The geometry oracle below is independent of the production generator.  It is
small enough to make the task's object/crop/pack contract reviewable in one
place and doubles as a future-agent diagnostic when a distribution change
breaks the teaching witness.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
import os
import random
import shutil
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "10bc62b2de84"
HOME = Path(__file__).resolve().parents[1]
ROOT = find_root(__file__)
SOURCE = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
SPEC = importlib.util.spec_from_file_location("reviewed_generator_10bc62b2de84", SOURCE)
GEN = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(GEN)


def components(grid):
    """Return nonzero 4-connected components, independent of color."""
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    result = []
    while unseen:
        start = min(unseen)
        stack = [start]
        unseen.remove(start)
        cells = []
        while stack:
            r, c = stack.pop()
            cells.append((r, c))
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                p = (r + dr, c + dc)
                if p in unseen:
                    unseen.remove(p)
                    stack.append(p)
        result.append(tuple(sorted(cells)))
    return sorted(result, key=lambda cells: min(c for _, c in cells))


def bbox(cells):
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    return min(rs), min(cs), max(rs), max(cs)


def packed_output(grid, *, align="bottom"):
    pieces = []
    for cells in components(grid):
        r1, c1, r2, c2 = bbox(cells)
        pieces.append([row[c1 : c2 + 1] for row in grid[r1 : r2 + 1]])
    out_h = max(map(len, pieces))
    out_w = sum(len(piece[0]) for piece in pieces) + len(pieces) - 1
    out = [[0] * out_w for _ in range(out_h)]
    left = 0
    for piece in pieces:
        top = 0 if align == "top" else out_h - len(piece)
        for r, row in enumerate(piece):
            for c, value in enumerate(row):
                if value:
                    out[top + r][left + c] = value
        left += len(piece[0]) + 1
    return out


def observed(grid):
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_objects": len(components(grid)),
    }


def component_heights(grid):
    return [bbox(cells)[2] - bbox(cells)[0] + 1 for cells in components(grid)]


def test_rule_hash_and_semantic_contract_are_pinned():
    assert GEN.RULE_HASH == "eb9f505d4c6b"
    assert GEN.CANONICAL_SHORTCUTS["top_aligned"] is GEN.SEMANTIC_RIVALS["top_aligned"]
    assert GEN.WITNESS_RIVALS["unequal_heights"] == ["top_aligned"]


@pytest.mark.parametrize(
    "pair",
    canonical_pairs(TASK_ID, root=ROOT, labeled_only=True),
    ids=lambda pair: f"{pair['split']}{pair['pair_index']}",
)
def test_canonical_inputs_are_accepted_and_oracle_matches_labels(pair):
    assert GEN.self_check(pair["input"]) == []
    assert packed_output(pair["input"]) == pair["output"]
    # This is the canonical ambiguity the production sampler must refute.
    assert packed_output(pair["input"], align="top") == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        {"grid_h": 6, "grid_w": 9, "n_objects": 2},
        {"grid_h": 6, "grid_w": 9, "n_objects": 6},
        {"grid_h": 14, "grid_w": 22, "n_objects": 4},
    ],
)
def test_exact_overrides_are_constructive_and_observable(band, options):
    grid = GEN.generate(73, 19, difficulty=band, **options)
    assert GEN.self_check(grid) == []
    assert observed(grid) == options
    assert GEN.observe_overrides(grid) == options
    assert len(set(component_heights(grid))) >= 2


@pytest.mark.parametrize(
    "kwargs",
    [
        {"seed": True, "sample_index": 0},
        {"seed": 1.5, "sample_index": 0},
        {"seed": "1", "sample_index": 0},
        {"seed": 1, "sample_index": True},
        {"seed": 1, "sample_index": -1},
        {"seed": 1, "sample_index": 1.5},
        {"seed": 1, "sample_index": "1"},
        {"seed": 1, "sample_index": 0, "difficulty": "expert"},
        {"seed": 1, "sample_index": 0, "typo_axis": 3},
        {"seed": 1, "sample_index": 0, "grid_h": True},
        {"seed": 1, "sample_index": 0, "grid_w": 8},
        {"seed": 1, "sample_index": 0, "n_objects": 7},
    ],
)
def test_invalid_call_scalars_and_overrides_are_rejected(kwargs):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(**kwargs)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_ordinary_draw_is_a_real_top_alignment_counterexample(band):
    for index in range(48):
        grid = GEN.generate(9000 + index, index, difficulty=band)
        assert GEN.self_check(grid) == []
        assert GEN.strict_canonical_like(grid) == []
        assert GEN.SEMANTIC_WITNESSES["unequal_heights"](grid)
        assert GEN.SEMANTIC_RIVALS["top_aligned"](grid) == packed_output(grid, align="top")
        assert GEN.SEMANTIC_RIVALS["top_aligned"](grid) != packed_output(grid)


def test_generation_is_deterministic_returns_fresh_grids_and_never_drops_objects():
    first = GEN.generate(991, 17, difficulty="hard", n_objects=6)
    pristine = deepcopy(first)
    first[0][0] = 9 if first[0][0] != 9 else 8
    second = GEN.generate(991, 17, difficulty="hard", n_objects=6)
    assert second == pristine
    assert first is not second
    assert len(components(second)) == 6


@pytest.mark.parametrize(
    "grid",
    [None, [], [[]], [[0], [0, 1]], [[True, 0], [0, 0]], [[10, 0], [0, 0]]],
)
def test_malformed_grids_return_diagnostics_instead_of_raising(grid):
    assert GEN.self_check(grid)



def test_literal_counterexample_file_refutes_the_canonical_shortcut():
    path = HOME / "counterexamples" / "top_aligned_shortcut.json"
    case = json.loads(path.read_text())
    grid = case["input"]
    assert GEN.self_check(grid) == []
    assert packed_output(grid) == case["canonical_bottom_aligned_output"]
    assert GEN.CANONICAL_SHORTCUTS["top_aligned"](grid) == case["top_aligned_rival_output"]
    assert case["top_aligned_rival_output"] != case["canonical_bottom_aligned_output"]


def test_every_advertised_integer_axis_combination_is_constructive():
    for h in range(6, 15):
        for w in range(9, 23):
            for n_objects in range(2, 7):
                grid = GEN.generate(
                    100000 + 1000 * h + 10 * w + n_objects,
                    h + w + n_objects,
                    grid_h=h,
                    grid_w=w,
                    n_objects=n_objects,
                )
                expected = {"grid_h": h, "grid_w": w, "n_objects": n_objects}
                assert GEN.observe_overrides(grid) == expected
                assert GEN.self_check(grid) == []
                assert GEN.SEMANTIC_WITNESSES["unequal_heights"](grid)


def test_generation_does_not_mutate_python_global_rng():
    random.seed(714)
    before = random.getstate()
    GEN.generate(17, 4, difficulty="hard")
    assert random.getstate() == before


@pytest.mark.skipif(
    not (os.environ.get("RACKET_PATH") or shutil.which("racket")),
    reason="Racket runtime required",
)
def test_public_racket_authority_matches_independent_pack_oracle():
    if not (ROOT / "catalog").is_dir():
        pytest.skip("Public Catalog API requires the packet/library root")
    from arcpuzzles import Catalog

    grids = [GEN.generate(811, index, difficulty=band)
             for index, band in enumerate(("easy", "medium", "hard", None))]
    literal = json.loads((HOME / "counterexamples" / "top_aligned_shortcut.json").read_text())["input"]
    grids.append(literal)
    receipt = Catalog(ROOT).apply(TASK_ID, grids, allow_unapproved=True, timeout=300)
    assert receipt["executed_rule_hash"] == GEN.RULE_HASH
    assert receipt["rule_hash_matches_catalog"] is True
    assert all(result["error"] is None for result in receipt["results"])
    assert [result["output"] for result in receipt["results"]] == [packed_output(grid) for grid in grids]
