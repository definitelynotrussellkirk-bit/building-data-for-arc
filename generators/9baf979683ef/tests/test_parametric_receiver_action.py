"""Focused contract for the divider-mirror receiver-action family."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import random
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from arcpuzzles import Catalog
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import find_root, public_challenge_bytes


TASK_ID = "9baf979683ef"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID / "workspace" / "parametric"


def _load(name: str):
    path = HOME / f"{name}.py"
    assert path.is_file(), f"missing parametric source: {path}"
    spec = importlib.util.spec_from_file_location(f"receiver_action_{name}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical() -> str:
    record = Catalog(ROOT).get(TASK_ID)
    programs = {
        variant["program_solution"]
        for variant in record["variants"]
        if isinstance(variant.get("program_solution"), str)
    }
    assert len(programs) == 1
    return next(iter(programs))


def _apply(bridge: RacketBridge, program: str, grid: list[list[int]]) -> list[list[int]]:
    literal = "'(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in grid
    ) + ")"
    return bridge.eval_text(f"({wrap_rule(program)} {literal})")


def _inputs(episode: dict) -> list[list[list[int]]]:
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_default_program_is_byte_exact_and_setting_validation_is_closed() -> None:
    adapter = _load("adapter")
    canonical = _canonical()
    assert adapter.program({"receiver_action": "preserve"}) == canonical
    alternate = adapter.program({"receiver_action": "absorb_color"})
    assert alternate != canonical
    assert "intermediate" in alternate
    assert "obj-cells" in alternate

    bad = (
        {},
        {"receiver_action": "other"},
        {"receiver_action": True},
        {"receiver_action": "preserve", "extra": 1},
        [],
    )
    for settings in bad:
        with pytest.raises((TypeError, ValueError)):
            adapter.program(settings)
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(0, settings, 3, 4)


def test_minimum_two_demos_identify_each_setting_and_refute_declared_rivals() -> None:
    adapter = _load("adapter")
    proto = _load("prototype")
    for seed in (0, 17, 63):
        for action in ("preserve", "absorb_color"):
            episode = adapter.generate(seed, {"receiver_action": action}, 2, 4)
            report = proto.teaching_report(episode["train"], episode["test"], action)
            assert report["selected_setting"] == action
            assert report["surviving_settings"] == [action]
            assert report["query_ambiguities"] == []
            assert report["surviving_rivals"] == []
            assert report["tested_rivals"] == [
                "all_receivers",
                "contact_cell_only",
                "fixed_color_two",
                "largest_receiver",
                "leftmost_receiver",
                "nearest_divider",
                "smallest_receiver",
            ]


def test_counts_are_independent_inputs_are_matched_and_first_query_is_stable() -> None:
    adapter = _load("adapter")
    full = adapter.generate(31, {"receiver_action": "absorb_color"}, 6, 4)
    minimum = adapter.generate(31, {"receiver_action": "absorb_color"}, 2, 1)
    canonical = adapter.generate(31, {"receiver_action": "preserve"}, 6, 4)

    assert minimum["train"] == full["train"][:2]
    assert minimum["test"] == full["test"][:1]
    assert _inputs(full) == _inputs(canonical)
    assert [pair["output"] for pair in full["train"]] != [
        pair["output"] for pair in canonical["train"]
    ]
    assert len({json.dumps(grid, separators=(",", ":")) for grid in _inputs(full)}) == 10
    assert public_challenge_bytes({"train": minimum["train"], "test": minimum["test"]}) == public_challenge_bytes(minimum)


def test_request_validation_determinism_freshness_and_global_rng_purity() -> None:
    adapter = _load("adapter")
    settings = {"receiver_action": "preserve"}
    for args in (
        (True, settings, 3, 4),
        (-1, settings, 3, 4),
        (2**63, settings, 3, 4),
        (0, settings, 1, 4),
        (0, settings, 7, 4),
        (0, settings, True, 4),
        (0, settings, 3, 0),
        (0, settings, 3, 5),
        (0, settings, 3, 1.0),
    ):
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(*args)

    random.seed(20261024)
    before = random.getstate()
    first = adapter.generate(91, settings, 4, 4)
    second = adapter.generate(91, settings, 4, 4)
    assert first == second
    assert random.getstate() == before
    first["train"][0]["input"][0][0] = 9
    assert first != second


def test_scene_grammar_varies_target_rank_and_has_substantive_boundary_stress() -> None:
    adapter = _load("adapter")
    proto = _load("prototype")
    episode = adapter.generate(41, {"receiver_action": "absorb_color"}, 6, 4)

    observations = [proto.observables(grid) for grid in _inputs(episode)]
    assert all(proto.domain_errors(grid) == [] for grid in _inputs(episode))
    first_two = observations[:2]
    assert {row["target_size_rank"] for row in first_two} == {"largest", "smallest"}
    assert {row["target_horizontal_rank"] for row in first_two} == {"leftmost", "rightmost"}
    assert all(row["receiver_count"] >= 3 for row in observations)
    assert all(row["contact_color"] not in (0, 5, 9) for row in observations)
    assert len({row["contact_color"] for row in observations[:6]}) >= 3

    stress = episode["test"][3]["input"]
    stress_obs = proto.observables(stress)
    assert len(stress) == len(stress[0]) == 30
    assert stress_obs["touches_right_boundary"] is True
    assert stress_obs["source_count"] >= 24
    assert stress_obs["receiver_count"] >= 4
    assert stress_obs["target_size"] >= 8


def test_python_claims_match_protected_racket_for_both_programs() -> None:
    adapter = _load("adapter")
    proto = _load("prototype")
    grids = _inputs(adapter.generate(7, {"receiver_action": "preserve"}, 2, 2))
    with RacketBridge(max_calls_before_restart=64) as bridge:
        for action in ("preserve", "absorb_color"):
            settings = {"receiver_action": action}
            program = adapter.program(settings)
            for grid in grids:
                assert _apply(bridge, program, grid) == proto.transform(grid, action)


def test_causal_witness_changes_under_skip_a_and_wrong_intermediate() -> None:
    proto = _load("prototype")
    witness = proto.causal_witness(seed=0)
    assert witness["step_a"] == "mirror every left-side source cell across the divider"
    assert witness["step_b"] == "recolor the contacted receiver component with the adjacent mirrored color"
    assert witness["final_output"] != witness["skip_a_output"]
    assert witness["final_output"] != witness["wrong_intermediate_output"]
    assert witness["intermediate"] != witness["input"]
    assert witness["selected_receiver_cells"]


def test_public_projection_hides_settings_program_and_query_answers() -> None:
    adapter = _load("adapter")
    proto = _load("prototype")
    episode = adapter.generate(12, {"receiver_action": "absorb_color"}, 3, 4)
    public = proto.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    raw = public_challenge_bytes(public).decode("utf-8")
    for forbidden in ("receiver_action", "absorb_color", "program_solution", "seed", "query_answers"):
        assert forbidden not in raw

    changed = copy.deepcopy(episode)
    changed["program_solution"] = "private replacement"
    changed["settings"] = {"receiver_action": "secret"}
    changed["test"][0]["output"] = [[9]]
    assert public_challenge_bytes(proto.public_challenge(changed)) == public_challenge_bytes(public)


def test_audit_writes_source_bound_protected_racket_evidence(tmp_path: Path) -> None:
    audit = _load("audit")
    destination = tmp_path / "evidence"
    result = audit.run_audit(destination, seeds=(0, 1), racket_seeds=(0,))

    assert result["schema"] == "arcpuzzles-receiver-action-audit-v1"
    assert result["task_id"] == TASK_ID
    assert result["status"] == "pass"
    assert result["bounded_sweep"] == {
        "seed_count": 2,
        "episode_count": 4,
        "teaching_checks": 20,
        "labeled_pairs": 40,
        "failures": [],
    }
    assert result["protected_racket"]["seed_count"] == 1
    assert result["protected_racket"]["label_evaluations"] == 20
    assert result["protected_racket"]["causal_evaluations"] == 4
    assert result["protected_racket"]["failures"] == []

    expected = {
        "summary.json",
        "sweep.json",
        "protected-racket.json",
        "causal-witness.json",
        "public-projection.json",
        "sources.json",
    }
    assert expected <= {path.name for path in destination.iterdir() if path.is_file()}
    sources = json.loads((destination / "sources.json").read_text(encoding="utf-8"))
    source_paths = {row["path"] for row in sources["files"]}
    assert f"generators/{TASK_ID}/workspace/parametric/audit.py" in source_paths
    assert f"generators/{TASK_ID}/workspace/parametric/prototype.py" in source_paths
    assert f"generators/{TASK_ID}/generator.py" in source_paths
    assert all(len(row["sha256"]) == 64 and row["bytes"] > 0 for row in sources["files"])

    causal = json.loads((destination / "causal-witness.json").read_text(encoding="utf-8"))
    assert causal["protected_racket"]["step_a_output"] == causal["intermediate"]
    assert causal["protected_racket"]["full_output"] == causal["final_output"]
    assert causal["protected_racket"]["skip_a_output"] != causal["final_output"]
    assert causal["protected_racket"]["wrong_intermediate_output"] != causal["final_output"]

    public = json.loads((destination / "public-projection.json").read_text(encoding="utf-8"))
    assert public["count"] == 4
    assert len(public["ids"]) == 4
    for identifier in public["ids"]:
        payload = destination / "public" / f"{identifier}.json"
        assert payload.is_file()
        assert hashlib.sha256(payload.read_bytes()).hexdigest() == identifier

    with pytest.raises(FileExistsError):
        audit.run_audit(destination, seeds=(0,), racket_seeds=())
