"""Native parametric family tests for the perimeter-tie curriculum."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from arcpuzzles import Catalog
from reviewer_support import find_root

HOME = Path(__file__).resolve().parents[1]
PARAM = HOME / "workspace" / "parametric"
ROOT = find_root(__file__)
TASK_ID = "270af96a99b0"
SETTINGS = (
    {"tie_break": "source_position"},
    {"tie_break": "smaller_area"},
)


def load_module(filename: str):
    path = PARAM / filename
    name = "_test_270af96a99b0_" + filename.replace(".", "_") + hashlib.sha256(
        str(path).encode()
    ).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    return module


def adapter():
    return load_module("adapter.py")


def oracle():
    return load_module("oracle.py")


def _inputs(episode, split):
    return [pair["input"] for pair in episode[split]]


def test_contract_declares_exact_finite_family_and_default():
    contract = json.loads((PARAM / "promotion.json").read_text())
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/270af96a99b0/workspace/parametric/adapter.py",
        "parameters": {"tie_break": ["source_position", "smaller_area"]},
        "default": {"tie_break": "source_position"},
        "qualification_demos": 3,
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "resources": [
            "generators/270af96a99b0/workspace/parametric/prototype.py",
            "generators/270af96a99b0/workspace/parametric/oracle.py",
            "generators/270af96a99b0/workspace/parametric/rivals.py",
            "generators/270af96a99b0/workspace/parametric/canonical.rkt",
            "generators/270af96a99b0/workspace/parametric/smaller_area.rkt",
            "generators/270af96a99b0/workspace/parametric/audit.py",
        ],
    }


def test_default_program_is_exact_selected_canonical_bytes():
    mod = adapter()
    record = Catalog(ROOT).get(TASK_ID)
    programs = {
        variant["program_solution"]
        for variant in record["variants"]
        if isinstance(variant.get("program_solution"), str)
    }
    assert len(programs) == 1
    canonical = next(iter(programs))
    assert (PARAM / "canonical.rkt").read_bytes() == canonical.encode("utf-8")
    assert mod.program(SETTINGS[0]) == canonical
    assert mod.program(SETTINGS[1]) == (PARAM / "smaller_area.rkt").read_text()
    assert mod.program(SETTINGS[1]) != canonical


@pytest.mark.parametrize(
    "bad",
    [
        None,
        {},
        {"tie_break": "unknown"},
        {"tie_break": 1},
        {"tie_break": "source_position", "extra": True},
    ],
)
def test_adapter_rejects_undeclared_settings(bad):
    mod = adapter()
    with pytest.raises(ValueError):
        mod.program(bad)
    with pytest.raises(ValueError):
        mod.generate(0, bad, 3, 4)


@pytest.mark.parametrize("demos", [2, 3, 6])
@pytest.mark.parametrize("queries", [1, 4])
def test_counts_matched_inputs_and_count_independent_prefixes(demos, queries):
    mod = adapter()
    episodes = [mod.generate(17, setting, demos, queries) for setting in SETTINGS]
    for episode, setting in zip(episodes, SETTINGS):
        assert set(episode) == {"train", "test", "program_solution"}
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == queries
        assert episode["program_solution"] == mod.program(setting)
        assert len({json.dumps(pair["input"]) for split in ("train", "test") for pair in episode[split]}) == demos + queries
    assert _inputs(episodes[0], "train") == _inputs(episodes[1], "train")
    assert _inputs(episodes[0], "test") == _inputs(episodes[1], "test")

    full = mod.generate(17, SETTINGS[0], 6, 4)
    assert _inputs(episodes[0], "train") == _inputs(full, "train")[:demos]
    assert _inputs(episodes[0], "test") == _inputs(full, "test")[:queries]


@pytest.mark.parametrize("seed", [0, 17, 97])
def test_every_demonstration_identifies_the_setting_and_labels_match_oracle(seed):
    mod = adapter()
    ref = oracle()
    source = mod.generate(seed, SETTINGS[0], 6, 4)
    alternate = mod.generate(seed, SETTINGS[1], 6, 4)
    assert _inputs(source, "train") == _inputs(alternate, "train")
    assert _inputs(source, "test") == _inputs(alternate, "test")

    for split in ("train", "test"):
        for left, right in zip(source[split], alternate[split]):
            grid = left["input"]
            assert left["output"] == ref.solve(grid, "source_position")
            assert right["output"] == ref.solve(grid, "smaller_area")
            assert left["output"] != right["output"]


def test_query_bank_contains_substantive_boundary_spanning_30x30_case():
    mod = adapter()
    ref = oracle()
    episode = mod.generate(31, SETTINGS[1], 6, 4)
    large_pairs = [pair for pair in episode["test"] if len(pair["input"]) == 30 and len(pair["input"][0]) == 30]
    assert len(large_pairs) == 1
    pair = large_pairs[0]
    grid = pair["input"]
    foreground = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value}
    assert len(foreground) >= 70
    assert any(r == 0 for r, _ in foreground)
    assert any(r == 29 for r, _ in foreground)
    assert any(c == 0 for _, c in foreground)
    assert any(c == 29 for _, c in foreground)
    components = ref.components(grid)
    assert len(components) == 4
    assert len({component.color for component in components}) == 4
    assert pair["output"] == ref.solve(grid, "smaller_area")
    assert ref.solve(grid, "source_position") != pair["output"]
    assert len(pair["output"]) <= 30 and len(pair["output"][0]) <= 30


def test_bounded_finite_rival_audit_finds_no_query_changing_survivor():
    audit = load_module("audit.py")
    result = audit.run(seeds=range(8), demo_counts=(2, 3, 6))
    assert result["status"] == "passed"
    assert result["episodes"] == 8 * 3 * 2
    assert result["pairs"] == 8 * 2 * sum(count + 4 for count in (2, 3, 6))
    assert result["query_changing_survivors"] == []
    assert result["matched_input_failures"] == []
    assert result["prefix_failures"] == []
    assert result["large_query_failures"] == []


def test_two_demo_prefix_rejects_global_area_shortcut_for_seed_four():
    mod = adapter()
    rival_mod = load_module("rivals.py")
    episode = mod.generate(4, {"tie_break": "smaller_area"}, 2, 4)
    assert any(
        rival_mod.global_area(pair["input"]) != pair["output"]
        for pair in episode["train"]
    )
