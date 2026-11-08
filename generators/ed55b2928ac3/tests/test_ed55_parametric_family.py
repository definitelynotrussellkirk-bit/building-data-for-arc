from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]
HOME = ROOT / "generators/ed55b2928ac3/workspace/parametric"
RUNTIME = ROOT / "shared/runtime"
for path in (RUNTIME, HOME):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


def _module(filename: str, name: str):
    path = HOME / filename
    assert path.is_file(), f"missing {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_default_program_is_exact_catalog_canonical():
    prototype = _module("prototype.py", "ed55_parametric_prototype")
    canonical = json.loads((ROOT / "shared/data/base/solutions/banks/fec6a16dfcc9/medium_p07__ed55b2928ac3.json").read_text())["racket_target"]["target_code"]
    assert prototype.program_for("plain") == canonical
    assert (HOME / "canonical.rkt").read_text() == canonical


def test_matched_inputs_counts_distinctness_and_stress_query():
    prototype = _module("prototype.py", "ed55_parametric_prototype_counts")
    for demos in range(2, 7):
        plain = prototype.generate_claims(17, "plain", demos=demos, queries=4)
        marked = prototype.generate_claims(17, "top_edge_to_8", demos=demos, queries=4)
        assert len(plain["train"]) == demos and len(plain["test"]) == 4
        assert [p["input"] for p in plain["train"] + plain["test"]] == [p["input"] for p in marked["train"] + marked["test"]]
        packed = [json.dumps(p["input"], separators=(",", ":")) for p in plain["train"] + plain["test"]]
        assert len(packed) == len(set(packed))
        stress = plain["test"][-1]["input"]
        assert (len(stress), len(stress[0])) == (30, 30)
        assert all(a["output"] != b["output"] for a, b in zip(plain["train"], marked["train"]))


def test_wrong_order_counterfactual_changes_the_final_output():
    prototype = _module("prototype.py", "ed55_parametric_prototype_causal")
    episode = prototype.generate_claims(43, "top_edge_to_8", demos=3, queries=4)
    divergences = []
    for pair in episode["train"] + episode["test"]:
        correct = prototype.python_mirror(pair["input"], "top_edge_to_8")
        wrong = prototype.python_wrong_order(pair["input"])
        assert correct == pair["output"]
        divergences.append(correct != wrong)
    assert all(divergences)


def test_adapter_rejects_malformed_settings_and_counts():
    adapter = _module("adapter.py", "ed55_parametric_adapter")
    with pytest.raises(ValueError):
        adapter.program({"finish_mode": "unknown"})
    with pytest.raises(ValueError):
        adapter.program({"finish_mode": "plain", "extra": 1})
    with pytest.raises(ValueError):
        adapter.generate(0, {"finish_mode": "plain"}, 1, 4)
    with pytest.raises(ValueError):
        adapter.generate(0, {"finish_mode": "plain"}, 2, 3)
