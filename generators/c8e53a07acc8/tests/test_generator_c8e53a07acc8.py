"""Focused regression and semantic tests for c8e53a07acc8."""
from __future__ import annotations

from collections import Counter, deque
from functools import cache
import importlib.util
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "c8e53a07acc8"
ROOT = find_root(__file__)
SOURCE = ROOT / "generators" / TASK_ID / "generator.py"
ADJ8 = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != (0, 0)
)


@cache
def generator():
    spec = importlib.util.spec_from_file_location("_test_c8_generator", SOURCE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def components(grid):
    bg = Counter(value for row in grid for value in row).most_common(1)[0][0]
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or grid[r][c] == bg:
                continue
            seen.add((r, c))
            queue = deque([(r, c)])
            cells = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for dr, dc in ADJ8:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] != bg
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            result.append(cells)
    return result


def template_count(grid):
    return sum(
        len({grid[r][c] for r, c in cells}) > 1
        for cells in components(grid)
    )


@pytest.mark.parametrize("difficulty", [None, "medium", "hard"])
def test_ordinary_draws_require_multi_template_iteration(difficulty):
    gen = generator()
    for index in range(8):
        grid = gen.generate(9100 + index, index, difficulty=difficulty)
        assert gen.self_check(grid, difficulty=difficulty) == []
        assert template_count(grid) >= 2
        assert gen.rule_mirror(grid) != gen.first_template_only_mirror(grid)



@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_each_band_has_an_exact_canonical_profile_anchor(difficulty):
    grid = generator().generate(404, 0, difficulty=difficulty)
    assert (len(grid), len(grid[0]), len({cell for row in grid for cell in row})) == (19, 19, 5)

def test_rule_pin_and_unknown_override_are_strict():
    gen = generator()
    assert gen.RULE_HASH == "559aa4d81a8f"
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, typo_axis=3)


def test_extreme_overrides_are_realized_and_observable():
    gen = generator()
    grid = gen.generate(
        77,
        3,
        difficulty="hard",
        grid_h=30,
        grid_w=30,
        n_templates=3,
        targets_per_template=2,
    )
    assert gen.self_check(grid, difficulty="hard") == []
    assert gen.observe_overrides(grid) == {
        "grid_h": 30,
        "grid_w": 30,
        "n_templates": 3,
        "targets_per_template": 2,
    }
    assert template_count(grid) == 3



def test_self_check_accepts_every_canonical_input():
    gen = generator()
    for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True):
        assert gen.self_check(pair["input"]) == []

def test_python_mirror_matches_protected_racket_on_generated_and_canonical_inputs():
    gen = generator()
    from arc_repl.racket_bridge import RacketBridge
    from arcpuzzles import Catalog
    from puzzle_generators.rule_wrap import wrap_rule

    record = Catalog(ROOT).get(TASK_ID)
    programs = {
        row["program_solution"]
        for row in record["variants"]
        if isinstance(row.get("program_solution"), str)
    }
    assert len(programs) == 1
    program = next(iter(programs))

    def datum(grid):
        return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"

    inputs = [gen.generate(222 + i, i, difficulty=band) for i, band in enumerate((None, "medium", "hard"))]
    inputs.extend(row["input"] for row in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)[:2])
    with RacketBridge(max_calls_before_restart=128) as bridge:
        for grid in inputs:
            expected = bridge.eval_text(f"({wrap_rule(program)} {datum(grid)})")
            assert gen.rule_mirror(grid) == expected
