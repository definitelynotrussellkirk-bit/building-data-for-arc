"""Focused tests for the proposed complete-rings -> ray-hit -> cross family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from reviewer_support import canonical_path, find_root


ROOT = find_root(__file__)
HOME = Path(__file__).resolve().parents[1] / "workspace" / "parametric"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_native_adapter_and_contract_are_present_and_finite():
    adapter_path = HOME / "adapter.py"
    promotion_path = HOME / "promotion.json"
    assert adapter_path.is_file()
    assert promotion_path.is_file()
    adapter = _load("d253_cross_adapter", adapter_path)
    assert callable(adapter.program)
    assert callable(adapter.generate)
    contract = json.loads(promotion_path.read_text(encoding="utf-8"))
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/d2534264df36/workspace/parametric/adapter.py",
        "parameters": {
            "cross_stop": ["complete_only", "nearest_hit", "farthest_hit"]
        },
        "default": {"cross_stop": "complete_only"},
        "limits": {"demos": [2, 6], "queries": [4, 8]},
    }


def _canonical_program() -> str:
    ledger = canonical_path(ROOT)
    programs = set()
    for line in ledger.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == "d2534264df36":
            programs.add(row["program_solution"])
    assert len(programs) == 1
    return programs.pop()


def test_programs_preserve_exact_default_and_reject_bad_settings():
    import pytest

    adapter = _load("d253_cross_adapter_programs", HOME / "adapter.py")
    canonical = _canonical_program()
    assert adapter.program({"cross_stop": "complete_only"}) == canonical
    nearest = adapter.program({"cross_stop": "nearest_hit"})
    farthest = adapter.program({"cross_stop": "farthest_hit"})
    assert nearest != canonical
    assert farthest != canonical
    assert nearest != farthest
    assert nearest.startswith("(rule!") and nearest.endswith(")")
    assert farthest.startswith("(rule!") and farthest.endswith(")")
    for mode, source in (
        ("complete_only", canonical),
        ("nearest_hit", nearest),
        ("farthest_hit", farthest),
    ):
        materialized = HOME / "rules" / f"{mode}.rkt"
        assert materialized.read_text(encoding="utf-8") == source
    for bad in (
        None,
        {},
        {"cross_stop": "unknown"},
        {"cross_stop": "complete_only", "extra": 1},
    ):
        with pytest.raises((TypeError, ValueError)):
            adapter.program(bad)


def _nonzero_positions(grid):
    return {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    }


def test_step_a_creates_ray_hits_that_control_substantive_step_b():
    prototype = _load("d253_cross_prototype_oracle", HOME / "prototype.py")
    oracle = _load("d253_cross_oracle", HOME / "oracle.py")
    grid = prototype.build_input(12345, 0)
    hub = len(grid) // 2
    assert all(grid[row][hub] == 0 for row in range(len(grid)))
    assert all(grid[hub][col] == 0 for col in range(len(grid[0])))

    completed = oracle.complete_rings(grid)
    nearest = oracle.ray_intermediate(completed, "nearest_hit")
    farthest = oracle.ray_intermediate(completed, "farthest_hit")
    assert nearest["hit_row"] > farthest["hit_row"]
    assert nearest["hit_color"] != farthest["hit_color"]
    assert nearest["hub"] == hub == farthest["hub"]

    near_output = oracle.solve(grid, "nearest_hit")
    far_output = oracle.solve(grid, "farthest_hit")
    assert near_output != completed
    assert far_output != completed
    assert near_output != far_output
    for row, col in _nonzero_positions(completed):
        assert near_output[row][col] == completed[row][col]
        assert far_output[row][col] == completed[row][col]
    assert len(_nonzero_positions(near_output) - _nonzero_positions(completed)) >= 9
    assert len(_nonzero_positions(far_output) - _nonzero_positions(completed)) >= 17

    # The skip-A counterfactual has no ray hit on the raw source and therefore
    # cannot choose the cross extent or color.
    assert oracle.skip_a_solve(grid, "nearest_hit") == grid
    assert oracle.skip_a_solve(grid, "farthest_hit") == grid


def _freeze(grid):
    return tuple(tuple(row) for row in grid)


def test_generate_is_matched_deterministic_distinct_and_boundary_covering():
    adapter = _load("d253_cross_adapter_generate", HOME / "adapter.py")
    prototype = _load("d253_cross_prototype_generate", HOME / "prototype.py")
    oracle = _load("d253_cross_oracle_generate", HOME / "oracle.py")

    episodes = {
        mode: adapter.generate(71, {"cross_stop": mode}, demos=2, queries=4)
        for mode in prototype.MODES
    }
    all_inputs = [
        [pair["input"] for pair in episode["train"] + episode["test"]]
        for episode in episodes.values()
    ]
    assert all_inputs[1:] == all_inputs[:-1]
    assert [len(grid) for grid in all_inputs[0]] == [19, 19, 23, 27, 30, 19]
    assert len({_freeze(grid) for grid in all_inputs[0]}) == 6

    # Minimum teaching examples deliberately share the same size and expose
    # singleton row, singleton column, and paired witnesses.
    for sample_index in (0, 1):
        metadata = prototype.input_metadata(71, sample_index)
        assert metadata["size"] == 19
        assert sorted(mode for mode in metadata["witness_modes"] if mode) == [
            "pair",
            "single_col",
            "single_row",
        ]

    for selected, episode in episodes.items():
        assert set(episode) == {"train", "test", "program_solution"}
        assert len(episode["train"]) == 2
        assert len(episode["test"]) == 4
        assert episode["program_solution"] == adapter.program({"cross_stop": selected})
        for pair in episode["train"] + episode["test"]:
            assert set(pair) == {"input", "output"}
            assert pair["output"] == oracle.solve(pair["input"], selected)
        survivors = [
            candidate
            for candidate in prototype.MODES
            if all(
                oracle.solve(pair["input"], candidate) == pair["output"]
                for pair in episode["train"]
            )
        ]
        assert survivors == [selected]

    # Independent maximum counts remain supported, distinct, and bounded.
    maximum = adapter.generate(
        83, {"cross_stop": "nearest_hit"}, demos=6, queries=8
    )
    maximum_inputs = [
        pair["input"] for pair in maximum["train"] + maximum["test"]
    ]
    assert len(maximum_inputs) == 14
    assert len({_freeze(grid) for grid in maximum_inputs}) == 14
    assert {19, 23, 27, 30} <= {len(grid) for grid in maximum_inputs}
    assert all(
        1 <= len(grid) <= 30
        and 1 <= len(grid[0]) <= 30
        and all(type(cell) is int for row in grid for cell in row)
        for grid in maximum_inputs
    )


def test_generate_validates_counts_seed_and_private_projection():
    import pytest
    from reviewer_support import public_challenge_bytes

    adapter = _load("d253_cross_adapter_validation", HOME / "adapter.py")

    for bad_seed in (True, -1, 2**63, 1.5, "71"):
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(bad_seed, {"cross_stop": "complete_only"}, 2, 4)
    for bad_demos in (True, 1, 7, 2.0, "2"):
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(0, {"cross_stop": "complete_only"}, bad_demos, 4)
    for bad_queries in (False, 3, 9, 4.0, "4"):
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(0, {"cross_stop": "complete_only"}, 2, bad_queries)
    for bad_settings in (
        None,
        {},
        {"cross_stop": "unknown"},
        {"cross_stop": "nearest_hit", "extra": 1},
    ):
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(0, bad_settings, 2, 4)

    episode = adapter.generate(83, {"cross_stop": "farthest_hit"}, 2, 4)
    public = json.loads(public_challenge_bytes(episode))
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    serialized = json.dumps(public, sort_keys=True)
    assert "cross_stop" not in serialized
    assert "farthest_hit" not in serialized
    assert "program_solution" not in serialized


def test_protected_racket_matches_independent_oracle_at_19_and_30():
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    adapter = _load("d253_cross_adapter_racket", HOME / "adapter.py")
    oracle = _load("d253_cross_oracle_racket", HOME / "oracle.py")
    grids = [
        adapter.generate(71, {"cross_stop": "complete_only"}, 2, 4)["train"][0]["input"],
        adapter.generate(71, {"cross_stop": "complete_only"}, 2, 4)["test"][2]["input"],
    ]
    assert [len(grid) for grid in grids] == [19, 30]

    with RacketBridge(timeout=30, max_calls_before_restart=32) as bridge:
        for index, grid in enumerate(grids):
            name = f"d253_cross_{index}"
            bridge.define_grid(name, grid)
            for mode in ("complete_only", "nearest_hit", "farthest_hit"):
                source = wrap_rule(adapter.program({"cross_stop": mode}))
                actual = bridge.eval_text(f"({source} {name})")
                assert actual == oracle.solve(grid, mode)
        assert bridge.runtime_identity["protected"] is True


def test_minimum_demos_reject_pair_axis_and_cross_shortcuts():
    prototype = _load("d253_cross_prototype_rivals", HOME / "prototype.py")
    rivals = _load("d253_cross_rivals", HOME / "rivals.py")

    rival_names = (
        "paired_only",
        "row_axis_only",
        "column_axis_only",
        "fixed_middle_hit",
        "corner_color_cross",
    )
    for selected in prototype.MODES:
        episode = prototype.generate(71, {"cross_stop": selected}, 2, 4)
        reports = rivals.audit_episode(episode, selected, rival_names=rival_names)
        assert [row["name"] for row in reports] == list(rival_names)
        for report in reports:
            assert report["fits_all_demos"] is False
            assert report["demo_mismatch_indices"]
            assert report["query_mismatch_indices"]


def test_rival_completion_shortcuts_fail_on_the_intended_singleton_morphology():
    prototype = _load("d253_cross_prototype_rival_morph", HOME / "prototype.py")
    oracle = _load("d253_cross_oracle_rival_morph", HOME / "oracle.py")
    rivals = _load("d253_cross_rivals_morph", HOME / "rivals.py")
    grid = prototype.build_input(71, 0)
    metadata = prototype.input_metadata(71, 0)
    canonical = oracle.complete_rings(grid)

    paired = rivals.restricted_completion(grid, "paired_only")
    row_only = rivals.restricted_completion(grid, "row_axis_only")
    column_only = rivals.restricted_completion(grid, "column_axis_only")
    assert paired != canonical
    assert row_only != canonical
    assert column_only != canonical

    for ring_index, witness_mode in enumerate(metadata["witness_modes"]):
        ring = 1 + 2 * ring_index
        hub = metadata["hub"]
        expected_color = metadata["side_colors"][ring_index]
        assert canonical[ring][hub] == expected_color
        if witness_mode == "single_row":
            assert paired[ring][hub] != expected_color
            assert row_only[ring][hub] == expected_color
            assert column_only[ring][hub] != expected_color
        elif witness_mode == "single_col":
            assert paired[ring][hub] != expected_color
            assert row_only[ring][hub] != expected_color
            assert column_only[ring][hub] == expected_color
        elif witness_mode == "pair":
            assert paired[ring][hub] == expected_color
            assert row_only[ring][hub] == expected_color
            assert column_only[ring][hub] == expected_color


def test_skip_a_counterfactual_program_is_executable_and_changes_the_final_output():
    import pytest
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    prototype = _load("d253_cross_prototype_skip_a", HOME / "prototype.py")
    oracle = _load("d253_cross_oracle_skip_a", HOME / "oracle.py")
    grid = prototype.build_input(71, 4)  # exact 30x30 boundary query
    assert len(grid) == 30

    with pytest.raises(ValueError):
        prototype.skip_a_program("complete_only")
    with RacketBridge(timeout=30, max_calls_before_restart=16) as bridge:
        bridge.define_grid("d253_skip_a_grid", grid)
        for mode in ("nearest_hit", "farthest_hit"):
            selected_program = prototype.program({"cross_stop": mode})
            counterfactual_program = prototype.skip_a_program(mode)
            selected = bridge.eval_text(
                f"({wrap_rule(selected_program)} d253_skip_a_grid)"
            )
            counterfactual = bridge.eval_text(
                f"({wrap_rule(counterfactual_program)} d253_skip_a_grid)"
            )
            assert selected == oracle.solve(grid, mode)
            assert counterfactual == oracle.skip_a_solve(grid, mode) == grid
            assert selected != counterfactual


def _synthetic_native_execution(prototype, seed=71, demos=3, queries=4):
    episodes = []
    checks = []
    for mode in prototype.MODES:
        settings = {"cross_stop": mode}
        episode = prototype.generate(seed, settings, demos, queries)
        episodes.append(
            {
                **episode,
                "seed": seed,
                "settings": settings,
                "program": episode["program_solution"],
                "task_id": "d2534264df36",
            }
        )
        checks.append(
            {
                "seed": seed,
                "settings": settings,
                "counts": {"demos": demos, "queries": queries},
                "survivors": [settings],
                "label_count": demos + queries,
            }
        )
    return {
        "episodes": episodes,
        "checks": checks,
        "racket": {"backend": "racket", "protected": True},
        "racket_evaluations": len(episodes) * (demos + queries),
    }


def test_evidence_tool_builds_finite_shortcut_audit_from_native_shape():
    import pytest

    prototype = _load("d253_cross_prototype_evidence", HOME / "prototype.py")
    tools = _load("d253_cross_evidence_tools", HOME / "evidence_tools.py")
    execution = _synthetic_native_execution(prototype)
    report = tools.audit_from_execution(execution, seed=71, demos=2, queries=4)

    assert report["schema"] == "d2534264df36-cross-stop-self-audit-v1"
    assert report["racket"] == {"backend": "racket", "protected": True}
    assert report["counts"] == {"settings": 3, "demos_used": 2, "queries_used": 4, "rivals": 5}
    assert [row["selected_mode"] for row in report["settings"]] == list(prototype.MODES)
    assert all(row["declared_survivors"] == [{"cross_stop": row["selected_mode"]}]
               for row in report["settings"])
    assert all(
        not rival["fits_all_demos"]
        for row in report["settings"]
        for rival in row["rivals"]
    )

    execution["racket"] = {"backend": "python", "protected": False}
    with pytest.raises(ValueError, match="protected Racket"):
        tools.audit_from_execution(execution, seed=71, demos=2, queries=4)


def test_evidence_tool_builds_source_bound_skip_a_witness():
    import hashlib

    prototype = _load("d253_cross_prototype_witness_tool", HOME / "prototype.py")
    tools = _load("d253_cross_evidence_witness_tool", HOME / "evidence_tools.py")
    execution = _synthetic_native_execution(prototype)
    programs = {}
    for mode in prototype.MODES:
        settings = {"cross_stop": mode}
        key = json.dumps(settings, sort_keys=True, separators=(",", ":"))
        programs[key] = hashlib.sha256(prototype.program(settings).encode()).hexdigest()
    qualification = {
        "source_binding": {"task_id": "d2534264df36", "files": [{"path": "dummy", "sha256": "0" * 64}]},
        "programs": programs,
    }

    witness, replay = tools.build_sequential_witness(
        qualification,
        execution,
        seed=71,
        sample_index=4,
        modes=("nearest_hit", "farthest_hit"),
    )
    assert witness["schema"] == "arcpuzzles-sequential-dependency-witness-v1"
    assert witness["source_binding"] == qualification["source_binding"]
    assert witness["racket"] == {"backend": "racket", "protected": True}
    assert len(witness["cases"]) == 2
    assert [len(case["input"]) for case in witness["cases"]] == [30, 30]
    assert all(case["ablation"] == "skip_a" for case in witness["cases"])
    assert all(case["output"] != case["counterfactual_output"] for case in witness["cases"])
    assert replay["protected"] is True
    assert replay["evaluations"] == 4
