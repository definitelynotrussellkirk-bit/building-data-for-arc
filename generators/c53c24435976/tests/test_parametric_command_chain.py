from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "c53c24435976"
REPO = find_root(__file__)
HERE = REPO / f"generators/{TASK_ID}/workspace/parametric"


def _load(name: str, filename: str):
    path = HERE / filename
    assert path.is_file(), f"missing parametric artifact: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def proto():
    return _load("c53c24435976_parametric_prototype", "prototype.py")


def _canonical_program() -> str:
    for line in canonical_path(REPO).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row["program_solution"]
    raise AssertionError("canonical program missing")


def _decisive_grid() -> list[list[int]]:
    grid = [[0] * 9 for _ in range(8)]
    grid[0][0] = 1
    shape = [
        [1, 5, 6, 3],
        [7, 0, 2, 8],
        [4, 9, 5, 2],
    ]
    for r, row in enumerate(shape, start=3):
        for c, value in enumerate(row, start=2):
            grid[r][c] = value
    return grid


def test_default_program_is_exact_canonical_and_variant_is_distinct(proto):
    assert proto.DEFAULT == {"command_chain": "outer_only"}
    assert proto.program(proto.DEFAULT) == _canonical_program()
    assert len({proto.program(setting) for setting in proto.SETTINGS}) == 2


def test_chain_consumes_the_transformed_intermediate(proto):
    grid = _decisive_grid()
    before = copy.deepcopy(grid)
    stage1 = proto.stage_one(grid)
    assert proto.selected_inner_command(stage1) == 4
    chained = proto.transform(grid, {"command_chain": "outer_then_corner"})
    assert grid == before
    assert chained == proto.apply_code(stage1, 4)
    assert chained != stage1
    assert proto.skip_outer_transform(grid) != chained


def test_strict_settings_counts_and_grid_types(proto):
    for settings in ({}, {"command_chain": "unknown"}, {"command_chain": 1},
                     {"command_chain": "outer_only", "extra": 0}):
        with pytest.raises(ValueError):
            proto.program(settings)
    for key, value in (("seed", True), ("seed", 1.0), ("demos", 1),
                       ("demos", 7), ("demos", True), ("queries", 3),
                       ("queries", 5), ("queries", True)):
        kwargs = dict(seed=9, settings=proto.DEFAULT, demos=3, queries=4)
        kwargs[key] = value
        with pytest.raises(ValueError):
            proto.generate(**kwargs)
    malformed = _decisive_grid()
    malformed[3][2] = True
    with pytest.raises(ValueError):
        proto.stage_one(malformed)


def test_generation_is_deterministic_identifiable_and_count_independent(proto):
    for seed in (0, 17, 41):
        for setting in proto.SETTINGS:
            short = proto.generate(seed, setting, demos=2, queries=4)
            long = proto.generate(seed, setting, demos=6, queries=4)
            assert short == proto.generate(seed, setting, demos=2, queries=4)
            assert short["train"] == long["train"][:2]
            assert short["test"] == long["test"]
            assert len(short["train"]) == 2 and len(short["test"]) == 4
            pairs = short["train"] + short["test"]
            assert len({proto.digest(pair["input"]) for pair in pairs}) == 6
            assert short["certificate"]["survivors"] == [setting]
            assert short["certificate"]["surviving_shortcuts"] == []
            assert all(pair["output"] == proto.transform(pair["input"], setting)
                       for pair in pairs)


def test_two_demo_lessons_refute_frequency_and_rank_shortcuts(proto):
    required = {
        "stat_mode_min", "stat_mode_max", "stat_rare_min", "stat_rare_max",
        "stat_last_command", "stat_second_command", "stat_center_or4",
        "stat_count_mod4",
    }
    for seed in range(32):
        for setting in proto.SETTINGS:
            episode = proto.generate(seed, setting, demos=2, queries=4)
            refutations = episode["certificate"]["shortcut_refutations"]
            assert required <= set(refutations)
            assert all(refutations[name] for name in required)


