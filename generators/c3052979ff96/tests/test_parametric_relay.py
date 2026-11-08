"""Native causal relay family for c3052979ff96."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import random

import pytest


HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]
SETTINGS = ("rotation_only", "relay_hit_color")


def adapter():
    source = HOME / "workspace/parametric/adapter.py"
    spec = importlib.util.spec_from_file_location(
        "_c3052979ff96_parametric_relay_test", source
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load adapter from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def racket():
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    # Portable task-test snapshots intentionally omit the vendor tarball and
    # compiled bank-helper cache.  This family uses only core ARC primitives,
    # so skip the unrelated generated bank helper file; otherwise a cold
    # isolated runtime spends minutes compiling it before the first assertion.
    with pytest.MonkeyPatch.context() as patch:
        patch.setenv("ARC_REPL_SKIP_BANK_HELPERS", "1")
        with RacketBridge(timeout=10) as bridge:
            assert bridge.runtime_identity["backend"] == "racket"
            assert bridge.runtime_identity["protected"] is True

            def apply(program, grid):
                bridge.define_grid("c305-parametric-test-grid", grid)
                return bridge.eval_text(
                    "(" + wrap_rule(program) + " c305-parametric-test-grid)"
                )

            yield apply


def _settings(mode: str) -> dict[str, str]:
    return {"rule_mode": mode}


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_default_program_is_exact_canonical_authority():
    programs = {
        row["program_solution"]
        for line in (ROOT / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()
        if (row := json.loads(line))["task_id"] == "c3052979ff96"
    }
    module = adapter()
    assert programs == {module.program(_settings("rotation_only"))}
    assert module.program(_settings("relay_hit_color")) not in programs


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_inputs_are_setting_neutral_deterministic_distinct_and_rng_local(demos):
    module = adapter()
    before = random.getstate()
    canonical = module.generate(17, _settings("rotation_only"), demos, 4)
    relay = module.generate(17, _settings("relay_hit_color"), demos, 4)
    assert _inputs(canonical) == _inputs(relay)
    assert canonical == module.generate(17, _settings("rotation_only"), demos, 4)
    assert random.getstate() == before
    assert len(canonical["train"]) == demos
    assert len(canonical["test"]) == 4
    visible = [json.dumps(grid, separators=(",", ":")) for grid in _inputs(canonical)]
    assert len(visible) == len(set(visible)) == demos + 4


def test_two_demos_identify_both_settings_against_declared_rivals():
    module = adapter()
    for mode in SETTINGS:
        episode = module.generate(91, _settings(mode), 2, 4)
        proof = module.certificate(
            episode["train"], [pair["input"] for pair in episode["test"]]
        )
        assert proof["survivors"] == [mode]
        assert proof["demos"] == 2
        assert proof["queries"] == 4
        assert {
            "relay_fixed_role_0",
            "relay_fixed_role_1",
            "relay_fixed_role_2",
            "relay_code_role",
            "relay_quadrant_role",
            "relay_largest_payload",
            "relay_all_colors",
            "relay_first_target_cell",
            "rotation_code_one_clockwise",
            "relay_code_one_clockwise",
        } <= set(proof["declared_hypotheses"])
        assert len(proof["predicted_query_sha256"]) == 4


def test_first_two_demos_force_rotation_before_payload_selection():
    module = adapter()
    episode = module.generate(123, _settings("relay_hit_color"), 2, 4)
    observed = [module.observe(pair["input"]) for pair in episode["train"]]
    assert [item["code"] for item in observed] == [1, 1]
    assert [item["source_quadrant"] for item in observed] == [2, 2]
    assert observed[0]["relay_color"] != observed[1]["relay_color"]
    assert observed[0]["cue_target_index"] != 0
    for pair, item in zip(episode["train"], observed, strict=True):
        canonical = module.transform(pair["input"], "rotation_only")
        assert pair["output"] == module.transform(pair["input"], "relay_hit_color")
        assert pair["output"] != canonical
        changed_payload = [
            [row, col]
            for row, values in enumerate(pair["input"])
            for col, value in enumerate(values)
            if (
                value == item["relay_color"]
                and [row, col] not in item["target"]
                and [row, col] != item["cue_cell"]
            )
        ]
        assert len(changed_payload) >= 2
        assert all(pair["output"][row][col] == 2 for row, col in changed_payload)



def test_identity_branch_uses_an_adjacent_cue_and_refutes_clockwise_shortcuts():
    module = adapter()
    for mode in SETTINGS:
        episode = module.generate(47, _settings(mode), 2, 4)
        proof = module.certificate(
            episode["train"], [pair["input"] for pair in episode["test"]]
        )
        assert proof["survivors"] == [mode]
        for pair in episode["train"][:2]:
            observed = module.observe(pair["input"])
            assert observed["code"] == 1
            assert observed["target"] == observed["source"]
            assert observed["cue_cell"] not in observed["target"]
            target = observed["target"][observed["cue_target_index"]]
            cue = observed["cue_cell"]
            assert abs(target[0] - cue[0]) + abs(target[1] - cue[1]) == 1
            assert module.predict(pair["input"], mode) == pair["output"]
            rival = (
                "rotation_code_one_clockwise"
                if mode == "rotation_only"
                else "relay_code_one_clockwise"
            )
            assert module.predict(pair["input"], rival) != pair["output"]

def test_four_queries_cover_codes_colors_boundaries_and_30x30_stress():
    module = adapter()
    episode = module.generate(7, _settings("relay_hit_color"), 3, 4)
    observed = [module.observe(pair["input"]) for pair in episode["test"]]
    assert {item["code"] for item in observed} == {1, 2, 3, 4}
    assert len({item["relay_color"] for item in observed}) == 3

    grid = episode["test"][-1]["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    occupied = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    assert min(row for row, _ in occupied) == 0
    assert max(row for row, _ in occupied) == 29
    assert min(col for _, col in occupied) == 0
    assert max(col for _, col in occupied) == 29
    assert len(occupied) >= 35
    assert sum(cell == 2 for row in episode["test"][-1]["output"] for cell in row) >= 10


@pytest.mark.parametrize("mode", SETTINGS)
def test_generated_claim_labels_match_protected_racket(mode, racket):
    module = adapter()
    episode = module.generate(5, _settings(mode), 2, 4)
    selected_program = module.program(_settings(mode))
    for pair in episode["train"] + episode["test"]:
        assert racket(selected_program, pair["input"]) == pair["output"]


@pytest.mark.parametrize(
    "seed,settings,demos,queries",
    [
        (True, _settings("rotation_only"), 2, 4),
        (-1, _settings("rotation_only"), 2, 4),
        (0, {"rule_mode": "wrong"}, 2, 4),
        (0, {"rule_mode": "rotation_only", "extra": 1}, 2, 4),
        (0, _settings("rotation_only"), 1, 4),
        (0, _settings("rotation_only"), 7, 4),
        (0, _settings("rotation_only"), 2, 3),
        (0, _settings("rotation_only"), 2, 5),
        (0, _settings("rotation_only"), 2, True),
    ],
)
def test_invalid_requests_fail_explicitly(seed, settings, demos, queries):
    with pytest.raises(ValueError):
        adapter().generate(seed, settings, demos, queries)


def test_observer_rejects_boolean_cells_missing_cue_and_duplicate_target_cues():
    module = adapter()
    grid = module.generate(13, _settings("rotation_only"), 2, 4)["train"][0]["input"]

    boolean = [row[:] for row in grid]
    boolean[0][0] = False
    with pytest.raises(ValueError):
        module.observe(boolean)

    observed = module.observe(grid)
    missing = [row[:] for row in grid]
    cue_row, cue_col = observed["cue_cell"]
    missing[cue_row][cue_col] = 0
    with pytest.raises(ValueError):
        module.observe(missing)

    duplicate = [row[:] for row in grid]
    target_set = {tuple(point) for point in observed["target"]}
    other = next(
        (row, col)
        for target_row, target_col in target_set
        for row, col in (
            (target_row + 1, target_col),
            (target_row - 1, target_col),
            (target_row, target_col + 1),
            (target_row, target_col - 1),
        )
        if 0 <= row < len(grid)
        and 0 <= col < len(grid[0])
        and (row, col) not in target_set
        and [row, col] != observed["cue_cell"]
        and duplicate[row][col] == 0
    )
    duplicate[other[0]][other[1]] = next(
        color for color in (5, 6, 7) if color != observed["relay_color"]
    )
    with pytest.raises(ValueError):
        module.observe(duplicate)


def test_bounded_audit_covers_demo_counts_settings_and_declared_rivals():
    source = HOME / "workspace/parametric/audit.py"
    spec = importlib.util.spec_from_file_location(
        "_c3052979ff96_parametric_audit_test", source
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load audit from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    report = module.build_report(seeds=4)
    assert report["status"] == "passed"
    assert report["episodes"] == 4 * 3 * 2
    assert report["settings"] == list(SETTINGS)
    assert report["demo_counts"] == [2, 3, 6]
    assert report["setting_neutral_input_checks"] == 4 * 3
    assert report["unique_survivor_checks"] == 4 * 3 * 2
    assert report["query_30x30_checks"] == 4 * 3 * 2
    assert set(report["query_codes"]) == {1, 2, 3, 4}
    assert set(report["query_relay_colors"]) == {5, 6, 7}


def test_stress_payload_slides_along_top_edge_instead_of_inward_when_blocked():
    module = adapter()
    grid = module.generate(11, _settings("rotation_only"), 2, 4)["test"][-1]["input"]
    occupied = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    assert min(row for row, _ in occupied) == 0
    assert max(row for row, _ in occupied) == 29
    assert min(col for _, col in occupied) == 0
    assert max(col for _, col in occupied) == 29
