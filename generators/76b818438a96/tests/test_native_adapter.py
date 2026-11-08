"""Focused native-adapter contract checks for the recolor-origin family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import types

import pytest


HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"


@pytest.fixture(scope="module")
def adapter():
    spec = importlib.util.spec_from_file_location(
        "_test_76b818438a96_native_adapter", PARAMETRIC / "adapter.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_exact_path_import_ignores_foreign_cached_prototype(monkeypatch):
    foreign = types.ModuleType("prototype")
    foreign.__file__ = "/foreign/task/prototype.py"
    foreign.load_programs = lambda: pytest.fail("foreign prototype supplied programs")
    monkeypatch.setitem(sys.modules, "prototype", foreign)
    monkeypatch.setitem(
        sys.modules, "_arcpuzzles_76b818438a96_recolor_origin_prototype", foreign
    )
    spec = importlib.util.spec_from_file_location(
        "_test_76b818438a96_adapter_cache_isolation", PARAMETRIC / "adapter.py"
    )
    fresh = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fresh)
    assert Path(fresh._prototype.__file__).resolve() == (PARAMETRIC / "prototype.py").resolve()
    assert fresh.program({"recolor_origin": "opposite"}) == (
        PARAMETRIC / "rule_opposite.rkt"
    ).read_text().rstrip("\n")


def test_default_program_is_exact_selected_canonical(adapter):
    root = HOME.parents[1]
    from arcpuzzles import Catalog

    catalog = Catalog(root)
    row = catalog.describe(HOME.name)
    authority = row.get("rule_task_id", HOME.name)
    programs = {item["program_solution"] for item in catalog._variants()[authority]}
    canonical = adapter.program({"recolor_origin": "opposite"})
    assert programs == {canonical}
    assert adapter.program({"recolor_origin": "aligned"}) == canonical.replace(
        "(curr other-ep)", "(curr ep)", 1
    )


@pytest.mark.parametrize("settings", [
    None, [], "opposite", {}, {"recolor_origin": "opposite", "extra": 1},
    {"recolor_origin": None}, {"recolor_origin": True},
    {"recolor_origin": 1}, {"recolor_origin": "unknown"},
])
def test_rejects_invalid_settings_before_building(adapter, monkeypatch, settings):
    def forbidden(**kwargs):
        pytest.fail("invalid request reached prototype generation")

    monkeypatch.setattr(adapter._prototype, "build_episode", forbidden)
    with pytest.raises((TypeError, ValueError)):
        adapter.program(settings)
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(1, settings, 3, 4)


@pytest.mark.parametrize("seed,demos,queries", [
    (True, 3, 4), (-1, 3, 4), (2**63, 3, 4), (1.0, 3, 4),
    (1, True, 4), (1, 1, 4), (1, 7, 4), (1, 3.0, 4),
    (1, 3, False), (1, 3, 0), (1, 3, 5), (1, 3, 1.0),
])
def test_rejects_invalid_counts_and_seed_before_building(
    adapter, monkeypatch, seed, demos, queries
):
    def forbidden(**kwargs):
        pytest.fail("invalid request reached prototype generation")

    monkeypatch.setattr(adapter._prototype, "build_episode", forbidden)
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(seed, {"recolor_origin": "opposite"}, demos, queries)


@pytest.mark.parametrize("demos,queries", [(2, 4), (3, 1), (6, 4)])
def test_forwards_independent_counts_and_projects_private_pairs(
    adapter, monkeypatch, demos, queries
):
    pairs = [
        {"input": [[index % 10]], "selected_output": [[(index + 1) % 10]],
         "private_extra": "not an ordinary pair"}
        for index in range(demos + queries)
    ]
    received = []

    def build_episode(**kwargs):
        received.append(kwargs)
        return {"train": pairs[:demos], "test": pairs[demos:]}

    monkeypatch.setattr(adapter._prototype, "build_episode", build_episode)
    generated = adapter.generate(19, {"recolor_origin": "aligned"}, demos, queries)
    assert received == [{"seed": 19, "parameter": "aligned", "n_train": demos,
                         "n_test": queries}]
    assert set(generated) == {"train", "test", "program_solution"}
    assert generated["program_solution"] == adapter.program({"recolor_origin": "aligned"})
    for source, actual in zip(pairs, generated["train"] + generated["test"]):
        assert actual == {"input": source["input"], "output": source["selected_output"]}
    generated["train"][0]["input"][0][0] = 9
    assert pairs[0]["input"] == [[0]]


def test_promotion_contract_matches_supported_api():
    contract = json.loads((PARAMETRIC / "promotion.json").read_text())
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/76b818438a96/workspace/parametric/adapter.py",
        "parameters": {"recolor_origin": ["opposite", "aligned"]},
        "default": {"recolor_origin": "opposite"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
    }


@pytest.mark.parametrize("parameter", ["opposite", "aligned"])
def test_native_episode_has_three_demonstrations_and_four_novel_queries(adapter, parameter):
    episode = adapter.generate(381, {"recolor_origin": parameter}, 3, 4)
    assert len(episode["train"]) == 3
    assert len(episode["test"]) == 4
    pairs = episode["train"] + episode["test"]
    assert len({json.dumps(pair["input"]) for pair in pairs}) == 7
    assert episode["program_solution"] == adapter.program({"recolor_origin": parameter})
    for pair in pairs:
        assert set(pair) == {"input", "output"}
        assert len(pair["input"]) == len(pair["output"])
        assert len(pair["input"][0]) == len(pair["output"][0])
        assert pair["input"] != pair["output"]


@pytest.fixture(scope="module")
def boundary_episodes(adapter):
    """One seed, eight requests; share real executed labels between checks."""
    return {
        (parameter, demos, queries): adapter.generate(
            381, {"recolor_origin": parameter}, demos, queries
        )
        for parameter in ("opposite", "aligned")
        for demos in (2, 6)
        for queries in (1, 4)
    }


@pytest.mark.parametrize("parameter", ["opposite", "aligned"])
@pytest.mark.parametrize("demos", [2, 6])
@pytest.mark.parametrize("queries", [1, 4])
def test_boundary_requests_preserve_counts_and_novel_inputs(
    adapter, boundary_episodes, parameter, demos, queries
):
    episode = boundary_episodes[parameter, demos, queries]
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == queries
    assert episode["program_solution"] == adapter.program({"recolor_origin": parameter})
    pairs = episode["train"] + episode["test"]
    assert len({json.dumps(pair["input"]) for pair in pairs}) == demos + queries
    assert all(set(pair) == {"input", "output"} for pair in pairs)


@pytest.mark.parametrize("parameter", ["opposite", "aligned"])
def test_demo_and_query_requests_use_independent_stable_streams(boundary_episodes, parameter):
    for demos in (2, 6):
        short = boundary_episodes[parameter, demos, 1]
        long = boundary_episodes[parameter, demos, 4]
        assert short["train"] == long["train"]
        assert short["test"] == long["test"][:1]
    for queries in (1, 4):
        short = boundary_episodes[parameter, 2, queries]
        long = boundary_episodes[parameter, 6, queries]
        assert short["train"] == long["train"][:2]
        assert short["test"] == long["test"]


def test_boundary_settings_share_inputs_and_have_different_teaching_labels(boundary_episodes):
    for demos in (2, 6):
        for queries in (1, 4):
            canonical = boundary_episodes["opposite", demos, queries]
            variant = boundary_episodes["aligned", demos, queries]
            for split in ("train", "test"):
                assert [pair["input"] for pair in canonical[split]] == [
                    pair["input"] for pair in variant[split]
                ]
            assert any(
                left["output"] != right["output"]
                for left, right in zip(canonical["train"], variant["train"])
            )
