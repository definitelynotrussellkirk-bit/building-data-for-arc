"""Focused contract for the proposed bridge-scope rule prototype."""
from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
sys.path.insert(0, str(HOME / "workspace" / "parametric"))

import prototype as proto  # noqa: E402
from reference_probe import (  # noqa: E402
    intended_output,
    load_generator,
    output_diff_cells,
    seed_lines_only_rival,
)


def witness_grids():
    gen = load_generator()
    return [
        gen.generate(20261020, index, difficulty="medium", layout_profile="mixed", n_keys=5)
        for index in range(4)
    ]


def test_parameter_contract_and_episode_choice_are_bounded_and_deterministic():
    assert proto.PARAMETER_NAME == "bridge_scope"
    assert proto.SCOPES == ("all_pairs", "seed_only")
    assert proto.DEFAULT_SCOPE == "all_pairs"
    assert proto.choose_scope(0) == "all_pairs"
    assert proto.choose_scope(1) == "seed_only"
    assert proto.choose_scope(0) == proto.choose_scope(0)
    with pytest.raises((TypeError, ValueError)):
        proto.racket_program("first_two")


def test_python_mirror_preserves_canonical_default_and_changes_nonseed_bridges():
    for grid in witness_grids():
        canonical = proto.python_output(grid, "all_pairs")
        alternative = proto.python_output(grid, "seed_only")
        assert canonical == intended_output(grid)
        assert alternative == seed_lines_only_rival(grid)
        assert output_diff_cells(canonical, alternative)


def test_materialized_racket_programs_match_python_for_both_settings():
    grids = witness_grids()
    for scope in proto.SCOPES:
        program = proto.racket_program(scope)
        assert program.startswith("(rule!")
        actual = proto.racket_outputs(program, grids)
        expected = [proto.python_output(grid, scope) for grid in grids]
        assert actual == expected


def test_complete_episode_uses_one_hidden_scope_and_demos_refute_the_other_scope():
    for scope, seed in (("all_pairs", 20), ("seed_only", 21)):
        episode = proto.build_episode(seed, scope=scope, difficulty="medium", n_train=3, n_test=1)
        assert episode["meta"]["bridge_scope"] == scope
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 1
        assert all(
            pair["output"] == proto.python_output(pair["input"], scope)
            for pair in episode["train"] + episode["test"]
        )
        rival = proto.other_scope(scope)
        assert all(
            pair["output"] != proto.python_output(pair["input"], rival)
            for pair in episode["train"]
        )

        public = proto.public_challenge(episode)
        assert "program" not in public
        assert "meta" not in public
        assert all("output" in pair for pair in public["train"])
        assert all("output" not in pair for pair in public["test"])
        assert scope not in json.dumps(public)


def test_evidence_bundle_records_both_settings_program_hashes_and_public_files(tmp_path):
    manifest = proto.write_evidence_bundle(tmp_path, seeds={"all_pairs": 20, "seed_only": 21})
    assert manifest["schema"] == "79a30e61d332-parametric-evidence-v1"
    assert set(manifest["settings"]) == set(proto.SCOPES)
    for scope in proto.SCOPES:
        item = manifest["settings"][scope]
        assert item["bridge_scope"] == scope
        assert item["racket_verified"] is True
        assert len(item["program_sha256"]) == 64
        assert item["demonstrations_refute_other_scope"] is True
        public = json.loads((tmp_path / item["public_challenge_path"]).read_text())
        assert "program" not in public and "meta" not in public
        assert all("output" not in pair for pair in public["test"])
