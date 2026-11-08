"""Native parametric frame family: local majority/minority rules and labels."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"


def load_prototype():
    path = PARAMETRIC / "prototype.py"
    assert path.is_file(), "parametric frame prototype is missing"
    spec = importlib.util.spec_from_file_location("_test_frame_parametric", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def prototype():
    return load_prototype()


def canonical_source():
    from arcpuzzles import Catalog

    catalog = Catalog(ROOT)
    row = catalog.describe("7ef325b21961")
    programs = {variant["program_solution"]
                for variant in catalog._variants()[row["rule_task_id"]]}
    assert len(programs) == 1
    return next(iter(programs))


def apply_racket(source, grid):
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    with RacketBridge() as bridge:
        identity = bridge.runtime_identity
        assert identity["backend"] == "racket"
        assert identity["protected"] is True
        return bridge.eval_text(f"({wrap_rule(source)} {literal})")


def test_default_program_is_exact_canonical_bytes(prototype):
    assert prototype.program({"fill_choice": "majority"}) == canonical_source()


def test_native_contract_names_both_executable_settings(prototype):
    contract = json.loads((PARAMETRIC / "promotion.json").read_text(encoding="utf-8"))
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/7ef325b21961/workspace/parametric/adapter.py",
        "parameters": {"fill_choice": ["majority", "minority"]},
        "default": {"fill_choice": "majority"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "qualification_demos": 2,
        "resources": [
            "generators/7ef325b21961/workspace/parametric/canonical.rkt",
            "generators/7ef325b21961/workspace/parametric/minority.rkt",
        ],
    }


@pytest.mark.parametrize("demos", [2, 3, 4, 5, 6])
def test_counts_matched_inputs_distinct_and_teaching(prototype, demos):
    settings = ({"fill_choice": "majority"}, {"fill_choice": "minority"})
    episodes = [prototype.generate(19, setting, demos, 4) for setting in settings]
    for episode, setting in zip(episodes, settings):
        assert episode["settings"] == setting
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
        assert len({json.dumps(grid, separators=(",", ":")) for grid in inputs}) == demos + 4
        assert [len(inputs[-1]), len(inputs[-1][0])] == [30, 30]
        certificate = prototype.check_teaching(episode["train"], setting)
        assert certificate["survivors"] == [setting["fill_choice"]]
        assert certificate["fit_scope"] == "demonstrations_only"
    for split in ("train", "test"):
        assert [pair["input"] for pair in episodes[0][split]] == [
            pair["input"] for pair in episodes[1][split]
        ]
    assert all(a["output"] != b["output"]
               for a, b in zip(episodes[0]["train"], episodes[1]["train"]))


def test_sampler_has_independent_local_statistics_and_safe_components(prototype):
    profiles = prototype.DEMO_PROFILES + prototype.QUERY_PROFILES
    for index, profile in enumerate(profiles):
        domain = "demo" if index < len(prototype.DEMO_PROFILES) else "query"
        local_index = index if domain == "demo" else index - len(prototype.DEMO_PROFILES)
        grid = prototype.sample_input(37, domain, local_index, profile)
        analysis = prototype.analyze(grid)
        assert len(analysis["frames"]) == profile[2]
        majorities = []
        minorities = []
        for frame in analysis["frames"]:
            ordered = frame["counts"].most_common()
            assert len(ordered) == 2
            assert ordered[0][1] > ordered[1][1] >= 1
            assert frame["majority"] == ordered[0][0]
            assert frame["minority"] == ordered[1][0]
            majorities.append(frame["majority"])
            minorities.append(frame["minority"])
        assert len(set(majorities)) == len(majorities)
        assert len(set(minorities)) == len(minorities)
        assert all(len(component["cells"]) == 1 for component in analysis["non_frames"])


@pytest.mark.parametrize("setting", ["majority", "minority"])
def test_racket_program_executes_claimed_labels(prototype, setting):
    episode = prototype.generate(5, {"fill_choice": setting}, 2, 4)
    source = prototype.program({"fill_choice": setting})
    for pair in episode["train"] + episode["test"]:
        assert apply_racket(source, pair["input"]) == pair["output"]


def test_selected_color_is_input_dependent_and_consumed_by_fill(prototype):
    grids = [prototype.sample_input(43, "query", index, profile)
             for index, profile in enumerate(prototype.QUERY_PROFILES)]
    selections = []
    for grid in grids:
        analysis = prototype.analyze(grid)
        selections.append(tuple(frame["majority"] for frame in analysis["frames"]))
        for choice in ("majority", "minority"):
            output = prototype.transform(grid, {"fill_choice": choice})
            for frame in analysis["frames"]:
                r1, c1, r2, c2 = frame["bbox"]
                selected = frame[choice]
                assert all(output[r][c] == selected
                           for r in range(r1 + 1, r2)
                           for c in range(c1 + 1, c2))
                assert all(output[r][c] == frame["frame_color"]
                           for r in range(r1, r2 + 1)
                           for c in range(c1, c2 + 1)
                           if r in (r1, r2) or c in (c1, c2))
    assert len(set(selections)) >= 3


def test_bounded_audit_rejects_declared_shortcuts(prototype):
    report = prototype.audit(seed=47, demos=3, queries=4)
    assert report["status"] == "passed"
    assert set(report["settings"]) == {"majority", "minority"}
    for row in report["settings"].values():
        assert row["survivors"] == [row["chosen"]]
        assert row["query_count"] == 4
        assert set(row["rivals"]) == {
            "global_statistic", "border_color", "fixed_color", "keep_dots", "skip_selection"
        }
        assert all(value["rejected"] for value in row["rivals"].values())


@pytest.mark.parametrize("field,value", [
    ("seed", -1), ("seed", True), ("demos", 1), ("demos", 7),
    ("demos", 3.0), ("queries", 0), ("queries", 5), ("queries", "4"),
])
def test_invalid_requests_fail(prototype, field, value):
    args = {"seed": 0, "settings": {"fill_choice": "majority"},
            "demos": 3, "queries": 4}
    args[field] = value
    with pytest.raises(ValueError):
        prototype.generate(**args)


@pytest.mark.parametrize("settings", [
    {}, {"fill_choice": "unknown"}, {"fill_choice": True},
    {"fill_choice": "majority", "extra": 1},
])
def test_invalid_settings_fail(prototype, settings):
    with pytest.raises(ValueError):
        prototype.program(settings)


def test_strict_grid_rejects_bool_ragged_and_bad_palette(prototype):
    grid = prototype.sample_input(0, "demo", 0, prototype.DEMO_PROFILES[0])
    for mutation in ("bool", "ragged", "palette"):
        bad = deepcopy(grid)
        if mutation == "bool":
            bad[0][0] = True
        elif mutation == "ragged":
            bad[0].pop()
        else:
            bad[0][0] = 10
        with pytest.raises(ValueError):
            prototype.strict_grid(bad)
