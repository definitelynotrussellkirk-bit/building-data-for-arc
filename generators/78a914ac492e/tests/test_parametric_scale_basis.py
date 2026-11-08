"""Prototype-only tests for the proposed scale-basis rule parameter."""
from __future__ import annotations

from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"
sys.path.insert(0, str(PARAMETRIC))


def test_default_program_is_exact_canonical_and_alternate_is_distinct():
    import prototype

    canonical = prototype.canonical_program()
    assert prototype.program_for("longer_side") == canonical
    assert prototype.program_for("shorter_side") != canonical
    with pytest.raises(ValueError, match="scale_basis"):
        prototype.program_for("diagonal")


def _asymmetric_seed_fixture():
    grid = [[0 for _ in range(14)] for _ in range(14)]
    # Non-rectangular template: common 2 plus accent L in color 8.
    grid[0][10] = 2
    grid[0][11] = 8
    grid[1][10] = 8
    grid[2][10] = 8
    # Seed: 2x3 common rectangle plus a 2x1 new-color rectangle.
    for row in (4, 5):
        for col in (1, 2, 3):
            grid[row][col] = 2
        grid[row][4] = 4
    return grid


def test_python_rules_use_longer_or_shorter_seed_side():
    import prototype

    grid = _asymmetric_seed_fixture()
    longer = prototype.apply_python(grid, "longer_side")
    shorter = prototype.apply_python(grid, "shorter_side")

    assert longer != shorter
    # Longer-side scale is 3: common 3x3 and each accent template cell 3x3.
    assert longer[6][3] == 2
    assert longer[6][6] == 4
    assert longer[12][3] == 4
    # Shorter-side scale is 2; cells outside the 2x-scaled stamp are cleared.
    assert shorter[5][2] == 2
    assert shorter[5][4] == 4
    assert shorter[9][2] == 4
    assert shorter[6][3] == 0
    assert shorter[12][3] == 0
    # The template itself remains visible in both outputs.
    assert longer[0][10:12] == [2, 8]
    assert shorter[0][10:12] == [2, 8]


def test_both_materialized_rules_match_python_on_asymmetric_fixture():
    import prototype

    grid = _asymmetric_seed_fixture()
    for setting in prototype.ALLOWED_SETTINGS:
        assert prototype.execute_racket(grid, setting) == prototype.apply_python(grid, setting)


def _all_inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_episode_holds_one_setting_and_uses_matched_inputs():
    import prototype

    longer = prototype.build_episode(1201, scale_basis="longer_side", demos=2, queries=4)
    shorter = prototype.build_episode(1201, scale_basis="shorter_side", demos=2, queries=4)

    assert longer["parameter"] == {"scale_basis": "longer_side"}
    assert shorter["parameter"] == {"scale_basis": "shorter_side"}
    assert _all_inputs(longer) == _all_inputs(shorter)
    assert all(pair["setting"] == "longer_side" for pair in longer["train"] + longer["test"])
    assert all(pair["setting"] == "shorter_side" for pair in shorter["train"] + shorter["test"])
    assert all(
        left["output"] != right["output"]
        for left, right in zip(longer["train"] + longer["test"], shorter["train"] + shorter["test"])
    )


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_supported_demo_counts_keep_four_distinct_setting_sensitive_queries(demos):
    import prototype

    episode = prototype.build_episode(2200 + demos, scale_basis="shorter_side", demos=demos, queries=4)
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == 4
    inputs = _all_inputs(episode)
    serialized = {prototype.grid_digest(grid) for grid in inputs}
    assert len(serialized) == demos + 4
    assert all(pair["outputs_by_setting"]["longer_side"] != pair["outputs_by_setting"]["shorter_side"] for pair in episode["train"] + episode["test"])
    large = episode["test"][-1]
    assert (len(large["input"]), len(large["input"][0])) == (30, 30)
    assert (len(large["output"]), len(large["output"][0])) == (30, 30)
    assert any(value != 0 for value in large["output"][0])
    assert any(value != 0 for value in large["output"][-1])
    assert any(row[0] != 0 for row in large["output"])
    assert any(row[-1] != 0 for row in large["output"])


def test_episode_rejects_wrong_types_and_unsupported_counts():
    import prototype

    for bad_seed in (True, 1.5, "1"):
        with pytest.raises((TypeError, ValueError), match="seed"):
            prototype.build_episode(bad_seed, demos=3, queries=4)
    for bad_demos in (True, 1, 7):
        with pytest.raises((TypeError, ValueError), match="demos"):
            prototype.build_episode(1, demos=bad_demos, queries=4)
    for bad_queries in (True, 3, 5):
        with pytest.raises((TypeError, ValueError), match="queries"):
            prototype.build_episode(1, demos=3, queries=bad_queries)


def test_public_projection_hides_private_fields_and_supports_sequential_reveal():
    import json
    import prototype

    episode = prototype.build_episode(3301, scale_basis="longer_side", demos=3, queries=4)
    public = prototype.public_challenge(episode)
    turns = prototype.public_turns(episode)

    assert len(public["train"]) == 3
    assert len(public["test"]) == 4
    assert len(turns) == 4
    assert all(len(turn["test"]) == 1 for turn in turns)
    assert turns[0] == prototype.single_query_challenge(episode, 0)
    assert turns[0]["test"][0] == public["test"][0]
    visible = json.dumps(public, sort_keys=True)
    assert "scale_basis" not in visible
    assert "longer_side" not in visible
    assert "shorter_side" not in visible
    assert "program" not in visible
    assert all("output" not in pair for pair in public["test"])


def test_verifier_rejects_tampered_selected_label():
    from copy import deepcopy
    import prototype

    episode = prototype.build_episode(4401, scale_basis="shorter_side", demos=2, queries=4)
    tampered = deepcopy(episode)
    tampered["train"][0]["output"][0][0] = (tampered["train"][0]["output"][0][0] + 1) % 10
    errors = prototype.episode_errors(tampered, replay_racket=False)
    assert any("label mismatch" in error for error in errors)


def test_promotion_adapter_exposes_independent_supported_counts():
    import adapter
    import prototype

    episode = adapter.generate(
        5501,
        {"scale_basis": "shorter_side"},
        demos=2,
        queries=4,
    )
    assert len(episode["train"]) == 2
    assert len(episode["test"]) == 4
    assert episode["program_solution"] == prototype.program_for("shorter_side")
    assert all("setting" not in pair for pair in episode["train"] + episode["test"])
    with pytest.raises(ValueError, match="settings"):
        adapter.generate(1, {"scale_basis": "longer_side", "extra": 1}, 2, 4)


def test_artifact_verifier_rejects_public_byte_tampering(tmp_path):
    import prototype

    episode = prototype.build_episode(6601, scale_basis="longer_side", demos=2, queries=4)
    out = tmp_path / "export"
    manifest = prototype.write_artifacts(episode, out)
    report = prototype.verify_artifacts(out, replay_racket=False)
    assert report["status"] == "passed"
    assert report["public_id"] == manifest["public_id"]
    assert report["turn_count"] == 4

    public_path = out / manifest["public_path"]
    public_path.write_bytes(public_path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="public"):
        prototype.verify_artifacts(out, replay_racket=False)
