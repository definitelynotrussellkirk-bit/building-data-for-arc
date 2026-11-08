"""Contract, semantic, and parametric regressions for 1118c9143cae."""
from __future__ import annotations

import copy
import importlib
import importlib.util
import hashlib
import json
import random
from pathlib import Path

import pytest

TASK_ID = "1118c9143cae"
ROOT = Path(__file__).resolve().parents[3]
BASE_RECORD = ROOT / "shared/data/base/solutions/banks/d994e8798bff/easy_p06__1118c9143cae.json"


def canonical_rule_source(task_id: str) -> str:
    assert task_id == TASK_ID
    return json.loads(BASE_RECORD.read_text())["racket_target"]["target_code"]


def canonical_rule_hash(task_id: str) -> str:
    program = canonical_rule_source(task_id)
    return hashlib.sha256(" ".join(program.split()).encode()).hexdigest()[:12]


def canonical_pairs(task_id: str) -> list[dict]:
    assert task_id == TASK_ID
    record = json.loads(BASE_RECORD.read_text())
    pairs = [copy.deepcopy(pair) for pair in record["visible_context"]["train"]]
    for pair, output in zip(
        record["visible_context"]["test_inputs"],
        record["verification"]["expected_test_outputs"],
    ):
        pairs.append({"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(output)})
    return pairs


try:
    GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
except ModuleNotFoundError:
    _generator_path = Path(__file__).resolve().parents[1] / "generator.py"
    _generator_spec = importlib.util.spec_from_file_location(f"_{TASK_ID}_generator", _generator_path)
    assert _generator_spec is not None and _generator_spec.loader is not None
    GEN = importlib.util.module_from_spec(_generator_spec)
    _generator_spec.loader.exec_module(GEN)
PARAMETRIC = Path(__file__).resolve().parents[1] / "workspace" / "parametric"


def _load_parametric(name: str):
    path = PARAMETRIC / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"_{TASK_ID}_{name}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _key(grid):
    return tuple(tuple(row) for row in grid)


def _pair(seed: int, sample_index: int, difficulty: str) -> dict:
    grid = GEN.generate(seed, sample_index, difficulty=difficulty)
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def _nonzero(grid):
    return [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]


def test_metadata_rule_hash_and_all_canonical_pairs_are_in_domain() -> None:
    assert GEN.VERSION == "2.0.0"
    assert GEN.RULE_HASH == canonical_rule_hash(TASK_ID) == "3c7019266d5c"
    assert set(GEN.AXES) == {
        "grid_h",
        "grid_w",
        "cell_count",
        "n_colors",
        "scene_profile",
    }
    assert canonical_rule_source(TASK_ID) == GEN.CANONICAL_PROGRAM

    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 4
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == source


def test_exact_live_overrides_and_incompatible_combinations() -> None:
    cases = [
        dict(grid_h=7, grid_w=8, cell_count=3, n_colors=2, scene_profile="interior"),
        dict(grid_h=5, grid_w=5, cell_count=5, n_colors=3, scene_profile="boundary"),
        dict(grid_h=9, grid_w=11, cell_count=7, n_colors=4, scene_profile="fixed_point"),
        dict(grid_h=30, grid_w=30, cell_count=40, n_colors=8, scene_profile="boundary"),
    ]
    for index, overrides in enumerate(cases):
        grid = GEN.generate(700 + index, index, difficulty="easy", **overrides)
        assert GEN.self_check(grid, meta={"overrides": overrides}) == []
        observed = GEN.observe_overrides(grid)
        for name, value in overrides.items():
            assert observed[name] == value

    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, typo_axis=3)
    with pytest.raises((TypeError, ValueError), match="integer|bool"):
        GEN.generate(1, 0, grid_h=True)
    with pytest.raises(ValueError, match="fixed_point|odd") as exc:
        GEN.generate(1, 0, grid_h=8, grid_w=10, scene_profile="fixed_point")
    assert set(getattr(exc.value, "incompatible_axes", ())) >= {
        "grid_h",
        "grid_w",
        "scene_profile",
    }
    with pytest.raises(ValueError, match="n_colors|cell_count") as exc:
        GEN.generate(1, 0, cell_count=3, n_colors=4)
    assert set(getattr(exc.value, "incompatible_axes", ())) >= {
        "cell_count",
        "n_colors",
    }


def test_profiles_realize_center_boundary_and_substantive_30x30_content() -> None:
    center = GEN.generate(
        91,
        0,
        grid_h=9,
        grid_w=9,
        cell_count=9,
        n_colors=4,
        scene_profile="fixed_point",
    )
    assert center[4][4] != 0
    assert GEN.observe_overrides(center)["scene_profile"] == "fixed_point"
    assert GEN.rule_mirror(center)[4][4] == center[4][4]

    boundary = GEN.generate(
        92,
        1,
        grid_h=12,
        grid_w=17,
        cell_count=14,
        n_colors=5,
        scene_profile="boundary",
    )
    h, w = len(boundary), len(boundary[0])
    boundary_cells = [
        (r, c)
        for r, c, _ in _nonzero(boundary)
        if r in (0, h - 1) or c in (0, w - 1)
    ]
    assert len(boundary_cells) >= 4
    assert GEN.observe_overrides(boundary)["scene_profile"] == "boundary"

    large = GEN.generate(
        93,
        2,
        grid_h=30,
        grid_w=30,
        cell_count=40,
        n_colors=8,
        scene_profile="boundary",
    )
    assert (len(large), len(large[0])) == (30, 30)
    assert len(_nonzero(large)) == 40
    assert len({v for _, _, v in _nonzero(large)}) == 8
    rows = {r for r, _, _ in _nonzero(large)}
    cols = {c for _, c, _ in _nonzero(large)}
    assert len(rows) >= 10 and len(cols) >= 10
    assert GEN.rule_mirror(large) != large


def test_generation_is_deterministic_fresh_and_global_rng_isolated() -> None:
    random.seed(20261026)
    state = random.getstate()
    first = GEN.generate(77, 9, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(77, 9, difficulty="hard")
    assert random.getstate() == state
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert GEN.generate(77, 9, difficulty="hard") == second


def test_default_census_is_lawful_varied_and_exercises_every_profile() -> None:
    for difficulty in ("easy", "medium", "hard"):
        grids = [GEN.generate(10000 + i, i, difficulty=difficulty) for i in range(120)]
        assert all(GEN.self_check(grid) == [] for grid in grids)
        assert all(GEN.strict_canonical_like(grid) == [] for grid in grids)
        assert len({_key(grid) for grid in grids}) >= 115
        profiles = {GEN.observe_overrides(grid)["scene_profile"] for grid in grids}
        assert profiles == set(GEN.SCENE_PROFILES)
        assert all(GEN.rule_mirror(grid) != grid for grid in grids)


def test_semantic_witnesses_kill_named_rivals_and_lessons_are_identifiable() -> None:
    for difficulty in ("easy", "medium", "hard"):
        grids = [GEN.generate(15000 + i, i, difficulty=difficulty) for i in range(120)]
        for witness_name, witness in GEN.SEMANTIC_WITNESSES.items():
            firing = [grid for grid in grids if witness(grid)]
            assert firing, (difficulty, witness_name)
            for grid in firing[:20]:
                official = GEN.rule_mirror(grid)
                assert any(
                    GEN.SEMANTIC_RIVALS[name](grid) != official
                    for name in GEN.WITNESS_RIVALS[witness_name]
                )

        for start in range(12):
            demos = [
                _pair(20000 + start, start + offset, difficulty)
                for offset in range(GEN.EXAMPLES_NEEDED)
            ]
            query = _pair(20000 + start, start + GEN.EXAMPLES_NEEDED, difficulty)
            assert GEN.lesson_identifiable(demos, query) == []
            for competitor in GEN.LESSON_COMPETITORS.values():
                assert any(
                    competitor(pair["input"]) != pair["output"]
                    for pair in demos
                )


def test_self_check_rejects_targeted_impostors() -> None:
    lawful = GEN.generate(
        501,
        3,
        grid_h=9,
        grid_w=11,
        cell_count=8,
        n_colors=4,
        scene_profile="interior",
    )
    h, w = len(lawful), len(lawful[0])

    blank = [[0] * w for _ in range(h)]
    single_color = [[0] * w for _ in range(h)]
    for r, c, _ in _nonzero(lawful):
        single_color[r][c] = 3
    mirrored_collision = copy.deepcopy(lawful)
    r, c, value = _nonzero(lawful)[0]
    mirrored_collision[h - 1 - r][w - 1 - c] = value
    bool_cell = copy.deepcopy(lawful)
    bool_cell[0][0] = True

    for name, grid in {
        "blank": blank,
        "single_color": single_color,
        "mirrored_collision": mirrored_collision,
        "bool_cell": bool_cell,
    }.items():
        assert GEN.self_check(grid), name
        assert GEN.observe_overrides(grid) == {}, name


# Parametric tests are intentionally in the same file so packet task-tests run
# the repaired base and the proposed family together.

def test_parametric_programs_contract_and_default_exactness() -> None:
    prototype = _load_parametric("prototype")
    assert prototype.program({"echo_scope": "all"}) == canonical_rule_source(TASK_ID)
    rarest = prototype.program({"echo_scope": "rarest_color"})
    assert rarest != canonical_rule_source(TASK_ID)
    assert rarest.startswith("(rule!")
    with pytest.raises(ValueError, match="exactly echo_scope"):
        prototype.program({})
    with pytest.raises(ValueError, match="echo_scope"):
        prototype.program({"echo_scope": "all", "extra": 1})
    with pytest.raises(ValueError, match="echo_scope"):
        prototype.program({"echo_scope": "unknown"})


def test_parametric_generation_supports_2_to_6_demos_and_exactly_four_queries() -> None:
    prototype = _load_parametric("prototype")
    for demos in range(2, 7):
        all_episode = prototype.generate(7000 + demos, {"echo_scope": "all"}, demos, 4)
        rare_episode = prototype.generate(7000 + demos, {"echo_scope": "rarest_color"}, demos, 4)
        assert len(all_episode["train"]) == len(rare_episode["train"]) == demos
        assert len(all_episode["test"]) == len(rare_episode["test"]) == 4
        all_inputs = [pair["input"] for pair in all_episode["train"] + all_episode["test"]]
        rare_inputs = [pair["input"] for pair in rare_episode["train"] + rare_episode["test"]]
        assert all_inputs == rare_inputs
        assert len({_key(grid) for grid in all_inputs}) == demos + 4
        assert any((len(grid), len(grid[0])) == (30, 30) for grid in all_inputs[demos:])
        assert all(prototype.scene_errors(grid) == [] for grid in all_inputs)
        for pair in all_episode["train"] + all_episode["test"]:
            assert pair["output"] == prototype.apply_python(pair["input"], "all")
        for pair in rare_episode["train"] + rare_episode["test"]:
            assert pair["output"] == prototype.apply_python(pair["input"], "rarest_color")

    for bad_demos in (1, 7, True):
        with pytest.raises(ValueError, match="demos"):
            prototype.generate(1, {"echo_scope": "all"}, bad_demos, 4)
    for bad_queries in (1, 3, 5, True):
        with pytest.raises(ValueError, match="queries"):
            prototype.generate(1, {"echo_scope": "all"}, 3, bad_queries)


def test_two_demo_core_defeats_declared_parametric_shortcuts_on_every_query() -> None:
    prototype = _load_parametric("prototype")
    for seed in range(32):
        for scope in prototype.ECHO_SCOPES:
            episode = prototype.generate(seed, {"echo_scope": scope}, 2, 4)
            demos = episode["train"]
            for name, rival in prototype.SHORTCUTS.items():
                survives = all(rival(pair["input"]) == pair["output"] for pair in demos)
                if survives:
                    assert all(
                        rival(pair["input"]) == pair["output"]
                        for pair in episode["test"]
                    ), (seed, scope, name)


def test_parametric_adapter_and_promotion_contract_are_native_shape() -> None:
    adapter = _load_parametric("adapter")
    contract = json.loads((PARAMETRIC / "promotion.json").read_text())
    assert contract["schema"] == "arcpuzzles-parametric-adapter-v1"
    assert contract["parameters"] == {"echo_scope": ["all", "rarest_color"]}
    assert contract["default"] == {"echo_scope": "all"}
    assert contract["qualification_demos"] == 3
    assert contract["limits"] == {"demos": [2, 6], "queries": [4, 4]}
    assert adapter.program({"echo_scope": "all"}) == canonical_rule_source(TASK_ID)
    episode = adapter.generate(17, {"echo_scope": "rarest_color"}, 3, 4)
    assert set(episode) == {"train", "test", "program_solution"}


def test_adversarial_probe_reports_no_tested_ambiguity(tmp_path: Path) -> None:
    probe = _load_parametric("adversarial_probe")
    out = tmp_path / "report.json"
    report = probe.run_probe(out=out, seeds=range(24))
    assert report["schema"] == "arcpuzzles-1118-parametric-adversarial-v1"
    assert report["status"] == "passed"
    assert report["ambiguous_lessons"] == []
    assert report["matched_input_failures"] == []
    assert report["boundary_failures"] == []
    assert "ragged_grid" in report["validator_attacks_checked"]
    assert out.is_file()


def test_parametric_intermediate_crosses_color_and_count_shortcuts() -> None:
    prototype = _load_parametric("prototype")
    observed_colors = set()
    observed_counts = set()
    for seed in range(24):
        episode = prototype.generate(seed, {"echo_scope": "rarest_color"}, 2, 4)
        demo_intermediates = []
        for pair in episode["train"]:
            color = prototype.rarest_color(pair["input"])
            count = prototype.color_counts(pair["input"])[color]
            observed_colors.add(color)
            observed_counts.add(count)
            demo_intermediates.append((color, count))
        assert demo_intermediates[0][0] != demo_intermediates[1][0]
        assert demo_intermediates[0][1] != demo_intermediates[1][1]
    assert len(observed_colors) >= 6
    assert observed_counts == {2, 3}


def test_episode_validator_rejects_duplicate_stale_forged_and_malformed_material() -> None:
    prototype = _load_parametric("prototype")
    settings = {"echo_scope": "rarest_color"}
    episode = prototype.generate(404, settings, 3, 4)
    assert prototype.validate_episode(episode, settings) == []

    duplicate = copy.deepcopy(episode)
    duplicate["test"][0]["input"] = copy.deepcopy(duplicate["train"][0]["input"])
    duplicate["test"][0]["output"] = copy.deepcopy(duplicate["train"][0]["output"])
    assert any("distinct" in error or "duplicate" in error for error in prototype.validate_episode(duplicate, settings))

    stale = copy.deepcopy(episode)
    stale["program_solution"] = canonical_rule_source(TASK_ID)
    assert any("program" in error for error in prototype.validate_episode(stale, settings))

    forged = copy.deepcopy(episode)
    forged["test"][1]["output"][0][0] = 9 if forged["test"][1]["output"][0][0] != 9 else 8
    assert any("label" in error or "output" in error for error in prototype.validate_episode(forged, settings))

    malformed = copy.deepcopy(episode)
    malformed["train"][0]["input"][0][0] = True
    assert any("integer" in error or "cell" in error for error in prototype.validate_episode(malformed, settings))

    wrong_count = copy.deepcopy(episode)
    wrong_count["test"] = wrong_count["test"][:3]
    assert any("four" in error or "queries" in error for error in prototype.validate_episode(wrong_count, settings))


def test_episode_validator_rejects_ragged_grid_without_crashing() -> None:
    prototype = _load_parametric("prototype")
    settings = {"echo_scope": "rarest_color"}
    episode = prototype.generate(405, settings, 2, 4)
    ragged = copy.deepcopy(episode)
    ragged["train"][0]["input"][1] = ragged["train"][0]["input"][1][:-1]

    errors = prototype.validate_episode(ragged, settings)

    assert any("rectangular" in error for error in errors)
