from __future__ import annotations

import importlib.util
import json
from functools import cache
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root

TASK_ID = "01023c69fe3c"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID / "workspace" / "parametric"


def _load(path: Path, name: str):
    assert path.is_file(), f"missing {path.relative_to(ROOT)}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@cache
def prototype():
    return _load(HOME / "prototype.py", "_parametric_01023c69fe3c")


def _canonical_program() -> str:
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        if record.get("task_id") == TASK_ID:
            return record["program_solution"]
    raise AssertionError(TASK_ID)


def _witness_grid() -> list[list[int]]:
    grid = [[0 for _ in range(12)] for _ in range(9)]
    grid[2][3] = 2
    grid[6][8] = 2
    grid[3][5] = 4  # true cue inside the derived rectangle
    grid[1][5] = 7  # one-cell-ring decoy for the wrong intermediate
    for r, c in [(0, 0), (0, 1), (1, 0)]:
        grid[r][c] = 4
    for r, c in [(7, 9), (7, 10), (8, 9), (8, 10)]:
        grid[r][c] = 7
    grid[0][10] = 5
    grid[8][1] = 6
    return grid


def test_default_program_is_exact_canonical_and_cue_program_matches_racket():
    p = prototype()
    canonical = _canonical_program()
    assert p.program_for("canonical") == canonical
    alternate = p.program_for("interior_cue")
    assert alternate != canonical

    from arc_repl.racket_bridge import RacketBridge

    grid = _witness_grid()
    with RacketBridge() as bridge:
        for mode in p.MODES:
            expected = p.transform(grid, mode)
            assert p.execute(bridge, p.program_for(mode), grid) == expected


def _all_inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def _grid_digest(grid):
    return json.dumps(grid, sort_keys=True, separators=(",", ":"))


def test_episode_counts_matched_inputs_prefix_stability_and_substantive_30x30():
    p = prototype()
    canonical = p.generate_episode(17, "canonical", demos=2, queries=4)
    alternate = p.generate_episode(17, "interior_cue", demos=2, queries=4)

    assert _all_inputs(canonical) == _all_inputs(alternate)
    assert len(canonical["train"]) == len(alternate["train"]) == 2
    assert len(canonical["test"]) == len(alternate["test"]) == 4
    assert len({_grid_digest(grid) for grid in _all_inputs(canonical)}) == 6
    assert all(
        a["output"] != b["output"]
        for a, b in zip(canonical["train"], alternate["train"])
    )

    stress = next(
        pair["input"]
        for pair in canonical["test"]
        if (len(pair["input"]), len(pair["input"][0])) == (30, 30)
    )
    profile = p.scene_profile(stress)
    assert profile["anchor_span_rows"] >= 20
    assert profile["anchor_span_cols"] >= 20
    assert profile["nonzero_count"] >= 30
    assert len(profile["cue_candidates"]) == 1
    assert len(profile["payload"]) >= 6
    assert profile["ring_decoy_color"] != profile["cue_color"]

    one = p.generate_episode(17, "canonical", demos=6, queries=1)
    assert one["test"] == canonical["test"][:1]


def test_two_demo_lesson_refutes_relevant_bypasses_across_fresh_seeds():
    p = prototype()
    for seed in range(24):
        for mode in p.MODES:
            episode = p.generate_episode(seed, mode, demos=2, queries=4)
            certificate = p.certify(episode)
            assert certificate["survivors"] == [{"mode": mode}]
            assert certificate["all_rivals_refuted"] is True
            assert set(certificate["rivals_refuted"]) >= {
                "canonical_only",
                "interior_cue",
                "expanded_interior",
                "all_decor_payloads",
                "most_frequent_decor",
                "least_frequent_decor",
                "preserve_payload_color",
                "paint_cue_cells_too",
            }
        demo_cues = [
            p.scene_profile(p.sample_scene(seed, "demo", index))["cue_color"]
            for index in range(2)
        ]
        assert len(set(demo_cues)) == 2


def test_crossed_controls_change_only_the_intended_semantic_factor():
    p = prototype()
    grid = p.sample_scene(91, "demo", 0)
    base_output = p.transform(grid, "interior_cue")

    changed_intermediate = p.swap_cue_and_ring_colors(grid)
    assert p.scene_profile(changed_intermediate)["anchors"] == p.scene_profile(grid)["anchors"]
    assert p.scene_profile(changed_intermediate)["cue_color"] != p.scene_profile(grid)["cue_color"]
    assert p.transform(changed_intermediate, "interior_cue") != base_output

    nuisance_only = p.swap_nuisance_colors(grid)
    assert p.scene_profile(nuisance_only)["cue_color"] == p.scene_profile(grid)["cue_color"]
    assert p.transform(nuisance_only, "interior_cue") == base_output


def test_wrong_expanded_intermediate_matches_python_and_changes_final_racket_output():
    p = prototype()
    grid = _witness_grid()
    right = p.transform(grid, "interior_cue")
    wrong = p.wrong_intermediate_transform(grid)
    assert wrong != right
    assert p.wrong_intermediate_value(grid)["cue_color"] == 7

    from arc_repl.racket_bridge import RacketBridge

    with RacketBridge() as bridge:
        assert p.execute(bridge, p.wrong_intermediate_program(), grid) == wrong
        assert p.execute(bridge, p.program_for("interior_cue"), grid) == right


