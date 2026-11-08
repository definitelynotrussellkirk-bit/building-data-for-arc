"""Native parametric regressions for the central-axis reflection family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest
from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root

TASK = "70a3d3e2c975"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK / "workspace" / "parametric"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def prototype():
    return load("_test_70a_parametric_prototype", HOME / "prototype.py")


@pytest.fixture(scope="module")
def adapter():
    return load("_test_70a_parametric_adapter", HOME / "adapter.py")


def frozen(grid):
    return json.dumps(grid, separators=(",", ":"))


def canonical_program() -> str:
    record = Catalog(ROOT).get(TASK)
    programs = {
        variant["program_solution"]
        for variant in record["variants"]
        if isinstance(variant.get("program_solution"), str)
    }
    assert len(programs) == 1
    return programs.pop()


def test_promotion_contract_declares_bounded_native_family():
    contract = json.loads((HOME / "promotion.json").read_text())
    assert contract["schema"] == "arcpuzzles-parametric-adapter-v1"
    assert contract["adapter"] == f"generators/{TASK}/workspace/parametric/adapter.py"
    assert contract["parameters"] == {"copy_policy": ["all_colors", "rarest_color"]}
    assert contract["default"] == {"copy_policy": "all_colors"}
    assert contract["limits"] == {"demos": [2, 6], "queries": [1, 4]}
    assert contract["qualification_demos"] == 3


def test_default_program_is_exact_canonical_bytes(adapter):
    assert adapter.program({"copy_policy": "all_colors"}) == canonical_program()
    assert (HOME / "canonical.rkt").read_text() == canonical_program()
    assert adapter.program({"copy_policy": "rarest_color"}) != canonical_program()


@pytest.mark.parametrize("policy", ["all_colors", "rarest_color"])
@pytest.mark.parametrize("demos", range(2, 7))
@pytest.mark.parametrize("queries", range(1, 5))
def test_supported_counts_generate_distinct_valid_pairs(adapter, prototype, policy, demos, queries):
    episode = adapter.generate(17, {"copy_policy": policy}, demos, queries)
    assert episode["program_solution"] == adapter.program({"copy_policy": policy})
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == queries
    pairs = episode["train"] + episode["test"]
    assert len({frozen(pair["input"]) for pair in pairs}) == len(pairs)
    for pair in pairs:
        assert prototype.validate_input(pair["input"]) == pair["input"]
        assert pair["output"] == prototype.transform(pair["input"], policy)
    assert prototype.setting_survivors(episode["train"]) == [policy]


def test_inputs_are_setting_neutral_and_count_prefix_stable(adapter):
    all_short = adapter.generate(91, {"copy_policy": "all_colors"}, 2, 1)
    all_long = adapter.generate(91, {"copy_policy": "all_colors"}, 6, 4)
    rare_long = adapter.generate(91, {"copy_policy": "rarest_color"}, 6, 4)
    assert [p["input"] for p in all_short["train"]] == [p["input"] for p in all_long["train"][:2]]
    assert all_short["test"][0]["input"] == all_long["test"][0]["input"]
    assert [p["input"] for p in all_long["train"] + all_long["test"]] == [
        p["input"] for p in rare_long["train"] + rare_long["test"]
    ]


def test_two_demo_lesson_rejects_declared_shortcuts(adapter, prototype):
    for seed in (0, 17, 91):
        for policy in prototype.POLICIES:
            episode = adapter.generate(seed, {"copy_policy": policy}, 2, 4)
            assert prototype.setting_survivors(episode["train"]) == [policy]
            assert prototype.rival_survivors(episode["train"], selected_policy=policy) == []
            assert all(
                prototype.transform(pair["input"], "all_colors")
                != prototype.transform(pair["input"], "rarest_color")
                for pair in episode["test"]
            )


def test_four_queries_cover_scale_boundaries_and_substantive_near_30_square(adapter):
    episode = adapter.generate(5, {"copy_policy": "rarest_color"}, 3, 4)
    shapes = [(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]]
    assert shapes == [(14, 15), (18, 19), (24, 25), (30, 29)]
    largest = episode["test"][-1]["input"]
    axis = len(largest[0]) // 2
    source_cells = sum(cell not in (0, 9) for row in largest for cell in row[:axis])
    assert source_cells >= 100
    assert any(row[0] not in (0, 9) for row in largest)
    assert any(row[axis - 1] not in (0, 9) for row in largest)


def test_default_python_transform_matches_every_canonical_label(prototype):
    pairs = canonical_pairs(TASK, root=ROOT)
    assert len(pairs) == 3
    for pair in pairs:
        assert prototype.transform(pair["input"], "all_colors") == pair["output"]


def test_dependency_explanation_is_input_derived(adapter, prototype):
    episode = adapter.generate(17, {"copy_policy": "rarest_color"}, 3, 4)
    info = prototype.dependency(episode["test"][-1]["input"], "rarest_color")
    assert info["step_a"]
    assert info["step_b"]
    assert info["eligible_colors"] == [info["rarest_color"]]
    assert sum(info["source_counts"].values()) >= 100
    assert info["final"] == episode["test"][-1]["output"]


@pytest.mark.parametrize(
    "settings",
    [None, {}, {"copy_policy": "unknown"}, {"copy_policy": 1}, {"copy_policy": True},
     {"copy_policy": "all_colors", "extra": 1}],
)
def test_settings_reject_malformed_values(adapter, settings):
    with pytest.raises((TypeError, ValueError)):
        adapter.program(settings)


@pytest.mark.parametrize(
    "args",
    [
        (True, {"copy_policy": "all_colors"}, 2, 1),
        (-1, {"copy_policy": "all_colors"}, 2, 1),
        (0, {"copy_policy": "all_colors"}, 1, 1),
        (0, {"copy_policy": "all_colors"}, 7, 1),
        (0, {"copy_policy": "all_colors"}, 2, 0),
        (0, {"copy_policy": "all_colors"}, 2, 5),
    ],
)
def test_generate_rejects_out_of_contract_requests(adapter, args):
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(*args)


def test_audit_tool_exposes_reusable_entrypoint():
    audit = load("_test_70a_parametric_audit", HOME / "audit.py")
    assert callable(audit.run_audit)
    assert callable(audit.main)
