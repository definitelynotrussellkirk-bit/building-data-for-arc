from __future__ import annotations

import copy
import importlib.util
import json
import random
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, find_root

TASK_ID = "89dfcff52ee8"
ROOT = find_root(__file__)
GENERATOR_PATH = ROOT / f"generators/{TASK_ID}/generator.py"
PARAMETRIC = ROOT / f"generators/{TASK_ID}/workspace/parametric"


def _load(name: str, path: Path):
    assert path.is_file(), f"missing artifact: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def gen():
    return _load("generator_89dfcff52ee8", GENERATOR_PATH)


@pytest.fixture(scope="module")
def proto():
    return _load("parametric_89dfcff52ee8", PARAMETRIC / "prototype.py")


def _canonical() -> dict:
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError(TASK_ID)


def _canonical_pairs() -> list[dict]:
    row = _canonical()
    test = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return [*row["train"], *test]


def _racket_apply(program: str, grid: list[list[int]], bridge: RacketBridge):
    wrapped = wrap_rule(program)
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    return bridge.eval_text(f"({wrapped} {literal})")


def test_canonical_pairs_include_singleton_rows_and_are_accepted(gen):
    pairs = _canonical_pairs()
    assert any(
        any(sum(cell != 0 for cell in row) == 1 for row in pair["input"])
        for pair in pairs
    )
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_base_generator_is_deterministic_pure_and_generates_singletons(gen):
    random.seed(20261026)
    state = random.getstate()
    first = gen.generate(41, 7, difficulty="medium")
    assert random.getstate() == state
    second = gen.generate(41, 7, difficulty="medium")
    assert first == second and first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert gen.self_check(first, difficulty="medium") == []

    draws = [gen.generate(900 + seed, seed, difficulty=None) for seed in range(36)]
    assert any(any(sum(v != 0 for v in row) == 1 for row in grid) for grid in draws)
    assert all(gen.self_check(grid) == [] for grid in draws)


@pytest.mark.parametrize(
    ("axis", "values"),
    [
        ("grid_h", (6, 30)),
        ("grid_w", (7, 30)),
        ("active_rows", (2, 6)),
        ("texture", ("balanced", "singleton_mix", "boundary_contacts")),
    ],
)
def test_base_controls_are_exact_and_observable(gen, axis, values):
    for value in values:
        grid = gen.generate(71, 9, difficulty="easy", **{axis: value})
        observed = gen.observe_overrides(grid)
        assert observed[axis] == value
        assert gen.self_check(grid, meta={"overrides": {axis: value}}) == []


def test_base_rejects_unknown_invalid_and_bool_overrides(gen):
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, typo_axis=2)
    for kwargs in (
        {"grid_h": True},
        {"grid_w": 6},
        {"active_rows": 1},
        {"texture": "degenerate"},
        {"difficulty": "extreme"},
    ):
        with pytest.raises((TypeError, ValueError)):
            gen.generate(1, 0, **kwargs)


def _all_inputs(episode: dict) -> list[list[list[int]]]:
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_parametric_default_is_exact_canonical_and_alternate_is_sequential(proto):
    canonical = _canonical()["program_solution"]
    assert proto.DEFAULT == {"closure": "rows_only"}
    assert proto.program(proto.DEFAULT) == canonical
    alternate = proto.program({"closure": "rows_then_columns"})
    assert alternate != canonical
    assert "col-close" in alternate
    assert len({proto.program(setting) for setting in proto.SETTINGS}) == 2


def test_parametric_counts_matched_inputs_and_four_query_stress(proto):
    for demos in (2, 3, 6):
        rows = proto.generate(17, {"closure": "rows_only"}, demos=demos, queries=4)
        composed = proto.generate(17, {"closure": "rows_then_columns"}, demos=demos, queries=4)
        assert _all_inputs(rows) == _all_inputs(composed)
        assert len(rows["train"]) == demos and len(rows["test"]) == 4
        assert rows["test"] == proto.generate(
            17, {"closure": "rows_only"}, demos=2, queries=4
        )["test"]
        assert len({proto.digest(grid) for grid in _all_inputs(rows)}) == demos + 4
        assert rows["certificate"]["survivors"] == [{"closure": "rows_only"}]
        assert composed["certificate"]["survivors"] == [{"closure": "rows_then_columns"}]

    stress = proto.generate(29, {"closure": "rows_then_columns"}, demos=3, queries=4)["test"][-1]
    assert (len(stress["input"]), len(stress["input"][0])) == (30, 30)
    profile = proto.profile(stress["input"])
    assert profile["row_intermediate_cells"] >= 100
    assert profile["composed_cells"] >= 180
    assert profile["touches_all_boundaries"]


def test_minimum_lesson_refutes_relevant_shortcuts(proto):
    for seed in (0, 17, 43):
        for setting in proto.SETTINGS:
            episode = proto.generate(seed, setting, demos=2, queries=4)
            certificate = episode["certificate"]
            assert certificate["survivors"] == [setting]
            assert set(certificate["extra_refutations"]) == set(proto.RIVAL_NAMES)
            assert all(indices for indices in certificate["extra_refutations"].values())
            for pair in episode["train"] + episode["test"]:
                assert proto.profile(pair["input"])["sequentially_decisive"]


