"""Source-bound regressions for df74e338b4f5 nesting-depth recoloring."""
from __future__ import annotations

from copy import deepcopy
import random

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "df74e338b4f5"
ROOT = find_root(__file__)
GEN, _, _ = load_selected_generator(TASK_ID, root=ROOT)
PAIRS = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)


def _pair(seed: int, sample_index: int, difficulty: str | None = None) -> dict:
    grid = GEN.generate(seed, sample_index, difficulty=difficulty)
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def test_rule_pin_and_canonical_authority() -> None:
    assert GEN.RULE_HASH == "3ba84d8589ae"
    assert len(PAIRS) == 5
    for pair in PAIRS:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]

    ambiguous = {
        name
        for name, rival in GEN.SEMANTIC_RIVALS.items()
        if all(rival(pair["input"]) == pair["output"] for pair in PAIRS)
    }
    assert set(GEN.CANONICAL_SHORTCUTS) == ambiguous == set()


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        {"grid_h": 11, "grid_w": 11, "n_frames": 2},
        {"grid_h": 18, "grid_w": 18, "n_frames": 3},
        {"grid_h": 11, "grid_w": 18, "n_frames": 3},
        {"grid_h": 18, "grid_w": 11, "n_frames": 2},
    ],
)
def test_every_exact_axis_round_trips_in_every_band(difficulty, options) -> None:
    grid = GEN.generate(913, 27, difficulty=difficulty, **options)
    assert GEN.self_check(grid, meta={"overrides": options}) == []
    assert GEN.observe_overrides(grid) == options


@pytest.mark.parametrize(
    "kwargs",
    [
        {"typo_axis": 12},
        {"grid_h": 10},
        {"grid_h": 19},
        {"grid_w": 10},
        {"grid_w": 19},
        {"n_frames": 1},
        {"n_frames": 4},
        {"grid_h": True},
        {"grid_w": 12.0},
        {"n_frames": "2"},
    ],
)
def test_unknown_invalid_and_coercible_overrides_fail_closed(kwargs) -> None:
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 0, **kwargs)


@pytest.mark.parametrize("bad_sample_index", [True, 1.0, "1", -1])
def test_sample_index_requires_a_nonnegative_genuine_integer(bad_sample_index) -> None:
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, bad_sample_index)


def test_unknown_difficulty_fails_closed() -> None:
    with pytest.raises(ValueError):
        GEN.generate(1, 0, difficulty="expert")


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_defaults_are_deterministic_lawful_and_teach_containment(difficulty) -> None:
    shapes = set()
    frame_counts = set()
    marker_colors = set()
    for index in range(36):
        seed = 7000 + index
        sample_index = index * 7 + 2
        before = random.getstate()
        grid = GEN.generate(seed, sample_index, difficulty=difficulty)
        assert before == random.getstate()
        assert grid == GEN.generate(seed, sample_index, difficulty=difficulty)
        assert GEN.self_check(grid) == []
        assert GEN.strict_canonical_like(grid) == []

        analysis = GEN._analyze(grid)
        assert analysis["errors"] == []
        depth_values = {marker["depth"] for marker in analysis["markers"]}
        assert depth_values == set(range(analysis["frame_count"] + 1))
        assert GEN.rule_mirror(grid) != GEN.SEMANTIC_RIVALS[
            "canvas_edge_distance_depth"
        ](grid)
        assert GEN.SEMANTIC_WITNESSES["canvas_distance_killer"](grid)

        shapes.add((len(grid), len(grid[0])))
        frame_counts.add(analysis["frame_count"])
        marker_colors.add(analysis["marker_color"])

    assert len(shapes) >= 5
    assert len(marker_colors) >= 5
    if difficulty is None:
        assert frame_counts == {2, 3}
    elif difficulty == "easy":
        assert frame_counts == {2}
    elif difficulty == "hard":
        assert frame_counts == {3}


def test_difficulty_is_live_for_the_same_seed_and_sample() -> None:
    grids = {
        band: GEN.generate(7331, 8, difficulty=band)
        for band in ("easy", "medium", "hard")
    }
    assert len({repr(grid) for grid in grids.values()}) == 3


def test_named_competitors_are_refuted_by_every_lesson_window() -> None:
    for start in range(12):
        lesson = [
            _pair(42000 + start, start + offset, ("easy", "medium", "hard")[start % 3])
            for offset in range(5)
        ]
        for query_index, query in enumerate(lesson):
            demos = [pair for index, pair in enumerate(lesson) if index != query_index]
            assert GEN.lesson_identifiable(demos, query) == []
            for name, rival in GEN.LESSON_COMPETITORS.items():
                assert not all(
                    rival(pair["input"]) == pair["output"] for pair in demos
                ), (start, query_index, name)


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True] * 11 for _ in range(11)],
        [[10] * 11 for _ in range(11)],
    ],
)
def test_self_check_reports_malformed_grids_without_raising(grid) -> None:
    errors = GEN.self_check(grid)
    assert isinstance(errors, list) and errors


def test_rule_mirror_observer_and_self_check_do_not_mutate_input() -> None:
    grid = GEN.generate(42, 99, difficulty="hard")
    original = deepcopy(grid)
    GEN.rule_mirror(grid)
    GEN.observe_overrides(grid)
    GEN.self_check(grid)
    assert grid == original


def test_retained_canvas_distance_counterexample_stays_lawful_and_decisive() -> None:
    import json
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / "counterexamples" / "canvas_edge_distance_depth.json"
    payload = json.loads(path.read_text())
    grid = payload["input"]
    assert GEN.self_check(grid) == []
    assert GEN.rule_mirror(grid) == payload["intended_output"]
    rival = GEN.SEMANTIC_RIVALS["canvas_edge_distance_depth"]
    assert rival(grid) == payload["rival_output"]
    assert payload["intended_output"] != payload["rival_output"]


def test_task_local_semantic_probe_replays_declared_contract() -> None:
    import importlib.util
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / "workspace" / "probe_semantics.py"
    spec = importlib.util.spec_from_file_location("df74e338_probe_semantics", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    report = module.run_probe(per_band=4, seed_base=88000)
    assert report["status"] == "pass", report
    assert report["canonical_shortcuts"]["all_fit"] is True
    assert report["generated"]["lawful"] == 12
    assert report["generated"]["rival_survivals"] == []
