"""Native parametric regressions for frame-selection metrics."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest
from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root

TASK = "75be7448827f"
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
    return load("_test_75_parametric_prototype", HOME / "prototype.py")


@pytest.fixture(scope="module")
def adapter():
    return load("_test_75_parametric_adapter", HOME / "adapter.py")


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


def test_promotion_contract_declares_metric_family():
    contract = json.loads((HOME / "promotion.json").read_text())
    assert contract["schema"] == "arcpuzzles-parametric-adapter-v1"
    assert contract["adapter"] == f"generators/{TASK}/workspace/parametric/adapter.py"
    assert contract["parameters"] == {"selection_metric": ["raw_count", "occupied_density"]}
    assert contract["default"] == {"selection_metric": "raw_count"}
    assert contract["limits"] == {"demos": [2, 6], "queries": [1, 4]}
    assert contract["qualification_demos"] == 3


def test_default_program_is_exact_canonical_bytes(adapter):
    assert adapter.program({"selection_metric": "raw_count"}) == canonical_program()
    assert (HOME / "canonical.rkt").read_text() == canonical_program()
    assert adapter.program({"selection_metric": "occupied_density"}) != canonical_program()


@pytest.mark.parametrize("metric", ["raw_count", "occupied_density"])
@pytest.mark.parametrize("demos", range(2, 7))
@pytest.mark.parametrize("queries", range(1, 5))
def test_supported_counts_generate_valid_distinct_pairs(adapter, prototype, metric, demos, queries):
    episode = adapter.generate(17, {"selection_metric": metric}, demos, queries)
    assert episode["program_solution"] == adapter.program({"selection_metric": metric})
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == queries
    pairs = episode["train"] + episode["test"]
    assert len({frozen(pair["input"]) for pair in pairs}) == len(pairs)
    for pair in pairs:
        frames = prototype.parse_frames(pair["input"])
        assert 2 <= len(frames) <= 3
        assert pair["output"] == prototype.transform(pair["input"], metric)
        assert prototype.transform(pair["input"], "raw_count") != prototype.transform(
            pair["input"], "occupied_density"
        )
    assert prototype.setting_survivors(episode["train"]) == [metric]


def test_inputs_are_setting_neutral_and_count_prefix_stable(adapter):
    short = adapter.generate(91, {"selection_metric": "raw_count"}, 2, 1)
    long = adapter.generate(91, {"selection_metric": "raw_count"}, 6, 4)
    density = adapter.generate(91, {"selection_metric": "occupied_density"}, 6, 4)
    assert [p["input"] for p in short["train"]] == [p["input"] for p in long["train"][:2]]
    assert short["test"][0]["input"] == long["test"][0]["input"]
    assert [p["input"] for p in long["train"] + long["test"]] == [
        p["input"] for p in density["train"] + density["test"]
    ]


def test_two_demo_lesson_rejects_declared_shortcuts(adapter, prototype):
    for seed in (0, 17, 91):
        for metric in prototype.METRICS:
            episode = adapter.generate(seed, {"selection_metric": metric}, 2, 4)
            assert prototype.setting_survivors(episode["train"]) == [metric]
            assert prototype.rival_survivors(episode["train"], selected_metric=metric) == []
            assert all(
                prototype.transform(pair["input"], "raw_count")
                != prototype.transform(pair["input"], "occupied_density")
                for pair in episode["test"]
            )


def test_four_queries_cover_scale_boundaries_and_substantive_30_square(adapter, prototype):
    episode = adapter.generate(5, {"selection_metric": "occupied_density"}, 3, 4)
    shapes = [(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]]
    assert shapes == [(14, 16), (18, 20), (24, 26), (30, 30)]
    largest = episode["test"][-1]["input"]
    assert sum(cell != 0 for row in largest for cell in row) >= 170
    frames = prototype.parse_frames(largest)
    assert sorted(frame["area"] for frame in frames) == [25, 49, 80]
    assert sorted(frame["count"] for frame in frames) == [10, 35, 45]


def test_default_python_transform_matches_every_canonical_label(prototype):
    pairs = canonical_pairs(TASK, root=ROOT)
    assert len(pairs) == 5
    for pair in pairs:
        assert prototype.transform(pair["input"], "raw_count") == pair["output"]


def test_density_comparison_uses_ratio_not_smallest_frame(adapter, prototype):
    episode = adapter.generate(0, {"selection_metric": "occupied_density"}, 2, 1)
    second = prototype.parse_frames(episode["train"][1]["input"])
    density_winner = prototype.select_frame(second, "occupied_density")
    smallest = min(second, key=lambda frame: frame["area"])
    assert density_winner["bbox"] != smallest["bbox"]


def test_dependency_explanation_carries_selected_box_to_crop(adapter, prototype):
    episode = adapter.generate(17, {"selection_metric": "raw_count"}, 3, 4)
    info = prototype.dependency(episode["test"][-1]["input"], "raw_count")
    assert info["step_a"]
    assert info["step_b"]
    assert info["selected_bbox"] == [1, 1, 12, 10]
    assert info["selected_count"] == 45
    assert info["selected_area"] == 80
    assert info["final"] == episode["test"][-1]["output"]


@pytest.mark.parametrize(
    "settings",
    [None, {}, {"selection_metric": "unknown"}, {"selection_metric": 1},
     {"selection_metric": True}, {"selection_metric": "raw_count", "extra": 1}],
)
def test_settings_reject_malformed_values(adapter, settings):
    with pytest.raises((TypeError, ValueError)):
        adapter.program(settings)


@pytest.mark.parametrize(
    "args",
    [
        (True, {"selection_metric": "raw_count"}, 2, 1),
        (-1, {"selection_metric": "raw_count"}, 2, 1),
        (0, {"selection_metric": "raw_count"}, 1, 1),
        (0, {"selection_metric": "raw_count"}, 7, 1),
        (0, {"selection_metric": "raw_count"}, 2, 0),
        (0, {"selection_metric": "raw_count"}, 2, 5),
    ],
)
def test_generate_rejects_out_of_contract_requests(adapter, args):
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(*args)


def test_audit_tool_exposes_reusable_entrypoint():
    audit = load("_test_75_parametric_audit", HOME / "audit.py")
    assert callable(audit.run_audit)
    assert callable(audit.main)
