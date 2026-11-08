from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path


PROTO = Path(__file__).resolve().parents[1] / "workspace" / "parametric" / "prototype.py"
spec = importlib.util.spec_from_file_location("rank_parametric_prototype", PROTO)
prototype = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(prototype)


def test_allowed_rank_parameter_and_canonical_default():
    assert prototype.ALLOWED_TARGET_RANKS == (1, 2)
    assert prototype.DEFAULT_TARGET_RANK == 2
    digest = hashlib.sha256(
        " ".join(prototype.racket_program(2).split()).encode()
    ).hexdigest()[:12]
    assert digest == "f074243a0544"


def test_settings_change_outputs_on_every_materialized_input():
    episode_one = prototype.build_episode(seed=91001, target_rank=1)
    episode_two = prototype.build_episode(seed=91001, target_rank=2)
    assert episode_one["target_rank"] == 1
    assert episode_two["target_rank"] == 2
    assert [item["input"] for item in episode_one["pairs"]] == [
        item["input"] for item in episode_two["pairs"]
    ]
    assert all(
        left["output"] != right["output"]
        for left, right in zip(episode_one["pairs"], episode_two["pairs"])
    )


def test_independent_oracle_matches_production_rank_two():
    generator = prototype.load_generator()
    episode = prototype.build_episode(seed=91002, target_rank=2)
    for pair in episode["pairs"]:
        assert pair["output"] == generator.rule_mirror(pair["input"])


def test_materializer_omits_hidden_parameter_and_query_answer_from_challenges(tmp_path):
    receipt = prototype.materialize(tmp_path)
    assert receipt["status"] == "complete"
    for rank in prototype.ALLOWED_TARGET_RANKS:
        challenge = json.loads((tmp_path / f"challenge-rank-{rank}.json").read_text())
        assert "target_rank" not in challenge
        assert len(challenge["train"]) == 3
        assert len(challenge["test"]) == 1
        assert "output" not in challenge["test"][0]
        private = json.loads((tmp_path / f"episode-rank-{rank}.json").read_text())
        assert private["target_rank"] == rank
        assert len(private["pairs"]) == 4
