from __future__ import annotations

import copy
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root, public_challenge_bytes

TASK = "615496fbe17b"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK
PARAMETRIC = HOME / "workspace" / "parametric"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


GEN = _load(f"review_{TASK}_generator", HOME / "generator.py")


def _adapter():
    path = PARAMETRIC / "adapter.py"
    assert path.is_file(), "native parametric adapter has not been implemented"
    return _load(f"review_{TASK}_adapter", path)


def _components(grid):
    return GEN._components_for_self_check(grid)


def _big_hole_impostor():
    grid = [[0] * 16 for _ in range(12)]
    for r in range(5):
        for c in range(5):
            if r in (0, 4) or c in (0, 4):
                grid[2 + r][2 + c] = 4
    for r in range(2):
        for c in range(3):
            grid[8 + r][11 + c] = 6
    return grid


def _canonical_program() -> str:
    from arcpuzzles.catalog import Catalog

    programs = {
        variant["program_solution"]
        for variant in Catalog(ROOT)._variants()[TASK]
        if isinstance(variant.get("program_solution"), str)
    }
    assert len(programs) == 1
    return next(iter(programs))


def test_canonical_rule_mirror_matches_every_original_pair():
    pairs = canonical_pairs(TASK, root=ROOT)
    assert len(pairs) >= 3
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_self_check_rejects_a_large_hole_that_survives_dilation():
    errors = GEN.self_check(_big_hole_impostor())
    assert errors
    assert any("seal" in error or "dilation" in error for error in errors)


def test_controls_are_strict_and_exact():
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(0, 0, difficulty="extreme")
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(0, 0, bogus=1)
    for kwargs in (
        {"grid_h": 11, "grid_w": 13, "rect_h": 3, "rect_w": 4, "n_distract": 1},
        {"grid_h": 20, "grid_w": 22, "rect_h": 8, "rect_w": 7, "n_distract": 4},
    ):
        grid = GEN.generate(17, 23, difficulty="hard", **kwargs)
        assert (len(grid), len(grid[0])) == (kwargs["grid_h"], kwargs["grid_w"])
        assert GEN.self_check(grid) == []
        components = _components(grid)
        assert len(components) == 1 + kwargs["n_distract"]
        chosen = GEN.selection_intermediate(grid)["selected"]
        assert chosen["bbox_height"] == kwargs["rect_h"]
        assert chosen["bbox_width"] == kwargs["rect_w"]


def test_ordinary_generation_is_deterministic_pure_and_varied():
    state = random.getstate()
    outputs = set()
    for band in (None, "easy", "medium", "hard"):
        for seed in range(16):
            first = GEN.generate(seed, seed * 13 + 7, difficulty=band)
            second = GEN.generate(seed, seed * 13 + 7, difficulty=band)
            assert first == second and first is not second
            assert GEN.self_check(first) == []
            before = copy.deepcopy(first)
            out = GEN.rule_mirror(first)
            assert first == before
            outputs.add(json.dumps(out, separators=(",", ":")))
    assert random.getstate() == state
    assert len(outputs) >= 20


def test_default_program_is_exact_canonical_and_alternate_is_distinct():
    adapter = _adapter()
    canonical = adapter.program({"hole_behavior": "sealed"})
    persistent = adapter.program({"hole_behavior": "persistent"})
    assert canonical == _canonical_program()
    assert persistent != canonical


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_parametric_counts_prefixes_matched_inputs_and_teaching(demos):
    adapter = _adapter()
    for seed in (0, 17, 91):
        episodes = {
            mode: adapter.generate(seed, {"hole_behavior": mode}, demos, 4)
            for mode in ("sealed", "persistent")
        }
        inputs = {
            mode: [pair["input"] for pair in episode["train"] + episode["test"]]
            for mode, episode in episodes.items()
        }
        assert inputs["sealed"] == inputs["persistent"]
        assert len({json.dumps(grid) for grid in inputs["sealed"]}) == demos + 4
        for mode, episode in episodes.items():
            assert len(episode["train"]) == demos
            assert len(episode["test"]) == 4
            assert episode["program_solution"] == adapter.program({"hole_behavior": mode})
            one = adapter.generate(seed, {"hole_behavior": mode}, demos, 1)
            assert one["train"] == episode["train"]
            assert one["test"] == episode["test"][:1]
            assert adapter.first_turn_bytes(one) == adapter.first_turn_bytes(episode)
            assert adapter.audit_episode(episode, mode) == []
        assert any(
            left["output"] != right["output"]
            for left, right in zip(episodes["sealed"]["train"], episodes["persistent"]["train"])
        )


