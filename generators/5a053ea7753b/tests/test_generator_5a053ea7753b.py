from __future__ import annotations

import copy
import random
from pathlib import Path

import pytest

from scripts.canonical_profile_gate import canonical_pairs
from scripts.generator_module_loader import load_module_from_path

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "5a053ea7753b"
GEN = load_module_from_path(
    f"test_generator_{TASK_ID}",
    ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py",
)


def _canonical_pairs():
    return list(canonical_pairs(TASK_ID))


def test_canonical_inputs_and_python_mirror():
    pairs = _canonical_pairs()
    assert len(pairs) == 4
    for pair in pairs:
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.self_check(pair["input"]) == []
        if "output" in pair:
            assert GEN._official_output(pair["input"]) == pair["output"]


def test_determinism_freshness_and_global_rng_purity():
    random.seed(912345)
    before = random.getstate()
    first = GEN.generate(123, 7, difficulty="hard")
    middle = random.getstate()
    second = GEN.generate(123, 7, difficulty="hard")
    after = random.getstate()
    assert first == second
    assert first is not second
    assert first[0] is not second[0]
    assert before == middle == after


@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": 19, "grid_w": 18},
        {"grid_h": 23, "grid_w": 23},
        {"source_h": 4, "source_w": 4},
        {"source_h": 7, "source_w": 7},
        {"target_h": 5, "target_w": 5},
        {"target_h": 9, "target_w": 9},
        {"shape_size": 7, "dot_color": 1},
        {"shape_size": 12, "dot_color": 9},
        {"panel_layout": "source_above"},
        {"panel_layout": "source_below"},
        {"panel_layout": "source_left"},
        {"panel_layout": "source_right"},
    ],
)
def test_exact_overrides_are_observable(overrides):
    grid = GEN.generate(55, 3, difficulty="medium", **overrides)
    observed = GEN.observe_overrides(grid)
    for name, value in overrides.items():
        assert observed[name] == value


def test_every_canonical_axis_profile_is_generatable_exactly():
    for index, pair in enumerate(_canonical_pairs()):
        info = GEN._analyze(pair["input"])
        overrides = {
            "grid_h": info["h"],
            "grid_w": info["w"],
            "source_h": info["source"]["h"],
            "source_w": info["source"]["w"],
            "target_h": info["target"]["h"],
            "target_w": info["target"]["w"],
            "shape_size": len(info["offsets"]),
            "dot_color": info["dot_color"],
            "panel_layout": info["panel_layout"],
        }
        grid = GEN.generate(700000 + index, index, difficulty="medium", **overrides)
        observed = GEN.observe_overrides(grid)
        assert observed == overrides
        assert GEN.self_check(grid) == []


def test_unknown_override_rejected():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, not_an_axis=True)


def _disconnected_shape_impostor(grid):
    info = GEN._analyze(grid)
    sr, sc, _ = info["source_dot"]
    occupied = set(info["offsets"])
    target_rel = info["target_rel"]
    allowed = GEN._allowed_offsets(
        info["source"]["h"],
        info["source"]["w"],
        (sr - info["source"]["r0"], sc - info["source"]["c0"]),
    )
    for removed in sorted(occupied):
        for replacement in sorted(allowed - occupied):
            candidate = (occupied - {removed}) | {replacement}
            if GEN._shape_connected(candidate):
                continue
            if max(max(abs(dr), abs(dc)) for dr, dc in candidate) != 2:
                continue
            if not any(max(abs(dr), abs(dc)) <= 1 for dr, dc in candidate):
                continue
            if not all(
                0 <= target_rel[0] + dr < info["target"]["h"]
                and 0 <= target_rel[1] + dc < info["target"]["w"]
                for dr, dc in candidate
            ):
                continue
            mutant = copy.deepcopy(grid)
            mutant[sr + removed[0]][sc + removed[1]] = 0
            mutant[sr + replacement[0]][sc + replacement[1]] = 4
            return mutant
    raise AssertionError("could not construct a disconnected in-panel mutation")


def test_self_check_rejects_targeted_impostors():
    grid = GEN.generate(
        923,
        0,
        difficulty="medium",
        source_h=7,
        source_w=7,
        target_h=9,
        target_w=9,
        shape_size=7,
    )
    info = GEN._analyze(grid)
    impostors = []

    missing_dot = copy.deepcopy(grid)
    tr, tc, _ = info["target_dot"]
    missing_dot[tr][tc] = 0
    impostors.append(missing_dot)

    third_dot = copy.deepcopy(grid)
    third_dot[0][0] = info["dot_color"]
    impostors.append(third_dot)

    mismatched = copy.deepcopy(grid)
    mismatched[tr][tc] = 9 if info["dot_color"] != 9 else 7
    impostors.append(mismatched)

    panel_hole = copy.deepcopy(grid)
    panel_hole[info["target"]["r0"]][info["target"]["c0"]] = 8
    impostors.append(panel_hole)

    detached_yellow = copy.deepcopy(grid)
    yr, yc = info["source"]["yellows"][0]
    detached_yellow[yr][yc] = 0
    detached_yellow[0][0] = 4
    impostors.append(detached_yellow)

    impostors.append(_disconnected_shape_impostor(grid))
    assert all(GEN.self_check(candidate) for candidate in impostors)
    assert any(
        "4-connected" in reason
        for reason in GEN.self_check(impostors[-1])
    )


def test_every_three_demo_schedule_window_is_identifiable():
    for start in range(8):
        demos = []
        for sample_index in range(start, start + GEN.EXAMPLES_NEEDED):
            grid = GEN.generate(8001, sample_index, difficulty="medium")
            demos.append({"input": grid, "output": GEN._official_output(grid)})
        query_grid = GEN.generate(
            8001, start + GEN.EXAMPLES_NEEDED, difficulty="medium"
        )
        query = {"input": query_grid, "output": GEN._official_output(query_grid)}
        assert GEN.lesson_identifiable(demos, query) == []

        orientations = {
            "vertical" if GEN._vertical_layout(pair["input"]) else "horizontal"
            for pair in demos
        }
        assert orientations == {"vertical", "horizontal"}
        assert {GEN._source_first(pair["input"]) for pair in demos} == {False, True}
        assert {
            GEN._source_area_relation(pair["input"]) for pair in demos
        } == {"source_smaller", "source_larger"}


def test_every_named_witness_refutes_its_named_rival():
    seen = set()
    for sample_index in range(20):
        grid = GEN.generate(404, sample_index, difficulty="hard")
        official = GEN._official_output(grid)
        for witness_name, witness in GEN.SEMANTIC_WITNESSES.items():
            if not witness(grid):
                continue
            seen.add(witness_name)
            assert any(
                GEN.SEMANTIC_RIVALS[rival_name](grid) != official
                for rival_name in GEN.WITNESS_RIVALS[witness_name]
            )
    assert seen == set(GEN.SEMANTIC_WITNESSES)


def test_generated_shapes_are_connected_and_off_center():
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(40):
            grid = GEN.generate(91000 + sample_index, sample_index, difficulty=difficulty)
            info = GEN._analyze(grid)
            assert GEN._shape_connected(info["offsets"])
            assert info["target_rel"] != (
                info["target"]["h"] // 2,
                info["target"]["w"] // 2,
            )
