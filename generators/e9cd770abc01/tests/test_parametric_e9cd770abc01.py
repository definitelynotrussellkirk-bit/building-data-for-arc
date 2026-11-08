"""Behavioral tests for the center-nearest size-class parametric family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import types

import pytest

try:
    from reviewer_support import canonical_path, find_root
except ModuleNotFoundError:
    for parent in Path(__file__).resolve().parents:
        runtime = parent / "shared/runtime"
        if (runtime / "reviewer_support.py").is_file():
            sys.path.insert(0, str(runtime))
            break
    from reviewer_support import canonical_path, find_root

HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"
PROTOTYPE = PARAMETRIC / "prototype.py"
PROBE = PARAMETRIC / "probe.py"


def load_prototype():
    assert PROTOTYPE.is_file(), "runnable parametric prototype is missing"
    spec = importlib.util.spec_from_file_location("_e9cd_parametric_test_subject", PROTOTYPE)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_probe():
    assert PROBE.is_file(), "bounded self-review probe is missing"
    spec = importlib.util.spec_from_file_location("_e9cd_parametric_probe_test_subject", PROBE)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def p():
    return load_prototype()


def test_default_program_is_exact_catalog_authority(p):
    catalog = canonical_path(find_root(__file__))
    records = [json.loads(line) for line in catalog.read_text().splitlines() if line.strip()]
    sources = {
        record["program_solution"]
        for record in records
        if record["task_id"] == "e9cd770abc01"
    }
    assert sources == {p.program({"paint_scope": "nearest_only"})}


def test_nearest_size_class_consumes_selected_object_size(p):
    grid = [[0] * 9 for _ in range(9)]
    # Remote equal-size companion.
    for r, c in [(0, 0), (0, 1), (1, 0)]:
        grid[r][c] = 3
    # Unique center-nearest object, also size three.
    for r, c in [(4, 4), (4, 5), (5, 4)]:
        grid[r][c] = 3
    # Different-size distractor object.
    for r, c in [(7, 7), (7, 8), (8, 7), (8, 8)]:
        grid[r][c] = 3

    nearest = p.apply_python(grid, {"paint_scope": "nearest_only"})
    size_class = p.apply_python(grid, {"paint_scope": "nearest_size_class"})

    assert nearest[4][4] == nearest[4][5] == nearest[5][4] == 7
    assert nearest[0][0] == nearest[0][1] == nearest[1][0] == 3
    assert size_class[4][4] == size_class[0][0] == 7
    assert size_class[7][7] == 3


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_counts_unique_inputs_and_demo_only_identification(p, demos):
    for scope in ("nearest_only", "nearest_size_class"):
        episode = p.generate(17, {"paint_scope": scope}, demos, 4)
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
        assert len({json.dumps(grid) for grid in inputs}) == demos + 4
        report = p.teaching_report(episode["train"], {"paint_scope": scope})
        assert report["setting_survivors"] == [scope]
        assert report["plausible_rival_survivors"] == []
        assert report["fit_scope"] == "demonstrations_only"


def test_teaching_scene_separates_manhattan_from_euclidean_and_scope(p):
    for scope in ("nearest_only", "nearest_size_class"):
        episode = p.generate(0, {"paint_scope": scope}, 2, 1)
        first = episode["train"][0]
        assert p.apply_rival(first["input"], "euclidean_nearest", scope) != first["output"]
        other = "nearest_size_class" if scope == "nearest_only" else "nearest_only"
        assert p.apply_python(first["input"], {"paint_scope": other}) != first["output"]


@pytest.mark.parametrize("seed", [0, 9, 17, 23])
@pytest.mark.parametrize("scope", ["nearest_only", "nearest_size_class"])
def test_two_constructive_demos_reject_every_declared_rival(p, seed, scope):
    train = [
        {"input": grid, "output": p.apply_python(grid, {"paint_scope": scope})}
        for grid in p._all_train_inputs(seed)[:2]
    ]
    report = p.teaching_report(train, {"paint_scope": scope})
    assert report["setting_survivors"] == [scope]
    assert report["plausible_rival_survivors"] == []


def test_extended_rival_bank_rejects_centroid_shape_and_bbox_shortcuts(p):
    expected_rivals = {
        "centroid_euclidean",
        "smallest_green",
        "last_green",
        "selected_shape_class",
        "bbox_dimensions_class",
        "at_least_selected_size",
        "at_most_selected_size",
    }
    assert expected_rivals <= set(p.RIVALS)
    for scope in ("nearest_only", "nearest_size_class"):
        train = [
            {"input": grid, "output": p.apply_python(grid, {"paint_scope": scope})}
            for grid in p._all_train_inputs(0)[:2]
        ]
        report = p.teaching_report(train, {"paint_scope": scope})
        assert expected_rivals.isdisjoint(report["plausible_rival_survivors"])


@pytest.mark.parametrize("seed", [0, 1, 2, 9, 17, 23, 100])
@pytest.mark.parametrize("scope", ["nearest_only", "nearest_size_class"])
def test_demo_equivalent_shadow_selectors_do_not_change_queries(p, seed, scope):
    settings = {"paint_scope": scope}
    train_inputs = p._all_train_inputs(seed)[:2]
    query_inputs = p._all_query_inputs(seed)
    expected_train = [p.apply_python(grid, settings) for grid in train_inputs]
    expected_queries = [p.apply_python(grid, settings) for grid in query_inputs]

    for selector in p.SHADOW_SELECTORS:
        shadow_train = [p.apply_rival(grid, selector, scope) for grid in train_inputs]
        if shadow_train == expected_train:
            shadow_queries = [p.apply_rival(grid, selector, scope) for grid in query_inputs]
            assert shadow_queries == expected_queries, (seed, scope, selector)


def test_setting_independent_inputs_query_prefix_and_large_content(p):
    a = p.generate(23, {"paint_scope": "nearest_only"}, 3, 4)
    b = p.generate(23, {"paint_scope": "nearest_size_class"}, 3, 4)
    one = p.generate(23, {"paint_scope": "nearest_only"}, 3, 1)
    for split in ("train", "test"):
        assert [x["input"] for x in a[split]] == [x["input"] for x in b[split]]
    assert one["train"] == a["train"]
    assert one["test"][0] == a["test"][0]
    large = a["test"][3]["input"]
    assert len(large) == 30 and len(large[0]) == 30
    # Every quadrant carries real content; this catches empty-padding stress cases.
    for r0 in (0, 15):
        for c0 in (0, 15):
            assert sum(v != 0 for row in large[r0:r0 + 15] for v in row[c0:c0 + 15]) >= 6


@pytest.mark.parametrize(
    "patch",
    [
        {"seed": True},
        {"seed": -1},
        {"demos": 1},
        {"demos": 7},
        {"demos": 2.0},
        {"queries": 0},
        {"queries": 5},
        {"queries": True},
        {"settings": {}},
        {"settings": {"paint_scope": "wrong"}},
        {"settings": {"paint_scope": "nearest_only", "extra": 1}},
    ],
)
def test_invalid_requests_are_rejected(p, patch):
    args = {
        "seed": 0,
        "settings": {"paint_scope": "nearest_only"},
        "demos": 2,
        "queries": 4,
    }
    args.update(patch)
    with pytest.raises(ValueError):
        p.generate(**args)


def test_adapter_loads_adjacent_implementation_not_cached_module(p):
    previous = sys.modules.get("prototype")
    sys.modules["prototype"] = types.ModuleType("prototype")
    try:
        spec = importlib.util.spec_from_file_location(
            "_e9cd_native_adapter_test", PARAMETRIC / "adapter.py"
        )
        adapter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(adapter)
        settings = {"paint_scope": "nearest_size_class"}
        assert adapter.program(settings) == p.program(settings)
        assert adapter.generate(9, settings, 2, 4) == p.generate(9, settings, 2, 4)
    finally:
        if previous is None:
            sys.modules.pop("prototype", None)
        else:
            sys.modules["prototype"] = previous


def test_bounded_probe_covers_every_setting_count_and_large_query(p):
    probe = load_probe()
    report = probe.build_study(p, seeds=[0, 17])
    assert report["schema"] == "e9cd770abc01-parametric-self-review-v1"
    assert report["jobs"] == 20
    assert report["successes"] == 20
    assert report["failures"] == []
    assert report["settings"] == ["nearest_only", "nearest_size_class"]
    assert report["demo_counts"] == [2, 3, 4, 5, 6]
    assert report["matched_inputs_across_settings"] is True
    assert report["query_prefix_stable"] is True
    assert report["max_query_shape"] == [30, 30]
    assert report["all_declared_rivals_rejected"] is True
    assert probe.DEFAULT_SEEDS == (0, 1, 2, 9, 17, 23, 100)
    assert report["declared_rival_count"] == len(p.RIVALS) == 14
    assert report["shadow_selector_count"] == len(p.SHADOW_SELECTORS) == 2
    assert report["shadow_selector_query_safe"] is True

    broken = dict(report)
    broken["shadow_selector_query_safe"] = False
    assert probe.failures_from(broken) == ["a demo-equivalent shadow selector changes a query"]
