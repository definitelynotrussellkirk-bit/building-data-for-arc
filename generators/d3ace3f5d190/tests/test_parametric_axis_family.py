"""Regression and native parametric tests for d3ace3f5d190."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "d3ace3f5d190"
ROOT = find_root(__file__)
HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"


def load_parametric(name: str):
    path = PARAMETRIC / f"{name}.py"
    assert path.is_file(), f"missing parametric source: {path}"
    module_name = f"_{TASK_ID}_{name}_{abs(hash(path))}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def base():
    module, _, _ = load_selected_generator(TASK_ID, root=ROOT)
    return module


def canonical_program() -> str:
    catalog = Catalog(ROOT)
    row = catalog.describe(TASK_ID)
    programs = {
        item["program_solution"]
        for item in catalog._variants()[row.get("rule_task_id", TASK_ID)]
    }
    assert len(programs) == 1
    return next(iter(programs))


def conflict_count(grid: list[list[int]], axis: str = "main") -> int:
    n = len(grid)
    count = 0
    for r in range(n):
        for c in range(r + 1, n):
            rr, cc = ((c, r) if axis == "main" else (n - 1 - c, n - 1 - r))
            if grid[r][c] and grid[rr][cc] and grid[r][c] != grid[rr][cc]:
                count += 1
    return count


def test_base_rule_replays_every_canonical_pair() -> None:
    module = base()
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == 5
    for pair in pairs:
        assert module.rule_mirror(pair["input"], "main") == pair["output"]


def test_base_generator_controls_are_strict_and_observable() -> None:
    module = base()
    with pytest.raises(ValueError):
        module.generate(0, 0, typo=1)
    with pytest.raises(ValueError):
        module.generate(0, 0, grid_h=6, grid_w=7)
    with pytest.raises(ValueError):
        module.generate(0, 0, grid_size=6, grid_h=7, grid_w=7)

    anchored = module.generate(4, 2, grid_size=8, anchor_corner=True, palette_kind="warm")
    plain = module.generate(4, 2, grid_size=8, anchor_corner=False, palette_kind="warm")
    assert (len(anchored), len(anchored[0])) == (8, 8)
    corners = [(0, 0), (0, 7), (7, 0), (7, 7)]
    assert sum(anchored[r][c] == 8 for r, c in corners) == 1
    assert all(plain[r][c] != 8 for r, c in corners)
    assert anchored != plain

    warm = module.generate(7, 1, palette_kind="warm", grid_size=9)
    cool = module.generate(7, 1, palette_kind="cool", grid_size=9)
    warm_colors = {v for row in warm for v in row if v not in (0, 8)}
    cool_colors = {v for row in cool for v in row if v not in (0, 8)}
    assert warm_colors <= set(module.PALETTES["warm"])
    assert cool_colors <= set(module.PALETTES["cool"])
    assert warm_colors != cool_colors

    forced = module.generate(11, 3, asymmetry_force=True, grid_size=9)
    unforced = module.generate(11, 3, asymmetry_force=False, grid_size=9)
    assert conflict_count(forced, "main") >= 1
    assert conflict_count(unforced, "main") == 0


def test_base_generator_covers_both_sides_and_rejects_degenerates() -> None:
    module = base()
    for index in range(32):
        grid = module.generate(100 + index, index)
        assert not module.self_check(grid)
        assert any(grid[r][c] for r in range(len(grid)) for c in range(len(grid)) if r < c)
        assert any(grid[r][c] for r in range(len(grid)) for c in range(len(grid)) if r > c)
        assert conflict_count(grid, "main") >= 1
        assert module.rule_mirror(grid, "main") != module.copy_blank_only_rival(grid, "main")
    for texture in module.DEGENERATE_TEXTURES:
        assert module.self_check(module.generate(0, 0, texture=texture)), texture


def test_default_program_is_exact_canonical_and_contract_is_bounded() -> None:
    adapter = load_parametric("adapter")
    contract_path = PARAMETRIC / "promotion.json"
    assert contract_path.is_file()
    contract = json.loads(contract_path.read_text())
    assert adapter.program({"axis_rule": "main"}) == canonical_program()
    assert contract["parameters"] == {"axis_rule": ["main", "anchor_selected"]}
    assert contract["default"] == {"axis_rule": "main"}
    assert contract["limits"] == {"demos": [2, 6], "queries": [1, 4]}
    assert contract["qualification_demos"] == 3


@pytest.mark.parametrize("seed", [0, 17, 43])
def test_matched_inputs_have_input_dependent_axis_and_30x30(seed: int) -> None:
    adapter = load_parametric("adapter")
    family = load_parametric("family")
    episodes = {
        mode: adapter.generate(seed, {"axis_rule": mode}, 6, 4)
        for mode in family.SETTINGS
    }
    inputs = {
        mode: [pair["input"] for pair in episode["train"] + episode["test"]]
        for mode, episode in episodes.items()
    }
    assert inputs["main"] == inputs["anchor_selected"]
    assert len({json.dumps(grid, separators=(",", ":")) for grid in inputs["main"]}) == 10
    selected = [family.intermediate(grid)["selected_axis"] for grid in inputs["main"]]
    assert {"main", "anti"} <= set(selected)
    assert all(family.intermediate(grid)["unique_corner_anchor"] for grid in inputs["main"])
    assert all(family.intermediate(grid)["main_conflicts"] >= 1 for grid in inputs["main"])
    assert all(family.intermediate(grid)["anti_conflicts"] >= 1 for grid in inputs["main"])
    stress = episodes["main"]["test"][-1]["input"]
    assert (len(stress), len(stress[0])) == (30, 30)
    assert sum(value != 0 for row in stress for value in row) >= 80
    assert episodes["main"]["private_query_bank"] == episodes["main"]["test"]


def test_every_supported_prefix_identifies_axis_rule_and_refutes_rivals() -> None:
    adapter = load_parametric("adapter")
    family = load_parametric("family")
    for seed in range(16):
        for demos in range(2, 7):
            for mode in family.SETTINGS:
                episode = adapter.generate(seed, {"axis_rule": mode}, demos, 4)
                opposite = adapter.generate(
                    seed,
                    {"axis_rule": "anchor_selected" if mode == "main" else "main"},
                    demos,
                    4,
                )
                assert [p["input"] for p in episode["train"]] == [p["input"] for p in opposite["train"]]
                assert any(a["output"] != b["output"] for a, b in zip(episode["train"], opposite["train"]))
                survivors = set(family.RIVALS)
                for pair in episode["train"]:
                    survivors = {
                        rival
                        for rival in survivors
                        if family.solve_rival(pair["input"], mode, rival) == pair["output"]
                    }
                assert not survivors, (seed, demos, mode, survivors)


def test_claimed_labels_match_solver_and_wrong_intermediate_changes() -> None:
    adapter = load_parametric("adapter")
    family = load_parametric("family")
    episode = adapter.generate(29, {"axis_rule": "anchor_selected"}, 3, 4)
    changed = 0
    for pair in episode["train"] + episode["test"]:
        assert family.solve(pair["input"], "anchor_selected") == pair["output"]
        info = family.intermediate(pair["input"])
        wrong = "anti" if info["selected_axis"] == "main" else "main"
        if family.solve_axis(pair["input"], wrong) != pair["output"]:
            changed += 1
    assert changed >= 1


@pytest.mark.parametrize(
    "settings",
    [None, {}, {"axis_rule": "x"}, {"axis_rule": True}, {"axis_rule": "main", "x": 1}],
)
def test_invalid_settings_are_rejected(settings: object) -> None:
    with pytest.raises(ValueError):
        load_parametric("adapter").program(settings)


@pytest.mark.parametrize(
    "field,bad",
    [
        ("seed", True),
        ("seed", -1),
        ("demos", 1),
        ("demos", 7),
        ("queries", 0),
        ("queries", 5),
        ("queries", 2.0),
    ],
)
def test_invalid_counts_are_rejected(field: str, bad: object) -> None:
    kwargs = {
        "seed": 0,
        "settings": {"axis_rule": "main"},
        "demos": 3,
        "queries": 4,
    }
    kwargs[field] = bad
    with pytest.raises(ValueError):
        load_parametric("adapter").generate(**kwargs)