def test_parametric_sampler_retries_the_complete_scene_when_late_packing_fails():
    adapter = _adapter()
    # This exact case previously packed both large rings first, then marooned
    # the final solid distractor and raised instead of retrying the scene.
    episode = adapter.generate(19, {"hole_behavior": "sealed"}, 6, 1)
    assert len(episode["train"]) == 6
    assert adapter.audit_episode(episode, "sealed") == []


def test_dependency_intermediate_controls_selection_and_crop():
    adapter = _adapter()
    grid = adapter.generate(7, {"hole_behavior": "persistent"}, 2, 4)["test"][0]["input"]
    intermediate = adapter.dependency_intermediate(grid, {"hole_behavior": "persistent"})
    assert intermediate["hole_behavior"] == "persistent"
    assert len(intermediate["object_metrics"]) >= 3
    assert intermediate["selected_index"] is not None
    expected = adapter.solve_from_intermediate(grid, intermediate)
    assert expected == adapter.solve(grid, {"hole_behavior": "persistent"})
    wrong = copy.deepcopy(intermediate)
    wrong["selected_index"] = next(
        index for index in range(len(wrong["object_metrics"]))
        if index != intermediate["selected_index"]
    )
    assert adapter.solve_from_intermediate(grid, wrong) != expected


def test_large_query_is_substantive_30x30_and_contains_both_hole_classes():
    adapter = _adapter()
    for mode in ("sealed", "persistent"):
        pair = adapter.generate(41, {"hole_behavior": mode}, 2, 4)["test"][3]
        grid = pair["input"]
        assert (len(grid), len(grid[0])) == (30, 30)
        occupied = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value}
        assert len(occupied) >= 100
        assert len({r for r, _ in occupied}) >= 22
        assert len({c for _, c in occupied}) >= 22
        assert any(r in (0, 29) or c in (0, 29) for r, c in occupied)
        metrics = adapter.dependency_intermediate(grid, {"hole_behavior": mode})["object_metrics"]
        assert sum(item["holes_before"] > item["holes_after"] for item in metrics) == 1
        assert sum(item["holes_before"] > 0 and item["holes_before"] == item["holes_after"] for item in metrics) == 1


def test_first_turn_ignores_private_fields_answers_and_future_queries():
    adapter = _adapter()
    episode = adapter.generate(8, {"hole_behavior": "persistent"}, 3, 4)
    before = adapter.first_turn_bytes(episode)
    changed = copy.deepcopy(episode)
    changed["settings"] = {"hole_behavior": "secret"}
    changed["program_solution"] = "secret"
    for pair in changed["test"]:
        pair["output"] = [[9]]
    changed["test"][1:] = [{"input": [[9]], "output": [[1]]}]
    assert adapter.first_turn_bytes(changed) == before
    assert before == public_challenge_bytes({"train": episode["train"], "test": episode["test"][:1]})


@pytest.mark.parametrize(
    "settings",
    [None, {}, {"hole_behavior": "bogus"}, {"hole_behavior": True}, {"hole_behavior": "sealed", "x": 1}],
)
def test_invalid_settings_fail(settings):
    adapter = _adapter()
    with pytest.raises(ValueError):
        adapter.program(settings)


@pytest.mark.parametrize(
    "seed,demos,queries",
    [(True, 2, 4), (-1, 2, 4), (0, 1, 4), (0, 7, 4), (0, 2, 0), (0, 2, 5), (0, 2.0, 4)],
)
def test_invalid_request_bounds_fail(seed, demos, queries):
    adapter = _adapter()
    with pytest.raises(ValueError):
        adapter.generate(seed, {"hole_behavior": "sealed"}, demos, queries)


def test_protected_racket_matches_python_for_both_settings():
    _adapter()
    from arcpuzzles.parametric_worker import evaluate_contract

    contract = json.loads((PARAMETRIC / "promotion.json").read_text())
    jobs = [
        {"seed": 17, "settings": {"hole_behavior": mode}, "demos": 2, "queries": 4}
        for mode in ("sealed", "persistent")
    ]
    result = evaluate_contract(ROOT, TASK, contract, jobs)
    assert result["racket"]["backend"] == "racket"
    assert result["racket"]["protected"] is True
    assert [check["survivors"] for check in result["checks"]] == [
        [job["settings"]] for job in jobs
    ]
    assert [check["label_count"] for check in result["checks"]] == [6, 6]
