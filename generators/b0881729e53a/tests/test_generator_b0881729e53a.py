"""Focused semantic and contract regressions for generator b0881729e53a."""
from __future__ import annotations

import copy
import hashlib
import json
import random
from pathlib import Path

import pytest

from puzzle_generators.base import set_ctx_observer
from puzzle_generators.per_puzzle.b0881729e53a import generator as gen
from reviewer_support import canonical_pairs, find_root


ROOT = find_root(__file__)


def _canonical_pairs():
    return canonical_pairs(gen.TASK_ID, root=ROOT)


def _pair(grid):
    return {"input": copy.deepcopy(grid), "output": gen.rule_mirror(grid)}


def _zero_cells(grid, cells):
    mutated = copy.deepcopy(grid)
    for r, c in cells:
        mutated[r][c] = 0
    return mutated


def _five_pair_cycle(seed, start, difficulty):
    return [
        _pair(gen.generate(seed, start + offset, difficulty=difficulty))
        for offset in range(gen.LESSON_SCHEDULE_PERIOD)
    ]


def test_rule_pin_and_all_canonical_pairs_are_exact():
    assert gen.RULE_HASH == "b7117efbdd28"
    pairs = _canonical_pairs()
    assert len(pairs) == 4
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_declared_canonical_shortcuts_really_fit_all_canonical_pairs():
    pairs = _canonical_pairs()
    assert set(gen.CANONICAL_SHORTCUTS) == {
        "smallest_external_object",
        "rightmost_external_object",
        "farthest_from_frame",
    }
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs), name


def test_canonical_scan_order_counterexample_selects_later_singleton():
    pair = _canonical_pairs()[2]
    frame, nonframes, selected = gen._scene(pair["input"])
    assert frame.color == 4
    assert [obj.size for obj in nonframes] == [4, 1]
    assert selected is nonframes[-1]
    assert selected.size == 1
    assert gen.rule_mirror(pair["input"]) == pair["output"]
    assert gen._rival_largest_external(pair["input"]) != pair["output"]


def test_five_slot_schedule_names_each_profile_once():
    names = [gen.schedule_profile(0, index, "medium") for index in range(5)]
    assert len(set(names)) == 5
    assert names[-1] == "single_object"
    assert all(name.startswith("scan_order_") for name in names[:4])
    assert [gen.schedule_profile(999, index + 5, "hard") for index in range(5)] == names


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_every_schedule_start_and_query_holdout_refutes_all_declared_rivals(difficulty):
    for start in range(gen.LESSON_SCHEDULE_PERIOD):
        pairs = _five_pair_cycle(77123 + start, start, difficulty)
        disagreements = {
            name: sum(rival(pair["input"]) != pair["output"] for pair in pairs)
            for name, rival in gen.LESSON_COMPETITORS.items()
        }
        # At least two counterexamples are required so holding out any one pair
        # still leaves a demonstration that defeats the rival.
        assert all(count >= 2 for count in disagreements.values()), disagreements
        for query_index, query in enumerate(pairs):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert gen.lesson_identifiable(demos, query) == []


def test_scan_order_profiles_reverse_side_shape_and_row_heuristics():
    grids = [gen.generate(918273, index, difficulty="medium") for index in range(4)]
    parts = [gen._two_object_parts(grid) for grid in grids]
    assert all(item is not None for item in parts)

    # First two: later component is on the left and starts on a lower row.
    for frame, earlier, selected in parts[:2]:
        assert selected.bbox[0] > earlier.bbox[0]
        assert selected.bbox[1] < earlier.bbox[1]
        assert selected.size == earlier.size
        assert selected.color == earlier.color

    # Last two: both components begin/end on the same rows and have equal
    # frame distance/bounding-box size; the right-hand start column breaks tie.
    for frame, earlier, selected in parts[2:]:
        assert selected.bbox[0] == earlier.bbox[0]
        assert selected.bbox[2] == earlier.bbox[2]
        assert selected.bbox[1] > earlier.bbox[1]
        assert gen._bbox_gap(frame, selected) == gen._bbox_gap(frame, earlier)
        assert gen._bbox_height(selected) == gen._bbox_height(earlier) == 2
        assert gen._bbox_width(selected) == gen._bbox_width(earlier) == 2

    assert gen._is_bent(parts[0][2]) and not gen._is_bent(parts[0][1])
    assert not gen._is_bent(parts[1][2]) and gen._is_bent(parts[1][1])
    assert gen._witness_same_bottom_edge_decoy(grids[0])
    assert gen._witness_same_top_edge_decoy(grids[2])
    assert gen._witness_equal_frame_distance_decoy(grids[3])


