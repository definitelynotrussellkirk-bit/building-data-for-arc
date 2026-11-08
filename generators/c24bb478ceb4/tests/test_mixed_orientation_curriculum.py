"""Regression tests for mixed-orientation teaching support in c24bb478ceb4."""
from __future__ import annotations

from puzzle_generators.per_puzzle.c24bb478ceb4 import generator as gen


def _first_orientation_for_all(grid):
    """Plausible shortcut: use the lowest color's missing corner for all colors."""
    facts = gen.semantic_observables(grid)
    assert facts["errors"] == []
    rectangles = sorted(facts["rectangles"], key=lambda rect: rect["color"])
    orientation = rectangles[0]["missing_name"]
    out = [list(row) for row in grid]
    for rect in rectangles:
        r0, r1 = rect["rows"]
        c0, c1 = rect["cols"]
        corners = {
            "top_left": (r0, c0),
            "top_right": (r0, c1),
            "bottom_left": (r1, c0),
            "bottom_right": (r1, c1),
        }
        r, c = corners[orientation]
        out[r][c] = rect["color"]
    return out


def _pair(seed: int, sample_index: int, *, pattern: str | None = None):
    kwargs = {}
    if pattern is not None:
        kwargs = {
            "grid_h": 9,
            "grid_w": 9,
            "n_rects": 3,
            "palette_kind": "low",
            "missing_pattern": pattern,
        }
    inp = gen.generate(seed, sample_index, difficulty="medium", **kwargs)
    return {"input": inp, "output": gen.rule_mirror(inp)}


def test_each_default_three_demo_window_refutes_global_first_orientation() -> None:
    """No production lesson may contain only homogeneous-orientation demos."""
    for band in ("easy", "medium", "hard"):
        for start in range(24):
            demos = []
            for sample_index in range(start, start + gen.EXAMPLES_NEEDED):
                inp = gen.generate(3400 + start, sample_index, difficulty=band)
                demos.append({"input": inp, "output": gen.rule_mirror(inp)})
            assert not all(
                _first_orientation_for_all(pair["input"]) == pair["output"]
                for pair in demos
            ), (band, start, [gen.semantic_observables(p["input"])["missing_pattern"] for p in demos])


def test_lesson_hook_declares_global_first_orientation_competitor() -> None:
    demos = [
        _pair(7101, 0, pattern="top_left"),
        _pair(7102, 1, pattern="bottom_right"),
        _pair(7103, 2, pattern="top_right"),
    ]
    query = _pair(7104, 3, pattern="mixed")

    assert all(_first_orientation_for_all(p["input"]) == p["output"] for p in demos)
    assert _first_orientation_for_all(query["input"]) != query["output"]
    reasons = gen.lesson_identifiable(demos, query)
    assert any("first_orientation_for_all" in reason for reason in reasons), reasons


def test_each_four_pair_window_refutes_rival_under_any_query_rotation() -> None:
    """Holding out any one of four consecutive pairs must leave a mixed demo."""
    for band in ("easy", "medium", "hard"):
        for start in range(24):
            pairs = []
            for sample_index in range(start, start + gen.EXAMPLES_NEEDED + 1):
                inp = gen.generate(9100 + start, sample_index, difficulty=band)
                pairs.append({"input": inp, "output": gen.rule_mirror(inp)})
            for query_offset in range(len(pairs)):
                demos = [pair for i, pair in enumerate(pairs) if i != query_offset]
                assert not all(
                    _first_orientation_for_all(pair["input"]) == pair["output"]
                    for pair in demos
                ), (
                    band,
                    start,
                    query_offset,
                    [gen.semantic_observables(p["input"])["missing_pattern"] for p in pairs],
                )
