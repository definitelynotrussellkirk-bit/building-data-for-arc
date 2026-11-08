"""Native adapter contract for the turn-preference parametric family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from arcpuzzles import Catalog
from reviewer_support import find_root

TASK_ID = "f8d1d470d522"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID / "workspace" / "parametric"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    record = Catalog(ROOT).get(TASK_ID)
    programs = {
        variant["program_solution"]
        for variant in record["variants"]
        if isinstance(variant.get("program_solution"), str)
    }
    assert len(programs) == 1
    return next(iter(programs))


def test_native_programs_preserve_exact_default_and_change_turn_objective():
    prototype = _load("f8_native_prototype", HOME / "prototype.py")
    assert prototype.program_for("fewest") == _canonical_program()
    alternative = prototype.program_for("most")
    assert alternative.startswith("(rule!")
    assert alternative != _canonical_program()
    assert "(> turns best-turns)" in alternative


def test_adapter_supports_two_to_six_demos_and_exactly_four_queries():
    prototype = _load("f8_native_prototype_counts", HOME / "prototype.py")
    adapter = _load("f8_native_adapter", HOME / "adapter.py")
    for preference in prototype.ALLOWED_TURN_PREFERENCES:
        settings = {"turn_preference": preference}
        for demos in (2, 3, 6):
            episode = adapter.generate(17, settings, demos, 4)
            assert episode["program_solution"] == adapter.program(settings)
            assert len(episode["train"]) == demos
            assert len(episode["test"]) == 4
            pairs = [*episode["train"], *episode["test"]]
            serialized = [json.dumps(pair["input"], separators=(",", ":")) for pair in pairs]
            assert len(serialized) == len(set(serialized))
            other = "most" if preference == "fewest" else "fewest"
            assert all(
                prototype.python_reference(pair["input"], turn_preference=preference)
                == pair["output"]
                for pair in pairs
            )
            assert all(
                prototype.python_reference(pair["input"], turn_preference=other)
                != pair["output"]
                for pair in episode["train"]
            )
            stress = episode["test"][-1]["input"]
            assert (len(stress), len(stress[0])) == (30, 30)
            assert prototype.python_reference(stress, turn_preference="fewest") != prototype.python_reference(
                stress, turn_preference="most"
            )


def test_adapter_is_deterministic_and_rejects_undeclared_requests():
    adapter = _load("f8_native_adapter_validation", HOME / "adapter.py")
    settings = {"turn_preference": "fewest"}
    assert adapter.generate(3, settings, 2, 4) == adapter.generate(3, settings, 2, 4)
    with pytest.raises(ValueError, match="exactly"):
        adapter.program({})
    with pytest.raises(ValueError, match="turn_preference"):
        adapter.program({"turn_preference": "middle"})
    with pytest.raises(ValueError, match="demos"):
        adapter.generate(3, settings, 1, 4)
    with pytest.raises(ValueError, match="queries"):
        adapter.generate(3, settings, 2, 3)
    with pytest.raises(TypeError, match="seed"):
        adapter.generate(True, settings, 2, 4)


def test_promotion_binds_dynamic_sources_and_retains_replayable_audit_tool():
    promotion = json.loads((HOME / "promotion.json").read_text())
    assert promotion["qualification_demos"] == 2
    assert promotion["limits"] == {"demos": [2, 6], "queries": [4, 4]}
    assert set(promotion["resources"]) == {
        f"generators/{TASK_ID}/workspace/parametric/prototype.py",
        f"generators/{TASK_ID}/workspace/parametric/rules/turn_fewest.rkt",
        f"generators/{TASK_ID}/workspace/parametric/rules/turn_most.rkt",
    }
    assert (HOME / "self_audit.py").is_file()
