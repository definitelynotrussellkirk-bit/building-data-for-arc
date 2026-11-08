"""Native parametric regressions for independent/cumulative corner commands."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest
from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root

TASK = "d01b33f4a589"
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
    return load("_test_d01_parametric_prototype", HOME / "prototype.py")


@pytest.fixture(scope="module")
def adapter():
    return load("_test_d01_parametric_adapter", HOME / "adapter.py")


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
    assert contract["parameters"] == {
        "application_policy": ["independent", "cumulative"]
    }
    assert contract["default"] == {"application_policy": "independent"}
    assert contract["limits"] == {"demos": [2, 6], "queries": [1, 4]}
    assert contract["qualification_demos"] == 3


def test_default_program_is_exact_canonical_bytes(adapter):
    expected = canonical_program()
    assert adapter.program({"application_policy": "independent"}) == expected
    assert (HOME / "canonical.rkt").read_text() == expected
    assert adapter.program({"application_policy": "cumulative"}) != expected


@pytest.mark.parametrize("policy", ["independent", "cumulative"])
@pytest.mark.parametrize("demos", range(2, 7))
@pytest.mark.parametrize("queries", range(1, 5))
def test_supported_counts_generate_distinct_valid_pairs(adapter, prototype, policy, demos, queries):
    episode = adapter.generate(17, {"application_policy": policy}, demos, queries)
    assert episode["program_solution"] == adapter.program({"application_policy": policy})
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == queries
    pairs = episode["train"] + episode["test"]
    assert len({frozen(pair["input"]) for pair in pairs}) == len(pairs)
    for pair in pairs:
        prototype.validate_input(pair["input"])
        assert pair["output"] == prototype.transform(pair["input"], policy)
        assert 1 <= len(pair["output"]) <= 30
        assert 1 <= len(pair["output"][0]) <= 30
        assert all(len(row) == len(pair["output"][0]) for row in pair["output"])
        assert all(type(cell) is int and 0 <= cell <= 9 for row in pair["output"] for cell in row)
    assert prototype.setting_survivors(episode["train"]) == [policy]


def test_inputs_are_setting_neutral_and_count_prefix_stable(adapter):
    short = adapter.generate(91, {"application_policy": "independent"}, 2, 1)
    long = adapter.generate(91, {"application_policy": "independent"}, 6, 4)
    alternate = adapter.generate(91, {"application_policy": "cumulative"}, 6, 4)
    assert [p["input"] for p in short["train"]] == [p["input"] for p in long["train"][:2]]
    assert short["test"][0]["input"] == long["test"][0]["input"]
    assert [p["input"] for p in long["train"] + long["test"]] == [
        p["input"] for p in alternate["train"] + alternate["test"]
    ]


def test_two_demo_lesson_rejects_declared_shortcuts(adapter, prototype):
    for seed in (0, 17, 91):
        for policy in prototype.POLICIES:
            episode = adapter.generate(seed, {"application_policy": policy}, 2, 4)
            assert prototype.setting_survivors(episode["train"]) == [policy]
            assert prototype.rival_survivors(episode["train"], selected_policy=policy) == []
            assert all(
                prototype.transform(pair["input"], "independent")
                != prototype.transform(pair["input"], "cumulative")
                for pair in episode["test"]
            )


def test_four_queries_cover_scale_boundaries_and_substantive_30_square(adapter, prototype):
    episode = adapter.generate(5, {"application_policy": "cumulative"}, 3, 4)
    shapes = [(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]]
    assert shapes == [(14, 16), (18, 21), (24, 27), (30, 30)]
    facts = prototype.analyze_input(episode["test"][-1]["input"])
    assert facts["motif_size"] >= 120
    assert facts["bbox_height"] == 14
    assert facts["bbox_width"] == 15
    assert len({frozen(v) for v in facts["independent_variants"]}) >= 4
    assert all(
        len(pair["output"]) <= 30 and len(pair["output"][0]) <= 30
        for pair in episode["test"]
    )


def test_default_python_transform_matches_every_canonical_label(prototype):
    pairs = canonical_pairs(TASK, root=ROOT)
    assert len(pairs) == 5
    for pair in pairs:
        assert prototype.transform(pair["input"], "independent") == pair["output"]


def test_dependency_explanation_is_input_derived(adapter, prototype):
    episode = adapter.generate(17, {"application_policy": "cumulative"}, 3, 4)
    info = prototype.dependency(episode["test"][-1]["input"], "cumulative")
    assert info["step_a"]
    assert info["step_b"]
    assert info["codes"] == [4, 2, 3, 1]
    assert len(info["variant_sha256"]) == 4
    assert info["variant_sha256"] != info["independent_variant_sha256"]
    assert info["final"] == episode["test"][-1]["output"]


@pytest.mark.parametrize(
    "settings",
    [None, {}, {"application_policy": "unknown"}, {"application_policy": 1},
     {"application_policy": True}, {"application_policy": "independent", "extra": 1}],
)
def test_settings_reject_malformed_values(adapter, settings):
    with pytest.raises((TypeError, ValueError)):
        adapter.program(settings)


@pytest.mark.parametrize(
    "args",
    [
        (True, {"application_policy": "independent"}, 2, 1),
        (-1, {"application_policy": "independent"}, 2, 1),
        (0, {"application_policy": "independent"}, 1, 1),
        (0, {"application_policy": "independent"}, 7, 1),
        (0, {"application_policy": "independent"}, 2, 0),
        (0, {"application_policy": "independent"}, 2, 5),
    ],
)
def test_generate_rejects_out_of_contract_requests(adapter, args):
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(*args)


def test_audit_tool_exposes_reusable_entrypoint():
    audit = load("_test_d01_parametric_audit", HOME / "audit.py")
    assert callable(audit.run_audit)
    assert callable(audit.main)
