from __future__ import annotations

import copy
import importlib.util
import json
import random
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, find_root, public_challenge_bytes

TASK_ID = "ebe7614a49f4"
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
    return _load("generator_ebe7614a49f4", GENERATOR_PATH)


@pytest.fixture(scope="module")
def proto():
    return _load("parametric_ebe7614a49f4", PARAMETRIC / "prototype.py")


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


def _inputs(episode: dict) -> list[list[list[int]]]:
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_base_accepts_canonical_pairs_and_mirror_matches(gen):
    for pair in _canonical_pairs():
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_base_generator_is_deterministic_pure_and_controls_are_observable(gen):
    random.seed(20261026)
    state = random.getstate()
    kwargs = dict(
        difficulty="hard",
        grid_h=30,
        grid_w=30,
        n_active_rows=5,
        n_active_cols=4,
        marker_redundancy=2,
        layout="boundary_contacts",
    )
    first = gen.generate(41, 7, **kwargs)
    assert random.getstate() == state
    second = gen.generate(41, 7, **kwargs)
    assert first == second and first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert (len(first), len(first[0])) == (30, 30)
    assert len({r for r, row in enumerate(first) if 1 in row}) == 5
    assert len({c for c in range(30) if any(row[c] == 2 for row in first)}) == 4
    assert sum(cell == 1 for row in first for cell in row) == 10
    assert sum(cell == 2 for row in first for cell in row) == 8
    assert any(first[0][c] in (1, 2) or first[-1][c] in (1, 2) for c in range(30))
    assert any(row[0] in (1, 2) or row[-1] in (1, 2) for row in first)
    assert gen.self_check(first) == []


@pytest.mark.parametrize(
    ("difficulty", "size", "count"),
    (("easy", 30, 5), ("hard", 6, 1)),
)
def test_explicit_base_controls_use_declared_ranges_not_difficulty_bands(
    gen, difficulty, size, count
):
    grid = gen.generate(19, 0, difficulty=difficulty, grid_h=size, grid_w=size,
                        n_active_rows=count, n_active_cols=count,
                        marker_redundancy=2, layout="boundary_contacts")
    assert (len(grid), len(grid[0])) == (size, size)
    assert len({row for row, values in enumerate(grid) if 1 in values}) == count
    assert len({col for col in range(size) if any(row[col] == 2 for row in grid)}) == count
    assert sum(cell == 1 for row in grid for cell in row) == count * 2
    assert sum(cell == 2 for row in grid for cell in row) == count * 2
    assert gen.self_check(grid) == []


@pytest.mark.parametrize("n_active_cols", (1, 5))
def test_crossed_layout_preserves_capacity_for_dense_six_square(
    gen, n_active_cols
):
    grid = gen.generate(23, 0, difficulty="easy", grid_h=6, grid_w=6,
                        n_active_rows=5, n_active_cols=n_active_cols,
                        marker_redundancy=2, layout="crossed_markers")
    assert len({row for row, values in enumerate(grid) if 1 in values}) == 5
    assert len({col for col in range(6) if any(row[col] == 2 for row in grid)}) == n_active_cols
    assert sum(cell == 1 for row in grid for cell in row) == 10
    assert sum(cell == 2 for row in grid for cell in row) == n_active_cols * 2
    assert gen.self_check(grid) == []


def test_base_rejects_unknown_invalid_and_bool_overrides(gen):
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, typo_axis=2)
    for kwargs in (
        {"grid_h": True},
        {"grid_w": 5},
        {"n_active_rows": 0},
        {"n_active_cols": 31},
        {"marker_redundancy": 0},
        {"layout": "fixed"},
        {"difficulty": "extreme"},
    ):
        with pytest.raises((TypeError, ValueError)):
            gen.generate(1, 0, **kwargs)


def test_parametric_default_is_exact_canonical_and_alternate_is_sequential(proto):
    canonical = _canonical()["program_solution"]
    assert proto.DEFAULT == {"render": "points"}
    assert proto.program(proto.DEFAULT) == canonical
    rays = proto.program({"render": "rays"})
    assert rays != canonical
    assert "route-starts" in rays
    assert "walk-ray" in rays
    assert len({proto.program(setting) for setting in proto.SETTINGS}) == 2


