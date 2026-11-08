"""Tests for the task-local threshold-rule prototype."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
WORKSPACE = HOME / "workspace"
sys.path.insert(0, str(WORKSPACE))


def _load_prototype():
    path = WORKSPACE / "parametric" / "threshold_prototype.py"
    spec = importlib.util.spec_from_file_location("threshold_prototype", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load prototype at {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _aggregate_histogram(proto, pairs):
    total = {degree: 0 for degree in range(5)}
    for pair in pairs:
        for degree, count in proto.adjacency_histogram(pair["input"]).items():
            total[degree] += count
    return total


def test_threshold_program_has_canonical_default_and_exact_allowed_values():
    proto = _load_prototype()
    assert proto.DEFAULT_THRESHOLD == 2
    assert proto.ALLOWED_THRESHOLDS == (1, 2, 3)
    assert proto.racket_program(2) == proto.canonical_program()

    for threshold in proto.ALLOWED_THRESHOLDS:
        program = proto.racket_program(threshold)
        assert program.count("(>= adj ") == 1
        assert f"(>= adj {threshold})" in program

    for invalid in (0, 4, True, 2.0, "2"):
        with pytest.raises(ValueError, match="threshold"):
            proto.racket_program(invalid)


def test_each_episode_uses_one_threshold_and_teaches_every_allowed_rival():
    proto = _load_prototype()
    for threshold in proto.ALLOWED_THRESHOLDS:
        episode = proto.build_episode(9100 + threshold, threshold=threshold)
        assert episode["meta"]["threshold"] == threshold
        assert len(episode["train"]) >= 3
        assert len(episode["test"]) >= 1

        pairs = episode["train"] + episode["test"]
        assert all(
            pair["output"] == proto.apply_python(pair["input"], threshold)
            for pair in pairs
        )

        histogram = _aggregate_histogram(proto, episode["train"])
        assert histogram[0] > 0
        assert histogram[1] > 0
        assert histogram[2] > 0
        assert histogram[3] + histogram[4] > 0

        for rival in proto.ALLOWED_THRESHOLDS:
            if rival == threshold:
                continue
            assert any(
                proto.apply_python(pair["input"], rival) != pair["output"]
                for pair in episode["train"]
            ), f"threshold {threshold} is ambiguous with {rival}"


def test_public_challenge_hides_rule_parameter_program_and_query_answers():
    proto = _load_prototype()
    episode = proto.build_episode(9202, threshold=2)
    challenge = proto.public_challenge(episode)

    assert set(challenge) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in challenge["train"])
    assert all(set(pair) == {"input"} for pair in challenge["test"])
    assert "threshold" not in repr(challenge)
    assert "program" not in repr(challenge)


@pytest.mark.parametrize("threshold", [1, 2, 3])
def test_racket_program_matches_python_labels_for_complete_episode(threshold):
    proto = _load_prototype()
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])

    episode = proto.build_episode(9300 + threshold, threshold=threshold)
    pairs = episode["train"] + episode["test"]
    inputs = [pair["input"] for pair in pairs]
    expected = [pair["output"] for pair in pairs]
    assert proto.racket_outputs(proto.racket_program(threshold), inputs) == expected


def _load_materializer():
    path = WORKSPACE / "parametric" / "materialize.py"
    spec = importlib.util.spec_from_file_location("threshold_materialize", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load materializer at {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_materializer_builds_hash_bound_racket_verified_bundle():
    import hashlib

    materialize = _load_materializer()
    bundle = materialize.build_bundle(seed_base=9400)
    assert bundle["schema"] == "arcpuzzles-parametric-threshold-evidence-v1"
    assert bundle["parameter"]["name"] == "orthogonal_neighbor_threshold"
    assert bundle["parameter"]["default"] == 2
    assert bundle["parameter"]["allowed"] == [1, 2, 3]
    generator_path = HOME / "generator.py"
    assert bundle["production_generator_source"] == str(generator_path.relative_to(materialize.proto.ROOT))
    assert bundle["production_generator_sha256"] == hashlib.sha256(generator_path.read_bytes()).hexdigest()
    assert len(bundle["settings"]) == 3

    for setting in bundle["settings"]:
        assert setting["racket_verified"] is True
        assert setting["program_sha256"] == hashlib.sha256(
            setting["program"].encode("utf-8")
        ).hexdigest()
        assert setting["rivals_distinguished"] == [
            rival for rival in [1, 2, 3] if rival != setting["threshold"]
        ]
        assert all(set(pair) == {"input"} for pair in setting["challenge"]["test"])