def test_strict_adapter_promotion_counts_and_bool_rejection():
    p = prototype()
    a = _load(HOME / "adapter.py", "_adapter_01023c69fe3c")
    promotion = json.loads((HOME / "promotion.json").read_text(encoding="utf-8"))
    assert promotion["default"] == {"mode": "canonical"}
    assert promotion["parameters"] == {"mode": ["canonical", "interior_cue"]}
    assert promotion["limits"] == {"demos": [2, 6], "queries": [1, 4]}
    assert a.program({"mode": "canonical"}) == p.program_for("canonical")
    episode = a.generate(8, {"mode": "interior_cue"}, 6, 4)
    assert len(episode["train"]) == 6 and len(episode["test"]) == 4
    assert episode["program_solution"] == a.program({"mode": "interior_cue"})

    for settings in ({}, {"mode": "canonical", "extra": 1}, {"mode": "bad"}, {"mode": 1}):
        with pytest.raises(ValueError):
            a.program(settings)
    for name, value in (("seed", True), ("demos", True), ("queries", True),
                        ("demos", 1), ("demos", 7), ("queries", 0), ("queries", 5)):
        args = {"seed": 0, "settings": {"mode": "canonical"}, "demos": 2, "queries": 4}
        args[name] = value
        with pytest.raises(ValueError):
            a.generate(**args)


def test_public_turn_hides_private_fields_future_queries_and_answers():
    import copy
    from reviewer_support import public_challenge_bytes, public_challenge_id

    p = prototype()
    episode = p.generate_episode(47, "interior_cue", demos=3, queries=4)
    first = p.public_turn(episode, 0)
    assert set(first) == {"train", "test"}
    assert len(first["test"]) == 1 and set(first["test"][0]) == {"input"}
    assert all(set(pair) == {"input", "output"} for pair in first["train"])
    before = public_challenge_bytes(first)
    identifier = public_challenge_id(first)

    changed = copy.deepcopy(episode)
    changed["settings"] = {"mode": "canonical"}
    changed["program_solution"] = "private"
    changed["test"][0]["output"] = [[9]]
    changed["test"][1:] = [{"input": [[9]], "output": [[8]]}]
    assert public_challenge_bytes(p.public_turn(changed, 0)) == before
    assert public_challenge_id(p.public_turn(changed, 0)) == identifier
    assert b"settings" not in before and b"program" not in before


def test_episode_verifier_rejects_corruption_duplicates_and_malformed_grids():
    import copy

    p = prototype()
    episode = p.generate_episode(61, "canonical", demos=2, queries=4)
    p.verify_episode(episode)

    corrupted = copy.deepcopy(episode)
    corrupted["train"][0]["output"] = [[0]]
    with pytest.raises(ValueError, match="label"):
        p.verify_episode(corrupted)

    duplicate = copy.deepcopy(episode)
    duplicate["test"][0]["input"] = copy.deepcopy(duplicate["train"][0]["input"])
    with pytest.raises(ValueError, match="distinct"):
        p.verify_episode(duplicate)

    malformed = copy.deepcopy(episode)
    malformed["test"][0]["input"][0][0] = True
    with pytest.raises(ValueError, match="grid"):
        p.verify_episode(malformed)


def test_expanded_selector_zone_contains_no_early_payload_before_ring_decoy():
    p = prototype()
    grid = p.sample_scene(0, "query", 2)
    profile = p.scene_profile(grid)
    wrong = p.wrong_intermediate_value(grid)
    assert wrong["candidates"][0][:2] == profile["ring_decoys"][0][:2]
    assert wrong["cue_color"] == profile["ring_decoy_color"]
    assert wrong["cue_color"] != profile["cue_color"]
    assert p.wrong_intermediate_transform(grid) != p.transform(grid, "interior_cue")


def test_crosshair_nuisance_stays_outside_wrong_expanded_selector_zone():
    p = prototype()
    grid = p.sample_scene(2, "demo", 0)
    profile = p.scene_profile(grid)
    wrong = p.wrong_intermediate_value(grid)
    assert wrong["candidates"][0][:2] == profile["ring_decoys"][0][:2]
    assert wrong["cue_color"] == profile["ring_decoy_color"]
    assert p.wrong_intermediate_transform(grid) != p.transform(grid, "interior_cue")


def test_adversarial_report_retains_every_repaired_failure_mode():
    audit = _load(HOME / "adversarial_probe.py", "_audit_report_01023c69fe3c")
    assert {row["regression"] for row in audit.FINDINGS_AND_REPAIRS} == {
        "test_crossed_controls_change_only_the_intended_semantic_factor",
        "test_two_demo_lesson_refutes_relevant_bypasses_across_fresh_seeds",
        "test_expanded_selector_zone_contains_no_early_payload_before_ring_decoy",
        "test_crosshair_nuisance_stays_outside_wrong_expanded_selector_zone",
    }
