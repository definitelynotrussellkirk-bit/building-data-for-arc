from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id

TASK = "204213f10aff"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK
PARAM = HOME / "workspace" / "parametric"


def _load(name: str, path: Path):
    assert path.is_file(), f"missing source: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def generator():
    return _load("_gen_204213f10aff_test", HOME / "generator.py")


@pytest.fixture(scope="module")
def prototype():
    return _load("_param_204213f10aff_test", PARAM / "prototype.py")


def _canonical_program() -> str:
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            return row["program_solution"]
    raise AssertionError("canonical program missing")


def _all_inputs(episode):
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def test_production_generator_repairs_sparse_legend_and_unlisted_distractors(generator):
    for seed in range(12):
        grid = generator.generate(seed, seed * 7 + 1, difficulty="medium")
        assert generator.self_check(grid) == []
        legend_positions = [c for c, value in enumerate(grid[0]) if value]
        legend = [grid[0][c] for c in legend_positions]
        assert legend_positions != list(range(len(legend_positions)))
        body_colors = {value for row in grid[1:] for value in row if value}
        assert body_colors - set(legend), "ordinary lessons must include unlisted body colors"
        analysis = generator.analyze(grid)
        assert analysis["piece_count"] == len(legend)
        assert analysis["distractor_count"] == len(body_colors - set(legend))
        assert all(len(analysis["components_by_color"][color]) == 1 for color in body_colors)


def test_production_controls_are_strict_observable_and_cover_30x30(generator):
    grid = generator.generate(
        37,
        5,
        difficulty="hard",
        grid_h=30,
        grid_w=30,
        piece_count=4,
        distractor_count=3,
    )
    assert (len(grid), len(grid[0])) == (30, 30)
    assert generator.observe_overrides(grid) == {
        "grid_h": 30,
        "grid_w": 30,
        "piece_count": 4,
        "distractor_count": 3,
    }
    assert generator.self_check(grid) == []

    for bad in (
        {"grid_h": True}, {"grid_w": 20.0}, {"piece_count": "3"},
        {"distractor_count": False}, {"unknown": 1},
    ):
        with pytest.raises((TypeError, ValueError)):
            generator.generate(0, 0, **bad)


def test_self_check_rejects_malformed_or_ambiguous_scenes(generator):
    valid = generator.generate(9, 11)
    assert generator.self_check(valid) == []

    duplicate_legend = copy.deepcopy(valid)
    positions = [c for c, value in enumerate(duplicate_legend[0]) if value]
    duplicate_legend[0][positions[1]] = duplicate_legend[0][positions[0]]
    assert any("legend colors must be unique" in err for err in generator.self_check(duplicate_legend))

    missing = copy.deepcopy(valid)
    missing_color = next(value for value in missing[0] if value)
    for r in range(1, len(missing)):
        for c in range(len(missing[0])):
            if missing[r][c] == missing_color:
                missing[r][c] = 0
    assert any("no body component" in err for err in generator.self_check(missing))

    ragged = copy.deepcopy(valid)
    ragged[-1].pop()
    assert generator.self_check(ragged) == ["ragged grid"]


def test_parametric_default_is_exact_canonical_and_alternate_is_distinct(prototype):
    canonical = prototype.program({"piece_order": "legend"})
    alternate = prototype.program({"piece_order": "area_descending"})
    assert canonical == _canonical_program()
    assert alternate != canonical
    assert canonical == (PARAM / "canonical.rkt").read_text(encoding="utf-8")
    assert alternate == (PARAM / "area_descending.rkt").read_text(encoding="utf-8")


def test_parametric_controls_are_strict(prototype):
    good = {"piece_order": "legend"}
    for settings in ({}, {"piece_order": "area"}, {"piece_order": 1}, {"piece_order": "legend", "x": 1}):
        with pytest.raises((TypeError, ValueError)):
            prototype.program(settings)
    for key, value in (
        ("seed", True), ("seed", -1), ("seed", 1.0),
        ("demos", 1), ("demos", 7), ("demos", True),
        ("queries", 3), ("queries", 5), ("queries", True),
    ):
        kwargs = {"seed": 0, "settings": good, "demos": 3, "queries": 4}
        kwargs[key] = value
        with pytest.raises((TypeError, ValueError)):
            prototype.generate(**kwargs)


def test_inputs_are_setting_neutral_prefix_stable_distinct_and_identifying(prototype):
    legend = prototype.generate(41, {"piece_order": "legend"}, demos=3, queries=4)
    area = prototype.generate(41, {"piece_order": "area_descending"}, demos=3, queries=4)
    assert _all_inputs(legend) == _all_inputs(area)
    assert len({prototype.digest(grid) for grid in _all_inputs(legend)}) == 7
    assert all(a["output"] != b["output"] for a, b in zip(legend["train"], area["train"]))

    two = prototype.generate(41, {"piece_order": "legend"}, demos=2, queries=4)
    six = prototype.generate(41, {"piece_order": "legend"}, demos=6, queries=4)
    assert two["train"] == six["train"][:2]
    assert two["test"] == six["test"]
    assert two["certificate"]["setting_survivors"] == [{"piece_order": "legend"}]
    assert two["certificate"]["rival_survivors"] == []


