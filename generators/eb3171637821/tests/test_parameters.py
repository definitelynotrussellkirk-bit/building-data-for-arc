"""Native promotion checks for the divider-lattice encoding family."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, find_root


TASK_ID = "eb3171637821"
ROOT = find_root(__file__)
HOME = ROOT / f"generators/{TASK_ID}"
PARAMETRIC = HOME / "workspace/parametric"
PROTOTYPE_PATH = PARAMETRIC / "prototype.py"
ADAPTER_PATH = PARAMETRIC / "adapter.py"
PROMOTION_PATH = PARAMETRIC / "promotion.json"
ENCODINGS = ("solid_count", "area_parity")


def _load(name: str, path: Path):
    assert path.is_file(), f"missing required parametric source: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    programs = {
        row["program_solution"]
        for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines()
        if line.strip()
        if (row := json.loads(line)).get("task_id") == TASK_ID
    }
    assert len(programs) == 1
    return programs.pop()


def _execute(bridge: RacketBridge, program: str, grid: list[list[int]]) -> list[list[int]]:
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    return bridge.eval_text(f"({wrap_rule(program)} {literal})")


@pytest.fixture(scope="module")
def prototype():
    return _load("parametric_eb3171637821", PROTOTYPE_PATH)


@pytest.fixture(scope="module")
def adapter():
    return _load("parametric_adapter_eb3171637821", ADAPTER_PATH)


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge(timeout=30, max_calls_before_restart=64) as runtime:
        yield runtime


def test_contract_declares_bounded_encoding_family():
    assert PROMOTION_PATH.is_file(), "promotion contract must be created"
    contract = json.loads(PROMOTION_PATH.read_text(encoding="utf-8"))
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"encoding": list(ENCODINGS)},
        "default": {"encoding": "solid_count"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
    }


def test_default_program_is_exact_canonical_and_alternate_is_composed(prototype, adapter):
    canonical = _canonical_program()
    assert prototype.canonical_program() == canonical
    assert prototype.rule_text("solid_count") == canonical
    assert adapter.program({"encoding": "solid_count"}) == canonical
    alternate = prototype.rule_text("area_parity")
    assert alternate == adapter.program({"encoding": "area_parity"})
    assert alternate != canonical
    assert "row-band-sizes" in alternate
    assert "col-band-sizes" in alternate
    assert "(odd? (* (list-ref row-band-sizes r)" in alternate


def test_episode_inputs_are_deterministic_matched_and_distinct(prototype, adapter):
    episodes = {
        encoding: adapter.generate(17, {"encoding": encoding}, 3, 4)
        for encoding in ENCODINGS
    }
    assert episodes["solid_count"] == adapter.generate(
        17, {"encoding": "solid_count"}, 3, 4
    )
    left_inputs = [
        pair["input"]
        for split in ("train", "test")
        for pair in episodes[ENCODINGS[0]][split]
    ]
    right_inputs = [
        pair["input"]
        for split in ("train", "test")
        for pair in episodes[ENCODINGS[1]][split]
    ]
    assert left_inputs == right_inputs
    assert len({json.dumps(grid, separators=(",", ":")) for grid in left_inputs}) == 7
    assert all(
        a["output"] != b["output"]
        for split in ("train", "test")
        for a, b in zip(episodes[ENCODINGS[0]][split], episodes[ENCODINGS[1]][split])
    )
    for encoding, episode in episodes.items():
        assert episode["program_solution"] == prototype.rule_text(encoding)
        for split in ("train", "test"):
            for pair in episode[split]:
                assert pair["output"] == prototype.output_for(pair["input"], encoding)


def test_two_demonstrations_identify_each_encoding_against_declared_rival(prototype):
    selected = prototype.select_inputs(29, demos=2, queries=4)
    for chosen in ENCODINGS:
        labels = [prototype.output_for(row["input"], chosen) for row in selected["train"]]
        survivors = [
            candidate
            for candidate in ENCODINGS
            if all(
                prototype.output_for(row["input"], candidate) == label
                for row, label in zip(selected["train"], labels)
            )
        ]
        assert survivors == [chosen]
    assert all(
        prototype.output_for(row["input"], ENCODINGS[0])
        != prototype.output_for(row["input"], ENCODINGS[1])
        for row in selected["train"]
    )


@pytest.mark.parametrize("demos", [2, 3, 6])
@pytest.mark.parametrize("queries", [1, 4])
def test_supported_count_boundaries(prototype, demos, queries):
    episode = prototype.generate_episode(
        41, encoding="area_parity", demos=demos, queries=queries
    )
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == queries
    inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
    assert len({json.dumps(grid) for grid in inputs}) == demos + queries


@pytest.mark.parametrize(
    "kwargs",
    [
        {"seed": True},
        {"seed": -1},
        {"encoding": "area_mod_three"},
        {"encoding": 1},
        {"demos": True},
        {"demos": 1},
        {"demos": 7},
        {"queries": 0},
        {"queries": 5},
        {"queries": 1.0},
    ],
)
def test_episode_rejects_invalid_boundaries(prototype, kwargs):
    call = {"seed": 0, "encoding": "solid_count", "demos": 3, "queries": 4}
    call.update(kwargs)
    with pytest.raises((TypeError, ValueError)):
        prototype.generate_episode(**call)


@pytest.mark.parametrize(
    "settings",
    [{}, {"encoding": "solid_count", "extra": 1}, {"encoding": "area_mod_three"}, None],
)
def test_adapter_rejects_unknown_or_missing_setting_keys(adapter, settings):
    with pytest.raises(ValueError, match="exactly encoding|declared encoding"):
        adapter.program(settings)


def test_oracle_recovers_ordered_band_sizes_and_area_parity(prototype):
    selected = prototype.select_inputs(53, demos=2, queries=1)
    grid = selected["train"][0]["input"]
    info = prototype.analyze_input(grid)
    assert len(info["row_band_sizes"]) >= 2
    assert len(info["col_band_sizes"]) >= 2
    expected = [
        [
            info["cell_color"]
            if (row_size * col_size) % 2
            else info["divider_color"]
            for col_size in info["col_band_sizes"]
        ]
        for row_size in info["row_band_sizes"]
    ]
    assert prototype.output_for(grid, "area_parity") == expected
    assert prototype.output_for(grid, "solid_count") == [
        [info["cell_color"] for _ in info["col_band_sizes"]]
        for _ in info["row_band_sizes"]
    ]


def test_four_queries_include_substantive_exact_30x30_stress(prototype):
    selected = prototype.select_inputs(59, demos=3, queries=4)
    large = [
        row
        for row in selected["test"]
        if len(row["input"]) == 30 and len(row["input"][0]) == 30
    ]
    assert len(large) == 1
    grid = large[0]["input"]
    info = prototype.analyze_input(grid)
    assert len(info["row_band_sizes"]) >= 5
    assert len(info["col_band_sizes"]) >= 5
    assert len(set(info["row_band_sizes"])) >= 4
    assert len(set(info["col_band_sizes"])) >= 4
    assert sum(cell == info["divider_color"] for row in grid for cell in row) >= 300
    assert prototype.output_for(grid, ENCODINGS[0]) != prototype.output_for(
        grid, ENCODINGS[1]
    )


def test_racket_executes_labels_and_demos_leave_one_program(prototype, bridge):
    programs = {encoding: prototype.rule_text(encoding) for encoding in ENCODINGS}
    for chosen in ENCODINGS:
        episode = prototype.generate_episode(67, encoding=chosen, demos=2, queries=4)
        survivors = []
        for encoding, program in programs.items():
            if all(
                _execute(bridge, program, pair["input"]) == pair["output"]
                for pair in episode["train"]
            ):
                survivors.append(encoding)
        assert survivors == [chosen]
        for pair in episode["test"]:
            assert _execute(bridge, programs[chosen], pair["input"]) == pair["output"]


def test_query_outputs_are_not_needed_to_fit_demonstration_survivor(prototype):
    episode = prototype.generate_episode(
        71, encoding="solid_count", demos=2, queries=4
    )
    mutated = copy.deepcopy(episode)
    mutated["test"][0]["output"][0][0] = (
        mutated["test"][0]["output"][0][0] + 1
    ) % 10
    survivors = [
        encoding
        for encoding in ENCODINGS
        if all(
            prototype.output_for(pair["input"], encoding) == pair["output"]
            for pair in episode["train"]
        )
    ]
    assert survivors == ["solid_count"]
    assert mutated["train"] == episode["train"]


def test_review_tool_reports_bounded_deterministic_census():
    tool_path = PARAMETRIC / "tools/review_family.py"
    tool = _load("review_family_eb3171637821", tool_path)
    report = tool.review_family(seeds=[0, 1], racket_seeds=[])
    assert report["schema"] == "arcpuzzles-parametric-family-review-v1"
    assert report["status"] == "pass"
    assert report["scope"] == {
        "seeds": [0, 1],
        "racket_seeds": [],
        "demo_counts": [2, 3, 6],
        "query_counts": [1, 4],
        "finite_limit": "Findings apply only to the enumerated seeds, counts, settings, and rivals.",
    }
    assert report["counts"]["episodes"] == 24
    assert report["counts"]["examples"] > 0
    assert report["counts"]["matched_setting_comparisons"] > 0
    assert report["counts"]["stress_30x30"] > 0
    assert report["failures"] == []
