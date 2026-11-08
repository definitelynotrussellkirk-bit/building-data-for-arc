from __future__ import annotations

import importlib.util
import json
from pathlib import Path


TASK_ROOT = Path(__file__).resolve().parents[1]
PROTOTYPE = TASK_ROOT / "workspace" / "parametric" / "prototype.py"


def _load():
    assert PROTOTYPE.exists(), "source-action prototype has not been implemented"
    spec = importlib.util.spec_from_file_location("source_action_prototype", PROTOTYPE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_default_rule_source_is_exact_canonical_and_copy_is_single_branch_variant():
    prototype = _load()
    canonical = prototype.canonical_rule_source().strip()
    move = prototype.rule_source("move")
    copy = prototype.rule_source("copy")
    assert move == canonical
    assert copy != move
    assert "(if (= v sc) 7 v)" in move
    assert "(if (= v sc) 7 v)" not in copy
    assert copy.count("(cellmap g") == move.count("(cellmap g") == 1


def test_hidden_source_action_is_fixed_once_per_episode_and_both_settings_are_reachable():
    prototype = _load()
    observed = {prototype.source_action_for_seed(seed) for seed in range(100)}
    assert observed == {"move", "copy"}
    for seed in range(20):
        episode = prototype.sample_episode(seed)
        assert episode["parameters"]["source_action"] == prototype.source_action_for_seed(seed)
        assert len(episode["inputs"]) == 4


def test_settings_share_inputs_but_produce_distinguishable_outputs():
    prototype = _load()
    inputs = prototype.sample_inputs(37)
    move_episode = prototype.sample_episode(37, source_action="move")
    copy_episode = prototype.sample_episode(37, source_action="copy")
    assert move_episode["inputs"] == copy_episode["inputs"] == inputs
    for grid in inputs:
        move = prototype.python_mirror(grid, "move")
        copy = prototype.python_mirror(grid, "copy")
        assert move != copy
        analysis = prototype.production_generator()._analysis(grid)
        for row, col in analysis["shape_cells"]:
            assert move[row][col] == 7
            assert copy[row][col] == analysis["shape_color"]


def test_public_challenge_hides_rule_parameter_program_and_query_output():
    prototype = _load()
    episode = prototype.sample_episode(51, source_action="copy")
    pairs = [
        {"input": grid, "output": prototype.python_mirror(grid, "copy")}
        for grid in episode["inputs"]
    ]
    challenge = prototype.public_challenge(pairs, query_index=3)
    payload = json.dumps(challenge)
    assert len(challenge["train"]) == 3
    assert len(challenge["test"]) == 1
    assert "output" not in challenge["test"][0]
    assert "source_action" not in payload
    assert "program" not in payload


def test_source_identity_binds_prototype_and_current_production_generator():
    prototype = _load()
    identity = prototype.source_identity()
    assert identity["task_id"] == "8a50bfdecd97"
    assert identity["production_generator_version"] == prototype.production_generator().VERSION
    assert identity["production_generator_sha256"] == prototype._sha256_bytes(
        (TASK_ROOT / "generator.py").read_bytes()
    )
    assert identity["prototype_source_sha256"] == prototype._sha256_bytes(
        PROTOTYPE.read_bytes()
    )