def test_crossed_controls_change_only_the_intended_factor(proto):
    for seed in range(32):
        controls = proto.crossed_controls(seed)
        inner_a, inner_b = controls["vary_inner_command"]
        assert (len(inner_a), len(inner_a[0])) == (len(inner_b), len(inner_b[0]))
        assert [[cell != 0 for cell in row] for row in inner_a] == [
            [cell != 0 for cell in row] for row in inner_b]
        stage_a, stage_b = proto.stage_one(inner_a), proto.stage_one(inner_b)
        assert proto.selected_inner_command(stage_a) != proto.selected_inner_command(stage_b)
        assert proto.transform(inner_a, proto.CHAINED) != proto.transform(inner_b, proto.CHAINED)

        nuisance_a, nuisance_b = controls["vary_canvas_and_position"]
        assert (len(nuisance_a), len(nuisance_a[0])) != (len(nuisance_b), len(nuisance_b[0]))
        assert proto.stage_one(nuisance_a) == proto.stage_one(nuisance_b)
        assert proto.transform(nuisance_a, proto.CHAINED) == proto.transform(nuisance_b, proto.CHAINED)


def test_queries_include_substantive_30x30_boundary_stress(proto):
    episode = proto.generate(31, proto.CHAINED, demos=3, queries=4)
    grid = episode["test"][-1]["input"]
    output = episode["test"][-1]["output"]
    assert (len(grid), len(grid[0])) == (30, 30)
    nonzero = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    assert len(nonzero) >= 220
    assert (0, 0) in nonzero
    assert max(r for r, _ in nonzero) == 29 and max(c for _, c in nonzero) == 29
    assert len(output) == 29 and len(output[0]) == 29


def test_first_turn_projection_hides_private_state_and_future_queries(proto):
    episode = proto.generate(43, proto.CHAINED, demos=3, queries=4)
    visible = proto.public_turn(episode, 0)
    assert set(visible) == {"train", "test"}
    assert len(visible["test"]) == 1 and set(visible["test"][0]) == {"input"}
    assert all(set(pair) == {"input", "output"} for pair in visible["train"])
    body = public_challenge_bytes(visible)
    identifier = public_challenge_id(visible)

    changed = copy.deepcopy(episode)
    changed["settings"] = proto.DEFAULT
    changed["program_solution"] = "private-change"
    changed["test"][0]["output"] = [[9]]
    changed["test"][1]["input"] = [[9]]
    assert public_challenge_bytes(proto.public_turn(changed, 0)) == body
    assert public_challenge_id(proto.public_turn(changed, 0)) == identifier
    assert b"settings" not in body and b"program_solution" not in body


def test_certificate_rejects_duplicate_inputs_and_forged_outputs(proto):
    episode = proto.generate(59, proto.CHAINED, demos=3, queries=4)
    duplicate = copy.deepcopy(episode)
    duplicate["test"][0]["input"] = copy.deepcopy(duplicate["train"][0]["input"])
    with pytest.raises(ValueError, match="distinct"):
        proto.certify(duplicate)

    forged = copy.deepcopy(episode)
    forged["train"][0]["output"] = [[9]]
    with pytest.raises(ValueError):
        proto.certify(forged)


def test_adapter_contract_and_protected_racket_match(proto):
    adapter = _load("c53c24435976_parametric_adapter", "adapter.py")
    episode = adapter.generate(5, proto.CHAINED, 6, 4)
    assert (len(episode["train"]), len(episode["test"])) == (6, 4)
    assert episode["program_solution"] == adapter.program(proto.CHAINED)
    promotion = json.loads((HERE / "promotion.json").read_text(encoding="utf-8"))
    assert promotion["default"] == proto.DEFAULT
    assert promotion["limits"] == {"demos": [2, 6], "queries": [4, 4]}
    assert promotion["qualification_demos"] == 3

    decisive = _decisive_grid()
    with proto.RacketRunner() as run:
        for setting in proto.SETTINGS:
            assert run(proto.program(setting), decisive) == proto.transform(decisive, setting)
        generated = proto.generate(61, proto.CHAINED, demos=2, queries=4)
        for pair in generated["train"] + generated["test"]:
            assert run(proto.program(proto.CHAINED), pair["input"]) == pair["output"]
