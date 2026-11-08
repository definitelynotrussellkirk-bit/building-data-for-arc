from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

TASK_HOME = Path(__file__).resolve().parents[1]
REPO = TASK_HOME.parents[1]
RUNTIME = REPO / "shared" / "runtime"
SRC = REPO / "src"
PARAMETRIC = TASK_HOME / "workspace" / "parametric"
for path in (RUNTIME, SRC):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


def load_adapter():
    path = PARAMETRIC / "adapter.py"
    spec = importlib.util.spec_from_file_location("parametric_08eaba8254b2", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_source() -> str:
    from arcpuzzles.catalog import Catalog

    catalog = Catalog(REPO)
    selected = catalog.describe("08eaba8254b2")
    variants = catalog._variants()[selected.get("rule_task_id", "08eaba8254b2")]
    programs = {variant["program_solution"] for variant in variants}
    assert len(programs) == 1
    return next(iter(programs))


def test_contract_and_default_program_are_source_exact():
    adapter = load_adapter()
    promotion = json.loads((PARAMETRIC / "promotion.json").read_text(encoding="utf-8"))
    assert promotion["schema"] == "arcpuzzles-parametric-adapter-v1"
    assert promotion["parameters"] == {
        "output_mode": ["xor_mask", "largest_xor_component"]
    }
    assert promotion["default"] == {"output_mode": "xor_mask"}
    assert promotion["limits"] == {"demos": [2, 6], "queries": [1, 4]}
    assert adapter.program({"output_mode": "xor_mask"}) == canonical_source()
    assert (PARAMETRIC / "canonical.rkt").read_text(encoding="utf-8") == canonical_source()
    assert adapter.program({"output_mode": "largest_xor_component"}) == (
        PARAMETRIC / "largest.rkt"
    ).read_text(encoding="utf-8")


@pytest.mark.parametrize("seed", [0, 17])
def test_generation_is_matched_identifying_distinct_and_count_independent(seed: int):
    adapter = load_adapter()
    xor_episode = adapter.generate(seed, {"output_mode": "xor_mask"}, 2, 4)
    largest_episode = adapter.generate(
        seed, {"output_mode": "largest_xor_component"}, 2, 4
    )

    assert [pair["input"] for pair in xor_episode["train"] + xor_episode["test"]] == [
        pair["input"] for pair in largest_episode["train"] + largest_episode["test"]
    ]
    assert all(
        a["output"] != b["output"]
        for a, b in zip(xor_episode["train"], largest_episode["train"])
    )

    one_query = adapter.generate(seed, {"output_mode": "xor_mask"}, 2, 1)
    assert one_query["train"] == xor_episode["train"]
    assert one_query["test"][0] == xor_episode["test"][0]

    encoded = [
        json.dumps(pair["input"], separators=(",", ":"))
        for pair in xor_episode["train"] + xor_episode["test"]
    ]
    assert len(encoded) == len(set(encoded)) == 6


@pytest.mark.parametrize("setting", ["xor_mask", "largest_xor_component"])
def test_four_query_lesson_contains_substantive_9_by_30_stress(setting: str):
    adapter = load_adapter()
    prototype = adapter._impl
    episode = adapter.generate(31, {"output_mode": setting}, 2, 4)
    stress = episode["test"][3]
    assert (len(stress["input"]), len(stress["input"][0])) == (9, 30)
    assert (len(stress["output"]), len(stress["output"][0])) == (4, 30)
    cells = prototype.xor_cells(stress["input"])
    components = prototype.components(cells)
    assert len(cells) >= 12
    assert len(components) >= 3
    assert max(len(component) for component in components) >= 4
    assert min(c for _, c in cells) <= 1
    assert max(c for _, c in cells) >= 28


def test_largest_stage_depends_on_xor_intermediate_and_rejects_top_panel_shortcut():
    adapter = load_adapter()
    prototype = adapter._impl
    episode = adapter.generate(43, {"output_mode": "largest_xor_component"}, 2, 4)
    for pair in episode["train"]:
        grid = pair["input"]
        xor_components = prototype.components(prototype.xor_cells(grid))
        sizes = sorted((len(component) for component in xor_components), reverse=True)
        assert len(xor_components) >= 2
        assert sizes[0] > sizes[1]

        largest = prototype.transform_with_selector(grid, "largest_xor_component")
        canonical = prototype.transform_with_selector(grid, "xor_mask")
        top_shortcut = prototype.transform_with_selector(grid, "largest_top_component")
        assert largest == pair["output"]
        assert largest != canonical
        assert largest != top_shortcut
        assert sum(cell == 3 for row in largest for cell in row) == sizes[0]

    assert prototype.counterfactual_program("largest_top_component") == (
        PARAMETRIC / "top-largest.rkt"
    ).read_text(encoding="utf-8")


def test_adapter_rejects_malformed_requests():
    adapter = load_adapter()
    with pytest.raises(ValueError, match="settings"):
        adapter.program({})
    with pytest.raises(ValueError, match="output_mode"):
        adapter.program({"output_mode": "smallest"})
    with pytest.raises(ValueError, match="demos"):
        adapter.generate(0, {"output_mode": "xor_mask"}, 1, 4)
    with pytest.raises(ValueError, match="queries"):
        adapter.generate(0, {"output_mode": "xor_mask"}, 2, 5)


@pytest.mark.parametrize("seed", [0, 14, 17, 75, 161, 369])
@pytest.mark.parametrize("mode", ["xor_mask", "largest_xor_component"])
def test_minimum_demos_identify_mode_against_declared_shortcuts(seed: int, mode: str):
    adapter = load_adapter()
    episode = adapter.generate(seed, {"output_mode": mode}, 2, 4)
    certificate = adapter._impl.teaching_certificate(
        episode["train"], {"output_mode": mode}
    )

    assert certificate["survivors"] == [mode]
    assert episode["certificate"] == certificate


def test_bounded_probe_reports_finite_teaching_certificate():
    path = PARAMETRIC / "probe.py"
    spec = importlib.util.spec_from_file_location("_xor_probe_test", path)
    assert spec and spec.loader
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)

    report = probe.run()

    assert report["checks"]["finite_declared_shortcut_certificate"] is True
    assert report["teaching_certificates"]
    assert all(
        row["survivors"] == [row["selected"]]
        for row in report["teaching_certificates"]
    )