@pytest.mark.parametrize("sample_index", range(5))
@pytest.mark.parametrize("placement", ["touching", "separated"])
@pytest.mark.parametrize("grid_h,grid_w", [(8, 9), (14, 15)])
def test_exact_override_boundaries_are_observable(sample_index, placement, grid_h, grid_w):
    overrides = {"grid_h": grid_h, "grid_w": grid_w, "placement": placement}
    captured = []
    set_ctx_observer(captured.append)
    try:
        grid = gen.generate(314159, sample_index, difficulty="hard", **overrides)
    finally:
        set_ctx_observer(None)
    assert gen.observe_overrides(grid) == overrides
    assert captured[-1].recorded_draws() == overrides
    assert captured[-1].overrides_used() == overrides
    assert gen.self_check(grid, meta={"overrides": overrides}) == []


def test_invalid_overrides_reject():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, texture="warm")
    with pytest.raises(ValueError, match="outside"):
        gen.generate(1, 0, grid_h=7)
    with pytest.raises(ValueError, match="options"):
        gen.generate(1, 0, placement="diagonal")


def test_self_check_rejects_named_structural_impostors():
    base = gen.generate(8811, 3, difficulty="medium")
    frame, nonframes, selected = gen._scene(base)

    no_frame = _zero_cells(base, frame.cells)
    assert gen.self_check(no_frame)

    broken_frame = copy.deepcopy(base)
    broken_frame[frame.cells[0][0]][frame.cells[0][1]] = 0
    assert gen.self_check(broken_frame)

    no_external_object = _zero_cells(base, [cell for obj in nonframes for cell in obj.cells])
    assert gen.self_check(no_external_object)

    inside_frame = _zero_cells(base, [cell for obj in nonframes for cell in obj.cells])
    fr0, fc0, fr1, fc1 = frame.bbox
    inside_frame[(fr0 + fr1) // 2][(fc0 + fc1) // 2] = selected.color
    assert any("outside the frame bbox" in error for error in gen.self_check(inside_frame))

    third_object = copy.deepcopy(base)
    occupied = {cell for obj in gen._components(third_object) for cell in obj.cells}
    injected = False
    for r in range(len(third_object)):
        for c in range(len(third_object[0])):
            if (r, c) in occupied:
                continue
            if all(
                not (0 <= r + dr < len(third_object) and 0 <= c + dc < len(third_object[0]))
                or third_object[r + dr][c + dc] == 0
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
            ):
                third_object[r][c] = 9 if frame.color != 9 else 1
                injected = True
                break
        if injected:
            break
    assert injected
    assert any("one or two non-frame" in error for error in gen.self_check(third_object))


def test_python_generation_is_deterministic_fresh_and_rng_neutral():
    state = random.getstate()
    first = gen.generate(20260725, 17, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(20260725, 17, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 1
    third = gen.generate(20260725, 17, difficulty="hard")
    assert third == second


def test_source_erasure_centering_and_noncyan_are_observable():
    grids = [gen.generate(44, index, difficulty="easy") for index in range(20)]
    assert any(gen._witness_non_cyan_frame(grid) for grid in grids)
    assert any(gen._witness_center_not_corner(grid) for grid in grids)
    for grid in grids:
        output = gen.rule_mirror(grid)
        frame, nonframes, selected = gen._scene(grid)
        for obj in nonframes:
            for r, c in obj.cells:
                assert output[r][c] == 0
        top, left = gen._center_top_left(frame, gen._normalized_shape(selected))
        assert all(
            output[top + dr][left + dc] == selected.color
            for dr, dc in gen._normalized_shape(selected)
        )


def test_retained_racket_counterexample_refutes_canonical_shortcuts():
    task_root = Path(__file__).resolve().parents[1]
    path = task_root / "counterexamples/scan_order_shortcuts.json"
    record = json.loads(path.read_text())
    source_hash = hashlib.sha256((task_root / "generator.py").read_bytes()).hexdigest()
    assert record["generator_sha256"] == source_hash
    assert record["rule_hash"] == gen.RULE_HASH
    grid = record["input"]
    official = record["racket_output"]
    assert gen.self_check(grid) == []
    assert gen.rule_mirror(grid) == official
    assert set(record["canonical_shortcuts_refuted"]) == set(gen.CANONICAL_SHORTCUTS)
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        output = rival(grid)
        assert output == record["canonical_shortcut_outputs"][name]
        assert output != official
