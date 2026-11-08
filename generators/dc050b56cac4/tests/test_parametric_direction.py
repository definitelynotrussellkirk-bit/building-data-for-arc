"""Prototype-only checks for an episode-level diagonal direction parameter."""

import importlib.util
import hashlib
import os
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root
from arc_repl.racket_bridge import RacketBridge

ROOT = find_root(__file__)
SOURCE = ROOT / "generators/dc050b56cac4/workspace/parametric/prototype.py"


def load_generator():
    source = Path(
        os.environ.get(
            "GENERATOR_UNDER_TEST",
            ROOT / "generators/dc050b56cac4/generator.py",
        )
    ).resolve()
    body = source.read_bytes()
    spec = importlib.util.spec_from_file_location("dc050b56_parametric_generator", source)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    exec(compile(body, str(source), "exec"), module.__dict__)
    return module, source, hashlib.sha256(body).hexdigest()


GEN, GENERATOR_SOURCE, GENERATOR_SHA256 = load_generator()


def load_prototype():
    if not SOURCE.is_file():
        pytest.fail(f"missing direction prototype: {SOURCE}")
    spec = importlib.util.spec_from_file_location("dc050b56_direction_prototype", SOURCE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_default_program_is_exact_and_only_direction_bindings_change():
    p = load_prototype()
    original = p.canonical_program(ROOT)
    assert p.instantiate(original) == original
    for direction, (row_op, col_op) in p.DIRECTION_OPERATORS.items():
        expected = original.replace(
            p.CANONICAL_ROW_BINDING,
            f"(nr ({row_op} cross-row n))",
            1,
        ).replace(
            p.CANONICAL_COL_BINDING,
            f"(nc ({col_op} cross-col n))",
            1,
        )
        assert p.instantiate(original, direction) == expected
    with pytest.raises(ValueError, match="unsupported direction"):
        p.instantiate(original, "clockwise")


def test_episode_parameter_is_deterministic_and_drawn_once():
    p = load_prototype()
    assert [p.parameters(seed)["direction"] for seed in range(4)] == list(p.DIRECTIONS)
    for seed in range(8):
        assert p.parameters(seed) == p.parameters(seed)
    for bad in (True, 1.0, "1", None):
        with pytest.raises(TypeError, match="seed must be an integer"):
            p.parameters(bad)


def test_controlled_inputs_are_deterministic_and_lawful_for_every_direction():
    p = load_prototype()
    for seed in range(4):
        inputs = p.fixture_inputs(seed)
        assert inputs == p.fixture_inputs(seed)
        assert len(inputs) == 4
        for grid in inputs:
            assert GEN.self_check(grid) == []
            facts = GEN._analyze(grid)
            n = int(facts["n_grays"])
            row = int(facts["cross_row"])
            col = int(facts["cross_col"])
            h = int(facts["grid_h"])
            w = int(facts["grid_w"])
            assert n <= row <= h - 1 - n
            assert n <= col <= w - 1 - n


def test_default_racket_program_matches_every_canonical_pair():
    p = load_prototype()
    bridge = RacketBridge()
    try:
        program = p.canonical_program(ROOT)
        pairs = canonical_pairs(p.TASK_ID, root=ROOT, labeled_only=True)
        assert pairs
        for pair in pairs:
            assert p.execute(bridge, p.instantiate(program), pair["input"]) == pair["output"]
    finally:
        bridge.shutdown()


def test_racket_episodes_distinguish_all_direction_rivals_and_mask_queries():
    p = load_prototype()
    bridge = RacketBridge()
    try:
        canonical = p.canonical_program(ROOT)
        records = [p.episode(seed, canonical, bridge) for seed in range(4)]
        assert {record["parameters"]["direction"] for record in records} == set(p.DIRECTIONS)
        for record in records:
            assert len(record["train"]) == 3
            assert len(record["test"]) == 1
            assert all(rival["demo_differences"] for rival in record["rivals"])
            assert all(rival["query_differs"] for rival in record["rivals"])
            public = p.public_challenge(record)
            assert set(public) == {"train", "test"}
            assert all(set(pair) == {"input"} for pair in public["test"])

        witness = p.fixture_inputs(0)[0]
        outputs = [
            p.execute(bridge, p.instantiate(canonical, direction), witness)
            for direction in p.DIRECTIONS
        ]
        assert len({p.grid_key(output) for output in outputs}) == len(p.DIRECTIONS)
    finally:
        bridge.shutdown()


def test_materialized_gallery_contains_hash_bound_private_and_masked_public_evidence(tmp_path):
    p = load_prototype()
    report = p.materialize(tmp_path)
    assert report["status"] == "prototype"
    assert report["default_program_exact"] is True
    assert report["episode_count"] == 4
    assert report["distinct_settings"] == list(p.DIRECTIONS)
    for index in range(4):
        assert (tmp_path / "public" / f"episode-{index}.json").is_file()
        assert (tmp_path / "private" / f"episode-{index}.json").is_file()
        assert (tmp_path / "private" / f"episode-{index}.rkt").is_file()
    assert (tmp_path / "private" / "differing-witness.json").is_file()
    assert (tmp_path / "private" / "canonical-default.json").is_file()
    assert (tmp_path / "report.json").is_file()
