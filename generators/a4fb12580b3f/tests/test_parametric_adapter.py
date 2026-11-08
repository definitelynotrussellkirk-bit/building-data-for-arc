"""Native adapter boundary: paired settings, count limits, and caller isolation."""
from __future__ import annotations

import importlib.util
import random
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]


def adapter():
    path = HOME / "workspace/parametric/adapter.py"
    assert path.is_file(), "Native adapter is not implemented yet"
    spec = importlib.util.spec_from_file_location("a4fb_adapter_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_paired_settings_counts_distinctness_and_nontrivial_rule_change(demos):
    mod = adapter()
    before = random.getstate()
    a = mod.generate(17, {"mode": "direct"}, demos, 4)
    b = mod.generate(17, {"mode": "largest_relay"}, demos, 4)
    assert random.getstate() == before
    assert len(a["train"]) == len(b["train"]) == demos
    assert len(a["test"]) == len(b["test"]) == 4
    for split in ("train", "test"):
        assert [p["input"] for p in a[split]] == [p["input"] for p in b[split]]
        assert any(x["output"] != y["output"] for x, y in zip(a[split], b[split]))
    inputs = [p["input"] for split in ("train", "test") for p in a[split]]
    assert len({repr(g) for g in inputs}) == demos + 4
    assert any(len(g) == 30 and len(g[0]) == 30 for g in inputs)
    a["test"][0]["input"][0][0] = 99
    assert mod.generate(17, {"mode": "direct"}, demos, 4)["test"][0]["input"][0][0] != 99


@pytest.mark.parametrize("args", [
    (True, 3, 4), (-1, 3, 4), (2**63, 3, 4),
    (0, 1, 4), (0, 7, 4), (0, True, 4), (0, 3, 0), (0, 3, 5), (0, 3, True),
])
def test_invalid_seed_or_count_fails_before_sampling(args):
    seed, demos, queries = args
    with pytest.raises(ValueError):
        adapter().generate(seed, {"mode": "direct"}, demos, queries)


def test_single_query_has_identical_demo_context_and_first_query():
    mod = adapter()
    a = mod.generate(0, {"mode": "largest_relay"}, 3, 1)
    b = mod.generate(0, {"mode": "largest_relay"}, 3, 4)
    assert a["train"] == b["train"]
    assert a["test"] == b["test"][:1]
