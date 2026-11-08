"""Regression contract for the fe947dc3e12c review repair."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import random
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TASK_ID = "fe947dc3e12c"
ROOT = find_root(__file__)
GEN, GEN_PATH, GEN_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
PAIRS = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
BANDS = (None, "easy", "medium", "hard")


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen, out = set(), []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            stack, cells = [(r, c)], set()
            seen.add((r, c))
            while stack:
                cr, cc = stack.pop()
                cells.add((cr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nxt = (cr + dr, cc + dc)
                    if (0 <= nxt[0] < h and 0 <= nxt[1] < w
                            and nxt not in seen and grid[nxt[0]][nxt[1]] != 0):
                        seen.add(nxt)
                        stack.append(nxt)
            out.append(cells)
    return out


def oracle(grid):
    result = [row[:] for row in grid]
    components = sorted(_components(grid), key=len, reverse=True)
    if len(components) != 3 or len({len(cells) for cells in components}) != 3:
        raise ValueError("oracle domain is exactly three differently-sized components")
    for color, cells in zip((1, 4, 2), components):
        for r, c in cells:
            result[r][c] = color
    return result


def bbox_area_rival(grid):
    result = [row[:] for row in grid]
    def area(cells):
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        return (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)
    components = sorted(_components(grid), key=lambda cells: (-area(cells), min(cells)))
    for color, cells in zip((1, 4, 2), components):
        for r, c in cells:
            result[r][c] = color
    return result


def _canonical_source():
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row["program_solution"]
    raise AssertionError("canonical source missing")


def test_rule_hash_authority_and_all_canonical_pairs():
    source = _canonical_source()
    digest = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
    assert GEN.RULE_HASH == digest == "0ef10b0042c4"
    base = json.loads((ROOT / "shared/data/base/solutions/training/ea32f347__fe947dc3e12c.json").read_text())
    assert base["racket_target"]["target_code"] == source
    assert "raw_code" in base["racket_target"]
    for pair in PAIRS:
        original = deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == oracle(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_axis_contract_is_small_exact_and_has_no_negative_fixtures():
    assert set(GEN.AXES) == {"grid_h", "grid_w", "palette_mode", "texture"}
    assert tuple(GEN.AXES["palette_mode"]["valid"].split("|")) == GEN.PALETTE_MODES
    assert tuple(GEN.AXES["texture"]["valid"].split("|")) == GEN.TEXTURES
    assert GEN.DEGENERATE_TEXTURES == ()
    assert GEN.LAWFUL_DEGENERATE_TEXTURES == ()
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("texture", ("bars", "bbox_witness"))
@pytest.mark.parametrize("palette_mode", ("canonical", "varied"))
@pytest.mark.parametrize("dims", ((9, 9), (10, 10), (14, 16)))
def test_every_joint_override_is_exact_observable_and_lawful(band, texture, palette_mode, dims):
    expected = {"grid_h": dims[0], "grid_w": dims[1],
                "texture": texture, "palette_mode": palette_mode}
    for seed in (0, 17):
        grid = GEN.generate(seed, 23, difficulty=band, **expected)
        assert GEN.self_check(grid) == []
        assert GEN.observe_overrides(grid) == expected
        assert GEN.rule_mirror(grid) == oracle(grid)
        assert grid == GEN.generate(seed, 23, difficulty=band, **expected)


@pytest.mark.parametrize(
    "args,kwargs",
    [
        ((True, 0), {}), ((1.0, 0), {}), (("1", 0), {}),
        ((0, True), {}), ((0, -1), {}), ((0, 1.0), {}),
        ((0, 0), {"difficulty": True}), ((0, 0), {"difficulty": "expert"}),
        ((0, 0), {"grid_h": True}), ((0, 0), {"grid_h": 10.0}),
        ((0, 0), {"grid_w": "10"}), ((0, 0), {"texture": "single_blob"}),
        ((0, 0), {"palette_mode": "rainbow"}), ((0, 0), {"bogus": 123}),
        ((0, 0), {"size_1": 9}),
    ],
)
def test_invalid_requests_fail_closed(args, kwargs):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(*args, **kwargs)


@pytest.mark.parametrize(
    "grid",
    [
        None, [], [[]], [[0] * 10 for _ in range(10)],
        [[5] * 10 for _ in range(10)],
        [[False] * 10 for _ in range(10)],
        [[10] * 10 for _ in range(10)],
        [[0] * 9 for _ in range(8)],
        [[0] * 10 for _ in range(9)] + [[0] * 9],
    ],
)
def test_malformed_and_degenerate_grids_fail_closed(grid):
    assert GEN.self_check(grid)


def test_tied_sizes_and_wrong_component_counts_are_rejected():
    tied = [[0] * 10 for _ in range(10)]
    for r, c in ((1, 1), (1, 2), (4, 1), (4, 2), (7, 1), (7, 2)):
        tied[r][c] = 5
    assert GEN.self_check(tied)
    one = [[0] * 10 for _ in range(10)]
    for c in range(6):
        one[4][c + 2] = 5
    assert GEN.self_check(one)


def test_bbox_area_is_a_real_canonical_shortcut_and_generated_counterexample():
    rival = GEN.CANONICAL_SHORTCUTS["bbox_area_rank"]
    assert all(rival(pair["input"]) == pair["output"] for pair in PAIRS)
    witness = GEN.generate(712, 0, texture="bbox_witness")
    assert GEN.SEMANTIC_WITNESSES["cell_count_not_bbox_area"](witness)
    assert rival(witness) == bbox_area_rival(witness)
    assert rival(witness) != oracle(witness)


@pytest.mark.parametrize("band", BANDS)
def test_every_four_pair_schedule_and_every_query_rotation_refute_bbox_rival(band):
    assert GEN.EXAMPLES_NEEDED == 3
    assert GEN.LESSON_SCHEDULE_PERIOD == 2
    for start in range(6):
        lesson = []
        for offset in range(4):
            sample_index = start + offset
            grid = GEN.generate(31_000 + start, sample_index, difficulty=band)
            lesson.append({"input": grid, "output": oracle(grid)})
        assert {GEN.observe_overrides(pair["input"])["texture"] for pair in lesson} == {
            "bars", "bbox_witness"
        }
        for query_index, query in enumerate(lesson):
            demos = lesson[:query_index] + lesson[query_index + 1:]
            assert GEN.lesson_identifiable(demos, query) == []


@pytest.mark.parametrize("band", BANDS)
def test_default_distribution_has_regular_strict_support_and_is_diverse(band):
    grids = [GEN.generate(9000 + seed, seed, difficulty=band) for seed in range(120)]
    assert all(GEN.self_check(grid) == [] for grid in grids)
    strict = [grid for grid in grids if GEN.strict_canonical_like(grid) == []]
    assert len(strict) >= 24
    assert all(9 <= len(grid) <= 14 and 9 <= len(grid[0]) <= 16 for grid in grids)
    assert len({json.dumps(grid, separators=(",", ":")) for grid in grids}) >= 110
    assert {GEN.observe_overrides(grid)["texture"] for grid in grids} == {
        "bars", "bbox_witness"
    }


def test_default_dimension_schedule_uses_declared_span_and_difficulty():
    observed = {}
    for band in ("easy", "medium", "hard"):
        observed[band] = [
            (len(GEN.generate(12000 + index, index, difficulty=band)),
             len(GEN.generate(12000 + index, index, difficulty=band)[0]))
            for index in range(1, 241)
            if index % 4 != 0
        ]
    assert observed["easy"] != observed["medium"] != observed["hard"]
    all_dims = [dims for values in observed.values() for dims in values]
    assert min(height for height, _ in all_dims) == 9
    assert max(height for height, _ in all_dims) == 14
    assert min(width for _, width in all_dims) == 9
    assert max(width for _, width in all_dims) == 16


def test_global_random_isolation_and_fresh_returns():
    random.seed(947)
    state = random.getstate()
    first = GEN.generate(91, 13, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(91, 13, difficulty="hard")
    assert first == second and first is not second and first[0] is not second[0]
    first[0][0] = 9
    assert GEN.generate(91, 13, difficulty="hard") == second