def test_parametric_counts_matched_inputs_and_four_query_stress(proto):
    for demos in (2, 3, 6):
        points = proto.generate(17, {"render": "points"}, demos=demos, queries=4)
        rays = proto.generate(17, {"render": "rays"}, demos=demos, queries=4)
        assert _inputs(points) == _inputs(rays)
        assert len(points["train"]) == demos and len(points["test"]) == 4
        assert points["test"] == proto.generate(17, {"render": "points"}, demos=2, queries=4)["test"]
        assert len({proto.digest(grid) for grid in _inputs(points)}) == demos + 4
        assert points["certificate"]["survivors"] == [{"render": "points"}]
        assert rays["certificate"]["survivors"] == [{"render": "rays"}]

    stress = proto.generate(29, {"render": "rays"}, demos=3, queries=4)["test"][-1]
    assert (len(stress["input"]), len(stress["input"][0])) == (30, 30)
    profile = proto.profile(stress["input"])
    assert profile["intersection_count"] >= 16
    assert profile["selected_direction_count"] == profile["intersection_count"]
    assert profile["decoy_direction_count"] >= profile["intersection_count"]
    assert profile["route_cell_count"] >= 60
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
    grid = proto.generate(31, {"render": "rays"}, demos=2, queries=4)["test"][1]["input"]
    decoys_changed = proto.change_decoy_codes(grid)
    selected_changed = proto.change_selected_code(grid)
    assert proto.intersections(grid) == proto.intersections(decoys_changed)
    assert proto.intersections(grid) == proto.intersections(selected_changed)
    assert proto.transform(grid, {"render": "rays"}) == proto.transform(
        decoys_changed, {"render": "rays"}
    )
    assert proto.transform(grid, {"render": "rays"}) != proto.transform(
        selected_changed, {"render": "rays"}
    )


def test_parametric_contract_and_certificate_fail_closed(proto):
    for settings in ({}, {"render": "lines"}, {"render": 1}, {"render": "points", "x": 1}):
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
    forged_program["program_solution"] = proto.program({"render": "rays"})
    corruptions.append(forged_program)
    for changed in corruptions:
        with pytest.raises(ValueError):
            proto.certify(changed)


def test_adapter_contract_and_first_turn_public_privacy(proto):
    adapter = _load("adapter_ebe7614a49f4", PARAMETRIC / "adapter.py")
    promotion = json.loads((PARAMETRIC / "promotion.json").read_text())
    assert promotion["default"] == proto.DEFAULT
    assert promotion["limits"] == {"demos": [2, 6], "queries": [4, 4]}
    episode = adapter.generate(5, proto.DEFAULT, 6, 4)
    assert len(episode["train"]) == 6 and len(episode["test"]) == 4
    assert episode["program_solution"] == adapter.program(proto.DEFAULT)

    visible = {"train": episode["train"], "test": [episode["test"][0]]}
    before = public_challenge_bytes(visible)
    changed = copy.deepcopy(episode)
    changed["settings"] = {"render": "rays"}
    changed["program_solution"] = "private"
    changed["test"][0]["output"][0][0] = (changed["test"][0]["output"][0][0] + 1) % 10
    changed["test"][1]["input"][0][0] = (changed["test"][1]["input"][0][0] + 1) % 10
    assert before == public_challenge_bytes({"train": changed["train"], "test": [changed["test"][0]]})


def test_protected_racket_matches_programs_and_skipping_selector_changes_output(proto):
    grid = proto.generate(53, {"render": "rays"}, demos=2, queries=4)["test"][-1]["input"]
    with RacketBridge(timeout=60) as bridge:
        assert bridge.runtime_identity["backend"] == "racket"
        assert bridge.runtime_identity["protected"] is True
        for setting in proto.SETTINGS:
            assert _racket_apply(proto.program(setting), grid, bridge) == proto.transform(grid, setting)
        intended = _racket_apply(proto.program({"render": "rays"}), grid, bridge)
        skipped = _racket_apply(proto.ALL_DIRECTION_TOKENS_PROGRAM, grid, bridge)
        assert intended != skipped


def test_adversarial_probe_has_reusable_pure_mode(proto):
    probe = _load("adversarial_probe_ebe7614a49f4", PARAMETRIC / "adversarial_probe.py")
    report = probe.run_probe(
        prototype=proto,
        sweep_seeds=(0, 1),
        racket_cases=(),
        include_racket=False,
    )
    assert report["schema"] == "arcpuzzles-ebe7614a49f4-adversarial-probe-v1"
    assert report["status"] == "passed"
    assert report["pure_sampler_sweep"]["episodes"] == 8
    assert report["crossed_controls"]["decoy_change_preserved_output"] is True
    assert report["crossed_controls"]["selected_code_changed_output"] is True
    assert report["tamper_rejections"]["all_rejected"] is True
    assert report["public_projection"]["future_queries_hidden"] is True
    assert report["protected_racket"]["status"] == "not_run"


def test_adversarial_probe_default_racket_cases_accept_none():
    probe = _load("adversarial_probe_ebe7614a49f4_defaults", PARAMETRIC / "adversarial_probe.py")
    assert probe._racket_case_list(None) == ((0, 2), (17, 2), (0, 6), (17, 6))
