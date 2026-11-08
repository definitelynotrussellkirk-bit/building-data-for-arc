"""Prototype-only checks; canonical production repair coverage is separate."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys

import pytest

from reviewer_support import canonical_pairs, find_root


TASK_ID = "7a37505e7bd0"
ROOT = find_root(__file__)
HOME = Path(__file__).resolve().parents[1] / "workspace" / "parametric"
SETTINGS = [
    {"counting_policy": policy, "expansion_axis": axis}
    for policy in ("all_colors", "nonzero_colors")
    for axis in ("both", "rows", "columns")
]


def _module():
    path = HOME / "prototype.py"
    assert path.is_file(), "Missing bounded episode prototype and Racket execution API"
    name = "_test_parametric_7a37505e7bd0"
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return sys.modules[name]


@pytest.fixture(scope="module")
def oracle():
    # The actual bridge is required. Missing Racket is an error, never a skip.
    from arc_repl.racket_bridge import RacketBridge

    with RacketBridge() as bridge:
        yield bridge


def test_canonical_setting_matches_racket_authority_on_all_eight_pairs(oracle):
    prototype = _module()
    with prototype.RacketOracle(bridge=oracle) as runner:
        pairs = canonical_pairs(TASK_ID, root=ROOT)
        assert len(pairs) == 8
        code = runner.program(prototype.CANONICAL_PARAMETERS)
        assert code == prototype.canonical_rule(ROOT)
        for pair in pairs:
            actual = runner.label(pair["input"], prototype.CANONICAL_PARAMETERS)
            authority = runner.execute_program(
                prototype.canonical_rule(ROOT), pair["input"], purpose="canonical_reference"
            )
            assert actual == authority == pair["output"]


def test_all_six_racket_program_files_match_materializer():
    prototype = _module()
    assert list(prototype.ALL_PARAMETERS) == SETTINGS
    codes = []
    for params in SETTINGS:
        code = prototype.materialize_program(params)
        retained = HOME / "rules" / (prototype.setting_key(params) + ".rkt")
        assert retained.read_text(encoding="utf-8") == code
        codes.append(code)
    assert len(set(codes)) == 6


@pytest.mark.parametrize("params", SETTINGS)
def test_exact_common_input_witness_uses_counted_block_expansion(oracle, params):
    prototype = _module()
    with prototype.RacketOracle(bridge=oracle) as runner:
        grid = runner.generator.generate(17, 1, difficulty="medium")
        assert runner.generator.self_check(grid) == []
        assert len({c for row in grid for c in row}) == 4
        assert 0 in {c for row in grid for c in row}
        result = runner.label(grid, params)
        factor = 4 if params["counting_policy"] == "all_colors" else 3
        rows = factor if params["expansion_axis"] in {"both", "rows"} else 1
        columns = factor if params["expansion_axis"] in {"both", "columns"} else 1
        assert (len(result), len(result[0])) == (3 * rows, 3 * columns)
        for r, row in enumerate(result):
            for c, color in enumerate(row):
                assert color == grid[r // rows][c // columns]


@pytest.mark.parametrize("bad", [
    {},
    {"counting_policy": "all_colors"},
    {"counting_policy": "all_colors", "expansion_axis": "diagonal"},
    {"counting_policy": "foreground", "expansion_axis": "both"},
    {"counting_policy": "all_colors", "expansion_axis": "both", "extra": 1},
    {"counting_policy": True, "expansion_axis": "both"},
])
def test_parameters_are_bounded_and_complete(bad):
    prototype = _module()
    with pytest.raises(ValueError):
        prototype.validate_parameters(bad)


def test_seed_selection_is_reproducible_and_does_not_use_global_rng():
    prototype = _module()
    random.seed(1979)
    before = random.getstate()
    first = [prototype.choose_parameters(seed) for seed in range(64)]
    second = [prototype.choose_parameters(seed) for seed in range(64)]
    assert first == second
    assert {prototype.setting_key(p) for p in first} == {
        prototype.setting_key(p) for p in SETTINGS
    }
    assert random.getstate() == before
    for invalid in (True, -1, "17", 2.0):
        with pytest.raises(ValueError):
            prototype.choose_parameters(invalid)


@pytest.mark.parametrize("params", SETTINGS)
@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_complete_episodes_preserve_sampler_and_distinguish_every_rotation(oracle, params, band):
    prototype = _module()
    with prototype.RacketOracle(bridge=oracle) as runner:
        for seed in (0, 17):
            episode = prototype.generate_episode(
                seed, difficulty=band, sample_start=3, parameters=params, oracle=runner
            )
            assert episode["parameters"] == params
            assert episode["parameter_selection"] == "explicit"
            pairs = episode["train"] + episode["test"]
            assert len(episode["train"]) == 5
            assert len(episode["test"]) == 1
            assert {len({c for row in p["input"] for c in row}) for p in pairs[:5]} == {1, 2, 3, 4, 5}
            for offset, pair in enumerate(pairs):
                expected_input = runner.generator.generate(seed, 3 + offset, difficulty=band)
                assert pair["input"] == expected_input
                assert pair["output"] == runner.label(expected_input, params)
                assert episode["sampling"][offset]["sample_index"] == 3 + offset
            for query_index in range(6):
                result = prototype.score_parameters(pairs, params, runner, query_index=query_index)
                assert result["identified"]
                assert not result["measured_ambiguity"]
                assert len(result["rivals"]) == 5
                assert all(row["status"] == "refuted" for row in result["rivals"])


def test_episode_seed_fixes_rule_across_inputs_and_returns_fresh_grids(oracle):
    prototype = _module()
    with prototype.RacketOracle(bridge=oracle) as runner:
        before = random.getstate()
        first = prototype.generate_episode(17, difficulty="hard", sample_start=4, oracle=runner)
        second = prototype.generate_episode(17, difficulty="hard", sample_start=4, oracle=runner)
        assert first == second
        assert first["parameters"] == prototype.choose_parameters(17)
        assert first["parameter_selection"] == "seeded"
        assert random.getstate() == before
        first["train"][0]["input"][0][0] = (first["train"][0]["input"][0][0] + 1) % 10
        assert first != second
        for kwargs in ({"difficulty": "expert"}, {"sample_start": True}, {"sample_start": -1}):
            with pytest.raises(ValueError):
                prototype.generate_episode(17, oracle=runner, **kwargs)


def test_prototype_domain_rejects_all_zero_and_arbitrary_shapes(oracle):
    prototype = _module()
    with prototype.RacketOracle(bridge=oracle) as runner:
        for grid in ([[0] * 3 for _ in range(3)], [[3]], [[1, 2], [2, 1]]):
            with pytest.raises(ValueError, match="input"):
                runner.label(grid, prototype.CANONICAL_PARAMETERS)


def test_rival_scoring_rejects_a_tampered_label(oracle):
    prototype = _module()
    with prototype.RacketOracle(bridge=oracle) as runner:
        episode = prototype.generate_episode(3, oracle=runner)
        pairs = copy.deepcopy(episode["train"] + episode["test"])
        pairs[0]["output"][0][0] = (pairs[0]["output"][0][0] + 1) % 10
        with pytest.raises(ValueError, match="Racket label"):
            prototype.score_parameters(pairs, episode["parameters"], runner, query_index=5)


def test_negative_control_records_real_ambiguity_without_a_solver_attempt(oracle):
    prototype = _module()
    with prototype.RacketOracle(bridge=oracle) as runner:
        control = prototype.ambiguity_control(runner)
        pairs = control["pairs"]
        assert len(pairs) == 6
        assert all(0 not in {c for row in pair["input"] for c in row} for pair in pairs[:5])
        assert 0 in {c for row in pairs[5]["input"] for c in row}
        for pair in pairs:
            assert pair["output"] == runner.label(pair["input"], prototype.CANONICAL_PARAMETERS)
        score = control["score"]
        assert not score["identified"]
        assert score["measured_ambiguity"]
        ambiguous = [row for row in score["rivals"] if row["status"] == "ambiguous"]
        assert [row["parameters"] for row in ambiguous] == [
            {"counting_policy": "nonzero_colors", "expansion_axis": "both"}
        ]
        assert control["solver_attempts"] == 0


def test_public_challenge_omits_query_label_parameters_and_code(oracle, tmp_path):
    prototype = _module()
    with prototype.RacketOracle(bridge=oracle) as runner:
        episode = prototype.generate_episode(29, oracle=runner)
        public = prototype.public_challenge(episode)
        assert set(public) == {"train", "test"}
        assert all(set(pair) == {"input", "output"} for pair in public["train"])
        assert len(public["test"]) == 1
        assert set(public["test"][0]) == {"input"}
        assert public["test"][0]["input"] == episode["test"][0]["input"]
        paths = prototype.save_episode(episode, tmp_path, "episode-0000")
        assert json.loads(Path(paths["public"]).read_text()) == public
        private = json.loads(Path(paths["private"]).read_text())
        receipt = json.loads(Path(paths["receipt"]).read_text())
        assert private == episode
        assert receipt["parameters"] == episode["parameters"]
        assert receipt["racket_outputs"] == [p["output"] for p in episode["train"] + episode["test"]]
        assert receipt["program"]["code"] == episode["program"]["code"]
        assert receipt["program"]["sha256"] == hashlib.sha256(episode["program"]["code"].encode()).hexdigest()
        assert receipt["sources"] == episode["sources"]
        public["train"][0]["input"][0][0] = -1
        assert episode["train"][0]["input"][0][0] >= 0


def test_small_evidence_export_has_exact_counts_and_source_bound_racket_outputs(tmp_path):
    prototype = _module()
    report = prototype.build_evidence(tmp_path / "evidence", seeds=(5,), bands=("easy",), starts=(0,))
    assert report["summary"] == {
        "settings": 6,
        "episodes": 6,
        "labeled_pairs": 36,
        "production_identified": 6,
        "production_ambiguous": 0,
        "rotations": 36,
        "rotations_identified": 36,
        "rotations_ambiguous": 0,
        "canonical_pairs": 8,
        "canonical_matches": 8,
        "witness_distinct_outputs": 6,
        "negative_controls": 1,
        "negative_controls_ambiguous": 1,
        "solver_attempts": 0,
    }
    out = tmp_path / "evidence"
    assert len(list((out / "public").glob("*.json"))) == 6
    assert len(list((out / "private" / "episodes").glob("*.episode.json"))) == 6
    assert len(list((out / "private" / "episodes").glob("*.receipt.json"))) == 6
    executions = [json.loads(line) for line in (out / "private" / "racket-executions.jsonl").read_text().splitlines()]
    assert executions
    assert {row["program_sha256"] for row in executions} >= {
        hashlib.sha256(prototype.materialize_program(p).encode()).hexdigest() for p in SETTINGS
    }
    assert all(row["backend"] == "racket" for row in executions)
    assert report["status"] == "prototype_bounded_checks_passed"
