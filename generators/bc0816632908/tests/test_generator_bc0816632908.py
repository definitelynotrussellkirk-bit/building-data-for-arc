from __future__ import annotations

import copy
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest


TASK = "bc0816632908"
TASK_HOME = Path(__file__).resolve().parents[1]
REPO = TASK_HOME.parents[1]
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


def _load_module():
    name = f"candidate_{TASK}"
    sys.modules.pop(name, None)
    spec = importlib.util.spec_from_file_location(name, TASK_HOME / "generator.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


GEN = _load_module()


def canonical_pairs():
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for raw in path.read_text().splitlines():
        row = json.loads(raw)
        if row.get("task_id") == TASK:
            test = row["test"] if isinstance(row["test"], list) else [row["test"]]
            return list(row["train"]) + list(test)
    raise AssertionError("canonical task row missing")


def changed_cells(before, after):
    return {
        (r, c)
        for r, row in enumerate(before)
        for c, value in enumerate(row)
        if value != after[r][c]
    }


def test_metadata_pins_the_selected_rule_and_minimal_axis_contract():
    assert GEN.RULE_HASH == "6868d528f0b2"
    assert set(GEN.AXES) == {"scene_profile"}
    assert set(GEN.SCENE_PROFILES) == set(
        GEN.AXES["scene_profile"]["valid"].split("|")
    )
    assert GEN.HELPFUL_TEXTURES == GEN.DEGENERATE_TEXTURES == ()


def test_runner_selected_rule_source_matches_canonical_source():
    canonical_path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    canonical_source = None
    for raw in canonical_path.read_text().splitlines():
        row = json.loads(raw)
        if row.get("task_id") == TASK:
            canonical_source = row["program_solution"]
            break
    assert canonical_source is not None
    base_path = (
        REPO
        / "shared"
        / "data"
        / "base"
        / "solutions"
        / "training"
        / "7447852a__bc0816632908.json"
    )
    base = json.loads(base_path.read_text())
    selected = base["racket_target"]["target_code"]
    normalize = lambda source: " ".join(source.split())
    assert normalize(selected) == normalize(canonical_source)


def test_every_canonical_input_is_owned_and_exactly_solved():
    pairs = canonical_pairs()
    assert len(pairs) == 4
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == pair["input"]


def test_three_profile_schedule_repeats_in_every_difficulty_band():
    for band in ("easy", "medium", "hard"):
        realized = []
        for sample_index in range(9):
            grid = GEN.generate(10_000 + sample_index, sample_index, difficulty=band)
            analysis = GEN._analysis(grid)
            assert analysis["errors"] == []
            assert GEN.self_check(grid, difficulty=band) == []
            assert GEN.rule_mirror(grid) == analysis["output"]
            realized.append(analysis["scene_profile"])
        assert realized[:3] == list(GEN.PROFILE_CYCLE)
        assert realized[3:6] == realized[:3]
        assert realized[6:9] == realized[:3]


def test_fixed_sample_index_canonical_profile_has_seed_diversity():
    grids = {
        tuple(map(tuple, GEN.generate(seed, 0, difficulty="medium")))
        for seed in range(40)
    }
    assert len(grids) >= 8


def test_generated_lessons_contain_multi_cell_components_and_recolor_whole_objects():
    for profile in GEN.SCENE_PROFILES:
        grid = GEN.generate(20_000 + len(profile), 4, scene_profile=profile)
        analysis = GEN._analysis(grid)
        components = analysis["components"]
        assert len(components) >= 6
        assert sum(len(component) > 1 for component in components) >= 4
        output = GEN.rule_mirror(grid)
        for index, component in enumerate(components):
            values = {output[r][c] for r, c in component}
            assert values == ({4} if index % 3 == 0 else {0})
        assert changed_cells(grid, output) == {
            cell
            for index, component in enumerate(components)
            if index % 3 == 0
            for cell in component
        }


def test_noncanonical_profiles_break_the_fixed_periodic_stencil_shortcut():
    for profile in ("shape_mix", "row_order_trap"):
        disagreements = 0
        for sample_index in range(12):
            grid = GEN.generate(30_000 + sample_index, sample_index, scene_profile=profile)
            if GEN.rule_mirror(grid) != GEN.fixed_periodic_stencil(grid):
                disagreements += 1
        assert disagreements == 12


def test_row_order_trap_reverses_at_least_one_column_vs_row_order_decision():
    for sample_index in range(12):
        grid = GEN.generate(40_000 + sample_index, sample_index, scene_profile="row_order_trap")
        analysis = GEN._analysis(grid)
        tops = [min(r for r, _c in component) for component in analysis["components"]]
        assert any(left > right for left, right in zip(tops, tops[1:]))
        assert GEN.rule_mirror(grid) != GEN.row_major_third(grid)


def test_exact_scene_profile_override_is_observable_and_unknown_controls_reject():
    for band in ("easy", "medium", "hard"):
        for profile in GEN.SCENE_PROFILES:
            grid = GEN.generate(50_000 + len(profile), 7, difficulty=band, scene_profile=profile)
            assert GEN.observe_overrides(grid) == {"scene_profile": profile}
            assert GEN.self_check(
                grid,
                difficulty=band,
                meta={"overrides": {"scene_profile": profile}},
            ) == []
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, typo_axis="silent override bugs are forbidden")
    with pytest.raises(ValueError):
        GEN.generate(1, 0, scene_profile="not_a_profile")
    with pytest.raises(ValueError):
        GEN.generate(1, 0, difficulty="expert")


