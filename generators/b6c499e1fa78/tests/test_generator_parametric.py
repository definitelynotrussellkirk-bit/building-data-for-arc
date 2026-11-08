from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id

TASK = "b6c499e1fa78"
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
    return _load("_gen_b6c499e1fa78_test", HOME / "generator.py")


@pytest.fixture(scope="module")
def prototype():
    return _load("_param_b6c499e1fa78_test", PARAM / "prototype.py")


@pytest.fixture(scope="module")
def adapter():
    return _load("_adapter_b6c499e1fa78_test", PARAM / "adapter.py")


def _canonical_program() -> str:
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            return row["program_solution"]
    raise AssertionError("canonical program missing")


def _all_inputs(episode):
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def test_production_generator_supports_strict_30x30_and_exact_roles(generator):
    grid = generator.generate(
        37,
        5,
        difficulty="hard",
        grid_size=30,
        wall_top=10,
        n_openings=3,
        n_match=2,
        n_negative=3,
    )
    assert (len(grid), len(grid[0])) == (30, 30)
    assert generator.observe_overrides(grid) == {
        "grid_size": 30,
        "wall_top": 10,
        "n_openings": 3,
        "n_match": 2,
        "n_negative": 3,
    }
    assert generator.self_check(grid) == []
    analysis = generator.analyze(grid)
    assert analysis["n_match"] == 2
    assert analysis["n_negative"] == 3
    assert analysis["n_branch_only"] == 1
    assert analysis["n_match_and_branch"] == 0


@pytest.mark.parametrize(
    "bad",
    [
        {"grid_size": True},
        {"wall_top": 4.0},
        {"n_openings": "2"},
        {"n_match": False},
        {"n_negative": 2.0},
        {"texture": 1},
        {"match_style": "direct"},
        {"unknown": 1},
    ],
)
def test_production_generator_rejects_coercive_or_unknown_controls(generator, bad):
    with pytest.raises((TypeError, ValueError)):
        generator.generate(0, 0, **bad)


def test_production_ordinary_draws_remain_semantically_nontrivial(generator):
    for seed in range(18):
        grid = generator.generate(seed, seed * 11 + 3, difficulty=("easy", "medium", "hard")[seed % 3])
        assert generator.self_check(grid) == []
        analysis = generator.analyze(grid)
        assert analysis["openings"]
        assert analysis["n_match"] >= 1
        assert analysis["n_branch_only"] == 1
        assert analysis["n_negative"] >= 1
        assert analysis["selected_cells"]
        assert analysis["surviving_gray_cells"]


def test_parametric_default_is_byte_exact_canonical_and_alternate_is_distinct(prototype):
    canonical = prototype.program({"branch_policy": "unconditional"})
    alternate = prototype.program({"branch_policy": "matched_area"})
    assert canonical == _canonical_program()
    assert canonical == (PARAM / "canonical.rkt").read_text(encoding="utf-8")
    assert alternate == (PARAM / "matched_area.rkt").read_text(encoding="utf-8")
    assert alternate != canonical


def test_parametric_controls_are_strict(prototype):
    good = {"branch_policy": "unconditional"}
    for settings in (
        {},
        {"branch_policy": "area"},
        {"branch_policy": 1},
        {"branch_policy": "unconditional", "x": 1},
    ):
        with pytest.raises((TypeError, ValueError)):
            prototype.program(settings)
    for key, value in (
        ("seed", True),
        ("seed", -1),
        ("seed", 1.0),
        ("demos", 1),
        ("demos", 7),
        ("demos", True),
        ("queries", 3),
        ("queries", 5),
        ("queries", True),
    ):
        kwargs = {"seed": 0, "settings": good, "demos": 3, "queries": 4}
        kwargs[key] = value
        with pytest.raises((TypeError, ValueError)):
            prototype.generate(**kwargs)


def test_inputs_are_setting_neutral_prefix_stable_distinct_and_identifying(prototype):
    canonical = prototype.generate(41, {"branch_policy": "unconditional"}, demos=2, queries=4)
    gated = prototype.generate(41, {"branch_policy": "matched_area"}, demos=2, queries=4)
    assert _all_inputs(canonical) == _all_inputs(gated)
    assert len({prototype.digest(grid) for grid in _all_inputs(canonical)}) == 6
    assert all(a["output"] != b["output"] for a, b in zip(canonical["train"], gated["train"]))

    two = prototype.generate(41, {"branch_policy": "matched_area"}, demos=2, queries=4)
    six = prototype.generate(41, {"branch_policy": "matched_area"}, demos=6, queries=4)
    assert two["train"] == six["train"][:2]
    assert two["test"] == six["test"]
    assert two["certificate"]["setting_survivors"] == [{"branch_policy": "matched_area"}]
    assert two["certificate"]["rival_survivors"] == []