def test_crossed_controls_separate_intermediate_from_nuisance(proto):
    grid = proto.generate(31, {"closure": "rows_then_columns"}, demos=2, queries=4)["test"][1]["input"]
    recolored = proto.recolor_markers(grid)
    shifted = proto.shift_one_endpoint(grid)
    assert proto.marker_positions(grid) == proto.marker_positions(recolored)
    assert proto.row_intermediate(grid) == proto.row_intermediate(recolored)
    assert proto.transform(grid, {"closure": "rows_then_columns"}) == proto.transform(
        recolored, {"closure": "rows_then_columns"}
    )
    assert proto.profile(grid)["dimensions"] == proto.profile(shifted)["dimensions"]
    assert proto.profile(grid)["active_rows"] == proto.profile(shifted)["active_rows"]
    assert proto.row_intermediate(grid) != proto.row_intermediate(shifted)
    assert proto.transform(grid, {"closure": "rows_then_columns"}) != proto.transform(
        shifted, {"closure": "rows_then_columns"}
    )


def test_parametric_contract_and_certificate_fail_closed(proto):
    for settings in ({}, {"closure": "both"}, {"closure": 1}, {"closure": "rows_only", "x": 1}):
        with pytest.raises(ValueError):
            proto.program(settings)
    for key, value in (("seed", True), ("demos", 1), ("demos", 7), ("queries", 1), ("queries", 5)):
        request = {"seed": 7, "settings": proto.DEFAULT, "demos": 3, "queries": 4}
        request[key] = value
        with pytest.raises(ValueError):
            proto.generate(**request)

    episode = proto.generate(7, proto.DEFAULT, demos=2, queries=4)
    corruptions = []
    wrong_label = copy.deepcopy(episode)
    wrong_label["train"][0]["output"] = [[9]]
    corruptions.append(wrong_label)
    duplicate = copy.deepcopy(episode)
    duplicate["test"][0]["input"] = copy.deepcopy(duplicate["train"][0]["input"])
    corruptions.append(duplicate)
    bad_cell = copy.deepcopy(episode)
    bad_cell["test"][0]["input"][0][0] = True
    corruptions.append(bad_cell)
    forged_program = copy.deepcopy(episode)
    forged_program["program_solution"] = proto.program({"closure": "rows_then_columns"})
    corruptions.append(forged_program)
    for changed in corruptions:
        with pytest.raises(ValueError):
            proto.certify(changed)


def test_adapter_contract(proto):
    adapter = _load("adapter_89dfcff52ee8", PARAMETRIC / "adapter.py")
    promotion = json.loads((PARAMETRIC / "promotion.json").read_text())
    assert promotion["default"] == proto.DEFAULT
    assert promotion["limits"] == {"demos": [2, 6], "queries": [4, 4]}
    episode = adapter.generate(5, proto.DEFAULT, 6, 4)
    assert len(episode["train"]) == 6 and len(episode["test"]) == 4
    assert episode["program_solution"] == adapter.program(proto.DEFAULT)


def test_protected_racket_matches_both_programs_and_wrong_intermediate_differs(proto):
    grid = proto.generate(53, {"closure": "rows_then_columns"}, demos=2, queries=4)["test"][-1]["input"]
    with RacketBridge(timeout=60) as bridge:
        assert bridge.runtime_identity["backend"] == "racket"
        assert bridge.runtime_identity["protected"] is True
        for setting in proto.SETTINGS:
            assert _racket_apply(proto.program(setting), grid, bridge) == proto.transform(grid, setting)
        intended = _racket_apply(proto.program({"closure": "rows_then_columns"}), grid, bridge)
        skipped = _racket_apply(proto.SKIP_ROW_CLOSURE_PROGRAM, grid, bridge)
        wrong_order = _racket_apply(proto.COLUMNS_THEN_ROWS_PROGRAM, grid, bridge)
        assert intended != skipped
        assert intended != wrong_order


def test_adversarial_probe_has_reusable_pure_contract(proto):
    probe = _load(
        "adversarial_probe_89dfcff52ee8",
        PARAMETRIC / "adversarial_probe.py",
    )
    report = probe.run_probe(
        prototype=proto,
        sweep_seeds=(0, 1),
        racket_cases=(),
        include_racket=False,
    )
    assert report["schema"] == "arcpuzzles-89df-adversarial-probe-v1"
    assert report["status"] == "passed"
    assert report["pure_sampler_sweep"]["episodes"] == 8
    assert report["pure_sampler_sweep"]["minimum_demo_episodes"] == 4
    assert report["crossed_controls"]["nuisance_preserved_intermediate"] is True
    assert report["crossed_controls"]["endpoint_changed_intermediate"] is True
    assert report["tamper_rejections"]["all_rejected"] is True
    assert report["public_projection"]["future_queries_hidden"] is True
    assert report["protected_racket"]["status"] == "not_run"
