"""Native promotion tests for the horizontal-beam relay family."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, find_root, public_challenge_bytes

TASK_ID = "78806e443729"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID / "workspace" / "parametric"
ADAPTER_PATH = HOME / "adapter.py"
FAMILY_PATH = HOME / "family.py"
AUDIT_PATH = HOME / "audit.py"
PROMOTION_PATH = HOME / "promotion.json"
EXPECTED_CANONICAL_SHA256 = "65a855ce11f7677687180f9efce9eaa4d834294153ea86cdc41c0a88e911ad02"


def _load(path: Path, suffix: str):
    assert path.is_file(), f"missing {path.name}"
    name = f"_parametric_{TASK_ID}_{suffix}_{hashlib.sha256(str(path).encode()).hexdigest()}"
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


def _pairs(episode):
    return [*episode["train"], *episode["test"]]


def _inputs(episode):
    return [pair["input"] for pair in _pairs(episode)]


def _literal(grid):
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def _execute(bridge, program, grid):
    return bridge.eval_text(f"({wrap_rule(program)} {_literal(grid)})")


def _canonical_source():
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        programs = {
            row["program_solution"]
            for raw in handle
            if (row := json.loads(raw)).get("task_id") == TASK_ID
        }
    assert len(programs) == 1
    return next(iter(programs))


def test_promotion_contract_is_exact_and_uses_three_demo_qualification():
    assert json.loads(PROMOTION_PATH.read_text()) == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"beam_mode": ["horizontal_only", "dominant_relay"]},
        "default": {"beam_mode": "horizontal_only"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "qualification_demos": 3,
    }


def test_default_program_is_exact_canonical_and_alternate_is_distinct(adapter):
    canonical = _canonical_source()
    default = adapter.program({"beam_mode": "horizontal_only"})
    alternate = adapter.program({"beam_mode": "dominant_relay"})
    assert default == canonical
    assert hashlib.sha256(default.encode()).hexdigest() == EXPECTED_CANONICAL_SHA256
    assert alternate != default
    assert "(mode base 0)" in alternate
    assert "(paint-cells base (append up down) dominant)" in alternate


@pytest.mark.parametrize(
    "settings",
    [None, {}, {"beam_mode": "relay"}, {"beam_mode": True}, {"beam_mode": "horizontal_only", "extra": 1}],
)
def test_program_rejects_noncontract_settings(adapter, settings):
    with pytest.raises(ValueError, match="settings|beam_mode"):
        adapter.program(settings)


@pytest.mark.parametrize("bad", [True, False, -1, 1.5, "1", None])
def test_generate_rejects_invalid_seed(adapter, bad):
    with pytest.raises((TypeError, ValueError), match="seed"):
        adapter.generate(bad, {"beam_mode": "horizontal_only"}, 3, 4)


@pytest.mark.parametrize(
    "name,bad",
    [("demos", True), ("demos", 1), ("demos", 7), ("queries", False), ("queries", 0), ("queries", 5)],
)
def test_generate_rejects_invalid_counts(adapter, name, bad):
    kwargs = dict(seed=0, settings={"beam_mode": "horizontal_only"}, demos=3, queries=4)
    kwargs[name] = bad
    with pytest.raises((TypeError, ValueError), match=name):
        adapter.generate(**kwargs)


def test_counts_are_independent_deterministic_unique_and_query_stable(adapter):
    setting = {"beam_mode": "horizontal_only"}
    minimum = adapter.generate(23, setting, 2, 1)
    maximum = adapter.generate(23, setting, 6, 4)
    repeated = adapter.generate(23, setting, 6, 4)
    four_queries = adapter.generate(23, setting, 2, 4)
    assert set(minimum) == {"train", "test", "program_solution"}
    assert minimum == adapter.generate(23, setting, 2, 1)
    assert maximum == repeated
    assert minimum["train"] == maximum["train"][:2]
    assert minimum["test"][0] == four_queries["test"][0]
    serialized = [json.dumps(grid, separators=(",", ":")) for grid in _inputs(maximum)]
    assert len(serialized) == len(set(serialized)) == 10


def test_inputs_match_across_settings_and_every_label_changes(adapter):
    horizontal = adapter.generate(17, {"beam_mode": "horizontal_only"}, 6, 4)
    relay = adapter.generate(17, {"beam_mode": "dominant_relay"}, 6, 4)
    assert _inputs(horizontal) == _inputs(relay)
    assert all(
        left["output"] != right["output"]
        for left, right in zip(_pairs(horizontal), _pairs(relay), strict=True)
    )


def test_family_has_unique_dominant_intermediate_and_vertical_blocker_cases(adapter, family):
    episode = adapter.generate(0, {"beam_mode": "dominant_relay"}, 6, 4)
    sides = set()
    blocker_cases = 0
    for pair in _pairs(episode):
        facts = family.analyze_input(pair["input"])
        assert facts["dominant_count"] > facts["runner_up_count"]
        assert len(facts["dominant_seed"]) == 2
        sides.add(facts["dominant_side"])
        blocker_cases += bool(facts["vertical_blockers"])
        assert pair["output"] == family.dominant_relay_output(pair["input"])
    assert sides == {"left", "right"}
    assert blocker_cases >= 2


def test_first_query_is_substantive_30x30_stress(adapter, family):
    episode = adapter.generate(0, {"beam_mode": "dominant_relay"}, 2, 4)
    pair = episode["test"][0]
    grid, output = pair["input"], pair["output"]
    assert (len(grid), len(grid[0])) == (30, 30)
    facts = family.analyze_input(grid)
    assert len(facts["active_rows"]) == 4
    assert facts["dominant_count"] >= 27
    assert sum(cell != 0 for row in output for cell in row) >= 130
    assert any(cell != 0 for cell in output[0])
    assert any(cell != 0 for cell in output[-1])
    assert any(row[0] != 0 for row in output)
    assert any(row[-1] != 0 for row in output)
    halves = [
        any(output[r][c] != 0 for r in rr for c in cc)
        for rr in (range(0, 15), range(15, 30))
        for cc in (range(0, 15), range(15, 30))
    ]
    assert all(halves)


def test_claimed_labels_match_both_programs_in_protected_racket(adapter):
    with RacketBridge(timeout=20) as bridge:
        assert bridge.runtime_identity["backend"] == "racket"
        assert bridge.runtime_identity["protected"] is True
        for seed in (0, 17):
            for mode in ("horizontal_only", "dominant_relay"):
                episode = adapter.generate(seed, {"beam_mode": mode}, 3, 4)
                program = adapter.program({"beam_mode": mode})
                for pair in _pairs(episode):
                    assert _execute(bridge, program, pair["input"]) == pair["output"]


def test_public_projection_hides_private_fields_and_future_queries(adapter, family):
    episode = adapter.generate(5, {"beam_mode": "dominant_relay"}, 3, 4)
    public = family.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    assert b"dominant_relay" not in public_challenge_bytes(public)
    turn = family.public_turn(episode, 0)
    assert set(turn) == {"train", "test"}
    assert len(turn["test"]) == 1
    assert turn["test"][0] == public["test"][0]
    serialized = json.dumps(turn, sort_keys=True)
    assert "program_solution" not in serialized
    assert episode["test"][1]["input"] not in [pair["input"] for pair in turn["test"]]
    one = adapter.generate(5, {"beam_mode": "dominant_relay"}, 3, 1)
    assert family.public_turn(one, 0) == turn


def test_bounded_audit_executes_rivals_and_rejects_them(audit_module):
    report = audit_module.audit(seed=0, demos=3, queries=4)
    assert report["status"] == "pass"
    assert report["racket"]["backend"] == "racket"
    assert report["racket"]["protected"] is True
    assert report["scope"] == {
        "seed": 0,
        "demos": 3,
        "queries": 4,
        "settings": 2,
        "rivals": 5,
    }
    for row in report["settings"]:
        assert row["chosen_labels_match_racket"] is True
        assert all(not rival["fits_demonstrations"] for rival in row["rivals"].values())
        assert all(rival["query_differs"] for rival in row["rivals"].values())


def test_small_stress_sweep_checks_every_count_setting_and_public_turn(audit_module):
    report = audit_module.stress(seed_count=3)
    assert report["status"] == "pass"
    assert report["counts"] == {
        "seeds": 3,
        "episodes": 30,
        "visible_pairs": 240,
        "matched_input_comparisons": 15,
        "sequential_turns": 120,
    }
    assert report["failures"] == []
