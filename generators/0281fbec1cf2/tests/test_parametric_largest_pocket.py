"""Native promotion tests for the blocker-created largest-pocket family."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

import pytest

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import find_root, normalize_grid

TASK_ID = "0281fbec1cf2"
ROOT = find_root(__file__)
PARAMETRIC = ROOT / "generators" / TASK_ID / "workspace" / "parametric"
ADAPTER_PATH = PARAMETRIC / "adapter.py"
FAMILY_PATH = PARAMETRIC / "native_family.py"
AUDIT_PATH = PARAMETRIC / "audit_native.py"
CONTRACT_PATH = PARAMETRIC / "promotion.json"
CANONICAL_PATH = PARAMETRIC / "canonical.rkt"
ALTERNATIVE_PATH = PARAMETRIC / "largest_pocket.rkt"
EXPECTED_CANONICAL_SHA256 = "02b458e5f6e265674740fa37facab026465106b764f3814257714bfcde73164e"


def _load(path: Path, suffix: str):
    assert path.is_file(), f"required native source is missing: {path.name}"
    name = f"_native_{TASK_ID}_{suffix}_{hashlib.sha256(str(path).encode()).hexdigest()}"
    module = sys.modules.get(name)
    if module is not None:
        return module
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def adapter():
    return _load(ADAPTER_PATH, "adapter")


@pytest.fixture(scope="module")
def family():
    return _load(FAMILY_PATH, "family")


@pytest.fixture(scope="module")
def audit_module():
    return _load(AUDIT_PATH, "audit")


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge() as instance:
        assert instance.runtime_identity["backend"] == "racket"
        assert instance.runtime_identity["protected"] is True
        yield instance


def _pairs(episode: dict[str, Any]) -> list[dict[str, list[list[int]]]]:
    return [*episode["train"], *episode["test"]]


def _inputs(episode: dict[str, Any]) -> list[list[list[int]]]:
    return [pair["input"] for pair in _pairs(episode)]


def _literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def _execute(bridge: RacketBridge, program: str, grid: list[list[int]]) -> list[list[int]]:
    return normalize_grid(bridge.eval_text(f"({wrap_rule(program)} {_literal(grid)})"))


def test_promotion_contract_names_exact_adapter_settings_and_limits():
    assert json.loads(CONTRACT_PATH.read_text()) == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"finish": ["rays_only", "largest_pocket"]},
        "default": {"finish": "rays_only"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "resources": [
            f"generators/{TASK_ID}/workspace/parametric/canonical.rkt",
            f"generators/{TASK_ID}/workspace/parametric/largest_pocket.rkt",
            f"generators/{TASK_ID}/workspace/parametric/native_family.py",
        ],
    }


def test_program_preserves_exact_canonical_default_and_declares_alternative(adapter):
    canonical = adapter.program({"finish": "rays_only"})
    alternative = adapter.program({"finish": "largest_pocket"})
    assert canonical == CANONICAL_PATH.read_text()
    assert alternative == ALTERNATIVE_PATH.read_text()
    assert hashlib.sha256(canonical.encode()).hexdigest() == EXPECTED_CANONICAL_SHA256
    assert alternative != canonical
    assert "find-0-regions" in alternative
    assert "pick-max enclosed length" in alternative


@pytest.mark.parametrize(
    "settings",
    [
        None,
        {},
        {"finish": "rays_only", "extra": 1},
        {"finish": "all_pockets"},
        {"finish": True},
        {"finish": 1},
    ],
)
def test_program_rejects_noncontract_settings(adapter, settings):
    with pytest.raises(ValueError, match="settings|finish"):
        adapter.program(settings)


@pytest.mark.parametrize("bad", [True, False, 1.0, "1", None, -1])
def test_generate_rejects_invalid_seed_scalars(adapter, bad):
    with pytest.raises((TypeError, ValueError), match="seed"):
        adapter.generate(bad, {"finish": "rays_only"}, 3, 4)


@pytest.mark.parametrize(
    "name,bad",
    [
        ("demos", True),
        ("demos", 1),
        ("demos", 7),
        ("queries", False),
        ("queries", 0),
        ("queries", 5),
    ],
)
def test_generate_rejects_invalid_count_scalars(adapter, name, bad):
    kwargs = {
        "seed": 0,
        "settings": {"finish": "rays_only"},
        "demos": 3,
        "queries": 4,
    }
    kwargs[name] = bad
    with pytest.raises((TypeError, ValueError), match=name):
        adapter.generate(**kwargs)


def test_counts_are_independent_prefix_stable_deterministic_and_unique(adapter):
    settings = {"finish": "rays_only"}
    minimum = adapter.generate(23, settings, 2, 1)
    maximum = adapter.generate(23, settings, 6, 4)
    repeated = adapter.generate(23, settings, 6, 4)
    four_queries = adapter.generate(23, settings, 2, 4)
    assert set(minimum) == {"train", "test", "program_solution"}
    assert len(minimum["train"]) == 2
    assert len(minimum["test"]) == 1
    assert len(maximum["train"]) == 6
    assert len(maximum["test"]) == 4
    assert maximum == repeated
    assert minimum["train"] == maximum["train"][:2]
    assert minimum["test"][0] == four_queries["test"][0]
    serialized = [json.dumps(grid, separators=(",", ":")) for grid in _inputs(maximum)]
    assert len(serialized) == len(set(serialized)) == 10


def test_inputs_are_setting_independent_and_every_label_changes(adapter):
    canonical = adapter.generate(17, {"finish": "rays_only"}, 6, 4)
    alternate = adapter.generate(17, {"finish": "largest_pocket"}, 6, 4)
    assert _inputs(canonical) == _inputs(alternate)
    assert all(
        left["output"] != right["output"]
        for left, right in zip(_pairs(canonical), _pairs(alternate), strict=True)
    )


def test_first_query_is_substantive_30x30_with_multiple_new_pockets(adapter, family):
    episode = adapter.generate(0, {"finish": "largest_pocket"}, 2, 4)
    grid = episode["test"][0]["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    assert sum(cell != 0 for row in grid for cell in row) >= 80
    facts = family.analyze_scene(grid)
    assert len(facts["enclosed_pockets"]) >= 4
    sizes = [len(region) for region in facts["enclosed_pockets"]]
    assert max(sizes) >= 6
    assert sizes.count(max(sizes)) == 1
    assert facts["target_marker_color"] not in (0, 2)
    assert facts["stage_a"] != grid
    assert facts["largest_pocket_output"] != facts["stage_a"]


def test_python_claimed_labels_match_both_programs_in_protected_racket(adapter, bridge):
    for finish in ("rays_only", "largest_pocket"):
        settings = {"finish": finish}
        episode = adapter.generate(0, settings, 2, 4)
        program = adapter.program(settings)
        assert episode["program_solution"] == program
        for pair in _pairs(episode):
            assert _execute(bridge, program, pair["input"]) == pair["output"]


def test_minimum_lesson_rejects_named_shortcuts_in_protected_racket(audit_module):
    report = audit_module.audit(seed=0)
    assert report["status"] == "pass"
    assert report["racket"]["backend"] == "racket"
    assert report["racket"]["protected"] is True
    assert report["scope"] == {
        "seed": 0,
        "demos": 2,
        "queries": 4,
        "settings": 2,
        "rivals_per_setting": 5,
    }
    for row in report["settings"]:
        assert row["chosen_labels_match_racket"] is True
        assert all(not rival["fits_demonstrations"] for rival in row["rivals"].values())
        assert all(rival["query_differs"] for rival in row["rivals"].values())


def test_causal_witness_replays_skip_a_counterfactual(audit_module):
    witness = audit_module.causal_witness(seed=0)
    assert witness["status"] == "reviewer_replayed"
    assert witness["setting"] == {"finish": "largest_pocket"}
    assert witness["step_a"] == "canonical blocker-aware red-ray expansion"
    assert witness["intermediate"] == "expanded grid whose red walls create enclosed zero pockets"
    assert witness["step_b"] == "select the unique largest enclosed zero pocket and fill it with its adjacent marker color"
    assert witness["chosen_output"] != witness["counterfactual_output"]
    assert witness["stage_a_output"] != witness["input"]
    assert witness["counterfactual_program_sha256"] != witness["chosen_program_sha256"]


def test_seed_104_decoys_preserve_declared_pocket_signature(adapter, family):
    """Regression: two inert decoys must not close an extra corner pocket."""
    episode = adapter.generate(104, {"finish": "largest_pocket"}, 2, 1)
    facts = family.analyze_scene(episode["train"][0]["input"])
    assert sorted(map(len, facts["enclosed_pockets"])) == [1, 2, 4]
    assert facts["target_marker_color"] == 6