def test_minimum_lesson_teaches_occupied_area_not_bbox_or_position(prototype):
    episode = prototype.generate(17, {"piece_order": "area_descending"}, demos=2, queries=4)
    assert episode["certificate"]["rival_survivors"] == []
    assert "bbox_area_descending" in episode["certificate"]["rejected_rivals"]
    assert "spatial_left_to_right" in episode["certificate"]["rejected_rivals"]
    assert "all_body_objects" in episode["certificate"]["rejected_rivals"]

    analyses = [prototype.analyze_scene(pair["input"]) for pair in episode["train"]]
    assert any(
        [piece["occupied_area"] for piece in analysis["selected"]]
        != [piece["bbox_area"] for piece in analysis["selected"]]
        for analysis in analyses
    )
    assert any(
        analysis["legend_colors"] != analysis["spatial_colors"]
        for analysis in analyses
    )


def test_queries_cover_boundaries_and_substantive_30x30(prototype):
    episode = prototype.generate(5, {"piece_order": "area_descending"}, demos=3, queries=4)
    dims = {(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]}
    assert (30, 30) in dims and len(dims) == 4
    large = next(pair["input"] for pair in episode["test"] if len(pair["input"]) == 30)
    occupied = {(r, c) for r, row in enumerate(large) for c, value in enumerate(row) if value}
    body = {(r, c) for r, c in occupied if r > 0}
    assert len(body) >= 35
    assert {0, 29} <= {c for _, c in occupied}
    assert 29 in {r for r, _ in body}
    assert len({value for row in large for value in row if value}) >= 6
    for split in ("train", "test"):
        for pair in episode[split]:
            assert pair["output"] == prototype.apply_rule(pair["input"], "area_descending")


def test_certificate_recomputes_and_rejects_forgery_duplicates_and_bad_grids(prototype):
    episode = prototype.generate(23, {"piece_order": "legend"}, demos=2, queries=4)
    assert prototype.certify(episode)["rival_survivors"] == []

    forged = copy.deepcopy(episode)
    forged["certificate"]["rival_survivors"] = ["forged"]
    with pytest.raises(ValueError, match="certificate"):
        prototype.certify(forged)

    duplicate = copy.deepcopy(episode)
    duplicate["test"][0]["input"] = copy.deepcopy(duplicate["train"][0]["input"])
    duplicate["test"][0]["output"] = prototype.apply_rule(duplicate["test"][0]["input"], "legend")
    with pytest.raises(ValueError, match="distinct"):
        prototype.certify(duplicate)

    malformed = copy.deepcopy(episode)
    malformed["train"][0]["input"][2][2] = True
    with pytest.raises(ValueError, match="exact integer"):
        prototype.certify(malformed)


def test_first_turn_projection_hides_settings_program_answers_and_future_queries(prototype):
    episode = prototype.generate(31, {"piece_order": "area_descending"}, demos=3, queries=4)
    visible = prototype.public_turn(episode, 0)
    body = public_challenge_bytes(visible)
    identifier = public_challenge_id(visible)
    assert set(visible) == {"train", "test"}
    assert len(visible["test"]) == 1 and set(visible["test"][0]) == {"input"}
    assert b"area_descending" not in body
    assert b"program_solution" not in body

    changed = copy.deepcopy(episode)
    changed["settings"] = {"piece_order": "legend"}
    changed["program_solution"] = "private"
    changed["test"][0]["output"] = [[9]]
    changed["test"][1]["input"] = [[9]]
    assert public_challenge_bytes(prototype.public_turn(changed, 0)) == body
    assert public_challenge_id(prototype.public_turn(changed, 0)) == identifier


def test_adapter_contract_and_protected_racket_match(prototype):
    adapter = _load("_adapter_204213f10aff_test", PARAM / "adapter.py")
    contract = json.loads((PARAM / "promotion.json").read_text(encoding="utf-8"))
    assert contract["default"] == {"piece_order": "legend"}
    assert contract["limits"] == {"demos": [2, 6], "queries": [4, 4]}
    episode = adapter.generate(7, {"piece_order": "area_descending"}, 2, 4)
    assert episode["program_solution"] == adapter.program({"piece_order": "area_descending"})

    decisive = episode["train"][0]["input"]
    with prototype.RacketRunner() as run:
        for mode in prototype.PIECE_ORDERS:
            assert run(prototype.program({"piece_order": mode}), decisive) == prototype.apply_rule(decisive, mode)


def test_maximum_lesson_certification_handles_wide_all_body_rival(prototype):
    for mode in prototype.PIECE_ORDERS:
        episode = prototype.generate(0, {"piece_order": mode}, demos=6, queries=4)
        assert len(episode["train"]) == 6
        assert episode["certificate"]["rival_survivors"] == []
        assert "all_body_objects" in episode["certificate"]["rejected_rivals"]


def test_every_declared_rival_is_total_on_maximum_lesson(prototype):
    episode = prototype.generate(0, {"piece_order": "legend"}, demos=6, queries=4)
    for pair in episode["train"]:
        for name in prototype.RIVALS:
            output = prototype._rival(name, pair["input"], "legend")
            prototype._grid(output)
