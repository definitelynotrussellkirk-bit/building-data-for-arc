from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
HOME = ROOT / "generators/7358813cf026/workspace/parametric"
PROTOTYPE = HOME / "prototype.py"
ADAPTER = HOME / "adapter.py"
PROMOTION = HOME / "promotion.json"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def family():
    assert PROTOTYPE.is_file(), "parametric prototype is missing"
    return _load(PROTOTYPE, "_test_parametric_735")


def _canonical_program() -> str:
    from arcpuzzles import Catalog

    catalog = Catalog(ROOT)
    row = catalog.describe("7358813cf026")
    programs = {
        variant["program_solution"]
        for variant in catalog._variants()[row.get("rule_task_id", row["id"])]
    }
    assert len(programs) == 1
    return next(iter(programs))


def test_default_program_is_byte_exact_canonical(family):
    """Catches a default branch that rephrases instead of preserving authority bytes."""
    assert family.program({"singleton_policy": "erase_all"}) == _canonical_program()


def test_contract_and_adapter_expose_finite_family(family):
    """Catches missing promotion metadata or an adapter wired to another family."""
    contract = json.loads(PROMOTION.read_text())
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/7358813cf026/workspace/parametric/adapter.py",
        "parameters": {
            "singleton_policy": ["erase_all", "protect_largest_color"]
        },
        "default": {"singleton_policy": "erase_all"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "qualification_demos": 2,
        "resources": [
            "generators/7358813cf026/workspace/parametric/prototype.py"
        ],
    }
    adapter = _load(ADAPTER, "_test_adapter_735")
    assert adapter.program({"singleton_policy": "protect_largest_color"}) == family.program(
        {"singleton_policy": "protect_largest_color"}
    )


def test_two_demos_identify_each_setting_and_four_queries_are_distinct(family):
    """Catches visible demonstrations that leave both finite settings consistent."""
    for setting in family.SETTINGS:
        episode = family.generate(17, setting, demos=2, queries=4)
        assert len(episode["train"]) == 2
        assert len(episode["test"]) == 4
        inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
        assert len({family.digest(grid) for grid in inputs}) == 6
        survivors = [
            candidate
            for candidate in family.SETTINGS
            if all(
                family.transform(pair["input"], candidate) == pair["output"]
                for pair in episode["train"]
            )
        ]
        assert survivors == [setting]
        for pair in episode["train"] + episode["test"]:
            assert family.transform(pair["input"], setting) == pair["output"]


def test_protected_setting_uses_input_dependent_nonlocal_intermediate(family):
    """Catches a fixed-color shortcut or a branch that does not protect remote anchor singletons."""
    seen_colors = set()
    setting = {"singleton_policy": "protect_largest_color"}
    for seed in (0, 1, 17, 29):
        episode = family.generate(seed, setting, demos=2, queries=4)
        for pair in episode["train"]:
            info = family.analyze(pair["input"])
            seen_colors.add(info["largest_object_color"])
            assert info["largest_object_unique"] is True
            assert info["largest_object_size"] == 6
            assert info["anchor_color_singletons"] >= 1
            assert info["second_color_singletons"] >= 1
            assert family.transform_with_rank(pair["input"], rank=1) == pair["output"]
            assert family.transform_with_rank(pair["input"], rank=2) != pair["output"]
    assert len(seen_colors) >= 3


def test_fourth_query_is_substantive_30x30_stress(family):
    """Catches nominal 30x30 padding with meaningful content confined to a corner."""
    episode = family.generate(
        43, {"singleton_policy": "protect_largest_color"}, demos=2, queries=4
    )
    grid = episode["test"][3]["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    info = family.analyze(grid)
    assert info["nonzero_count"] >= 35
    assert info["row_span"] >= 27
    assert info["col_span"] >= 27
    assert info["object_count"] >= 10


def test_invalid_settings_and_counts_are_rejected(family):
    """Catches permissive coercion and out-of-contract episode sizes."""
    with pytest.raises(ValueError):
        family.program({"singleton_policy": "unknown"})
    with pytest.raises(ValueError):
        family.generate(True, family.SETTINGS[0], 2, 4)
    with pytest.raises(ValueError):
        family.generate(0, family.SETTINGS[0], 1, 4)
    with pytest.raises(ValueError):
        family.generate(0, family.SETTINGS[0], 2, 5)