def test_minimum_lesson_rejects_partial_intermediate_and_area_shortcuts(prototype):
    episode = prototype.generate(17, {"branch_policy": "matched_area"}, demos=2, queries=4)
    cert = episode["certificate"]
    assert cert["rival_survivors"] == []
    for rival in (
        "match_only",
        "unconditional_branch",
        "opening_area_gate",
        "matched_bbox_area_gate",
        "first_matched_area_gate",
        "area_parity_gate",
        "area_mod3_gate",
        "between_extremes_gate",
        "any_match_unlocks_all_branches",
    ):
        assert rival in cert["rejected_rivals"]

    first, second = [prototype.analyze_scene(pair["input"]) for pair in episode["train"]]
    assert set(first["matched_piece_areas"]) == {4, 6}
    assert {4, 5, 6, 7} <= set(first["branch_areas"])
    assert set(second["matched_piece_areas"]) == {5}
    assert {4, 5, 7, 8} <= set(second["branch_areas"])
    assert first["matched_piece_areas"] != first["opening_areas"]
    assert second["matched_piece_areas"] != second["matched_piece_bbox_areas"]


def test_queries_cover_geometry_boundaries_and_substantive_30x30(prototype):
    episode = prototype.generate(5, {"branch_policy": "matched_area"}, demos=3, queries=4)
    dims = [(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]]
    assert dims == [(17, 17), (21, 21), (25, 25), (30, 30)]
    large = episode["test"][-1]["input"]
    analysis = prototype.analyze_scene(large)
    assert len(analysis["pieces"]) >= 10
    assert len(analysis["openings"]) >= 4
    assert len(analysis["gray_cells"]) >= 45
    assert {0, 29} <= {c for _, c in analysis["gray_cells"]}
    assert 29 in {r for r, _ in analysis["gray_cells"]}
    assert set(analysis["matched_piece_areas"]) >= {4, 5, 6}
    assert 8 in analysis["branch_areas"]
    for split in ("train", "test"):
        for pair in episode[split]:
            assert pair["output"] == prototype.apply_rule(pair["input"], "matched_area")


def test_certificate_recomputes_and_rejects_forgery_duplicates_and_bad_grids(prototype):
    episode = prototype.generate(23, {"branch_policy": "unconditional"}, demos=2, queries=4)
    assert prototype.certify(episode)["rival_survivors"] == []

    forged = copy.deepcopy(episode)
    forged["certificate"]["rival_survivors"] = ["forged"]
    with pytest.raises(ValueError, match="certificate"):
        prototype.certify(forged)

    duplicate = copy.deepcopy(episode)
    duplicate["test"][0]["input"] = copy.deepcopy(duplicate["train"][0]["input"])
    duplicate["test"][0]["output"] = prototype.apply_rule(duplicate["test"][0]["input"], "unconditional")
    with pytest.raises(ValueError, match="distinct"):
        prototype.certify(duplicate)

    malformed = copy.deepcopy(episode)
    malformed["train"][0]["input"][0][0] = True
    with pytest.raises(ValueError, match="exact integer"):
        prototype.certify(malformed)


def test_first_turn_projection_hides_settings_program_answers_and_future_queries(prototype):
    episode = prototype.generate(31, {"branch_policy": "matched_area"}, demos=3, queries=4)
    visible = prototype.public_turn(episode, 0)
    body = public_challenge_bytes(visible)
    identifier = public_challenge_id(visible)
    assert set(visible) == {"train", "test"}
    assert len(visible["test"]) == 1 and set(visible["test"][0]) == {"input"}
    assert b"matched_area" not in body
    assert b"program_solution" not in body

    changed = copy.deepcopy(episode)
    changed["settings"] = {"branch_policy": "unconditional"}
    changed["program_solution"] = "private"
    changed["test"][0]["output"] = [[9]]
    changed["test"][1]["input"] = [[9]]
    assert public_challenge_bytes(prototype.public_turn(changed, 0)) == body
    assert public_challenge_id(prototype.public_turn(changed, 0)) == identifier


def test_adapter_contract_and_protected_racket_parity(adapter, prototype):
    for policy in prototype.BRANCH_POLICIES:
        settings = {"branch_policy": policy}
        assert adapter.program(settings) == prototype.program(settings)
        episode = adapter.generate(0, settings, 2, 4)
        assert set(episode) == {"train", "test", "program_solution"}
        assert len(episode["train"]) == 2 and len(episode["test"]) == 4
        with prototype.RacketRunner() as execute:
            for pair in episode["train"] + episode["test"]:
                assert execute(episode["program_solution"], pair["input"]) == pair["output"]