@pytest.mark.parametrize(
    "grid",
    [
        [],
        [[]],
        [[2] * 12 for _ in range(3)],
        [[0]],
        [[0, 0], [0, 0]],
        [[2, 0, 2, 0, 2, 0]],
        [[2, 0, 2] for _ in range(3)],
        [[False, 2], [2, 0]],
        [[2, 0], [2]],
        [[2, 7, 2], [0, 0, 2], [2, 2, 2]],
    ],
)
def test_self_check_fails_closed_on_minimal_impostors(grid):
    assert GEN.self_check(grid)


def test_determinism_fresh_returns_and_global_rng_independence():
    random.seed(991)
    state = random.getstate()
    first = GEN.generate(61, 5, difficulty="hard", scene_profile="shape_mix")
    assert random.getstate() == state
    second = GEN.generate(61, 5, difficulty="hard", scene_profile="shape_mix")
    assert first == second and first is not second and first[0] is not second[0]
    first[0][0] = 9
    assert GEN.generate(61, 5, difficulty="hard", scene_profile="shape_mix") == second


def test_each_three_demo_window_identifies_the_next_query_against_declared_rivals():
    for band in ("easy", "medium", "hard"):
        for start in range(6):
            episode = []
            for sample_index in range(start, start + GEN.EXAMPLES_NEEDED + 1):
                grid = GEN.generate(70_000 + start, sample_index, difficulty=band)
                episode.append({"input": grid, "output": GEN.rule_mirror(grid)})
            assert GEN.lesson_identifiable(episode[:-1], episode[-1]) == []


@pytest.mark.parametrize(
    ("seed", "sample_index", "difficulty"),
    [
        (True, 0, None),
        (1.0, 0, None),
        ("1", 0, None),
        (1, True, None),
        (1, 1.0, None),
        (1, "0", None),
        (1, -1, None),
        (1, 0, True),
        (1, 0, 0),
        (1, 0, 1.0),
        (1, 0, "expert"),
    ],
)
def test_generate_rejects_noncanonical_public_call_scalars(
    seed, sample_index, difficulty
):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(seed, sample_index, difficulty=difficulty)


def _load_parametric_prototype():
    path = TASK_HOME / "workspace" / "parametric" / "selection_schedule.py"
    assert path.is_file(), "parametric selection-schedule prototype is missing"
    name = f"parametric_{TASK}"
    sys.modules.pop(name, None)
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _canonical_program_source():
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for raw in path.read_text().splitlines():
        row = json.loads(raw)
        if row.get("task_id") == TASK:
            return row["program_solution"]
    raise AssertionError("canonical task row missing")


def test_parametric_default_rule_is_exactly_canonical():
    prototype = _load_parametric_prototype()
    assert prototype.ALLOWED_SETTINGS == ((2, 0), (2, 1), (3, 0), (3, 1))
    assert prototype.DEFAULT_SETTING == (3, 0)
    source = prototype.racket_source(period=3, phase=0, root=REPO)
    assert source == _canonical_program_source()
    assert prototype.normalized_hash(source) == GEN.RULE_HASH


def test_parametric_period_and_phase_select_whole_components_distinctly():
    prototype = _load_parametric_prototype()
    grid = GEN.generate(91_337, 1, difficulty="medium", scene_profile="shape_mix")
    facts = GEN._analysis(grid)
    assert len(facts["components"]) >= 6

    rendered = {}
    for period, phase in prototype.ALLOWED_SETTINGS:
        output = prototype.python_output(grid, period=period, phase=phase)
        rendered[(period, phase)] = json.dumps(output, separators=(",", ":"))
        for index, component in enumerate(facts["components"]):
            expected = 4 if index % period == phase else 0
            assert {output[row][col] for row, col in component} == {expected}

    assert len(set(rendered.values())) == len(prototype.ALLOWED_SETTINGS)
