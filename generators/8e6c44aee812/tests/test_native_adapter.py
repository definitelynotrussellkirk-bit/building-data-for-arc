"""Native promotion boundary checks for the staircase family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from arcpuzzles import Catalog
from reviewer_support import find_root


HOME = Path(__file__).resolve().parents[1]
ROOT = find_root(__file__)


def load_adapter():
    path = HOME / "workspace/parametric/adapter.py"
    spec = importlib.util.spec_from_file_location("native_staircase_adapter_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_default_program_is_exact_catalog_source():
    adapter = load_adapter()
    record = Catalog(ROOT).get("8e6c44aee812")
    selected = {v["program_solution"] for v in record["variants"]
                if isinstance(v.get("program_solution"), str)}
    assert selected == {adapter.program({"output_scale": 2})}
    assert adapter.program({"output_scale": 3}) != next(iter(selected))


def test_promotion_contract_and_native_episode_agree():
    adapter = load_adapter()
    contract = json.loads((HOME / "workspace/parametric/promotion.json").read_text())
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/8e6c44aee812/workspace/parametric/adapter.py",
        "parameters": {"output_scale": [2, 3]},
        "default": {"output_scale": 2},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
    }
    for scale in (2, 3):
        settings = {"output_scale": scale}
        episode = adapter.generate(17, settings, demos=3, queries=4)
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 4
        assert episode["program_solution"] == adapter.program(settings)
