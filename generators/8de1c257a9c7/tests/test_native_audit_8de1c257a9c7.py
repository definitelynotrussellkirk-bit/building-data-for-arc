"""Independent semantic and executable-rival checks for the native family."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest


HOME = Path(__file__).resolve().parents[1]
AUDIT = HOME / "workspace/parametric/audit_native.py"
IDENTITY = {"stamp_transform": "identity"}
MIRROR = {"stamp_transform": "mirror_horizontal"}


@pytest.fixture(scope="module")
def audit():
    assert AUDIT.is_file(), "independent native audit has not been implemented"
    spec = importlib.util.spec_from_file_location("_stamp_independent_audit_tests", AUDIT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _grid(shape, green, cyans, reds):
    result = [[0] * shape[1] for _ in range(shape[0])]
    result[green[0]][green[1]] = 3
    for r, c in cyans:
        result[r][c] = 8
    for r, c in reds:
        result[r][c] = 2
    return result


def _colored(grid, color=8):
    return {(r, c) for r, row in enumerate(grid) for c, cell in enumerate(row)
            if cell == color}


def _hook(reflected=False):
    # Literal six-cell input and destinations from the historical count witness.
    cyans = ({(4, 6), (5, 6), (5, 5), (6, 5), (7, 5), (7, 4)} if reflected else
             {(4, 6), (5, 6), (5, 7), (6, 7), (7, 7), (7, 8)})
    return _grid((13, 13), (6, 6), cyans, {(3, 3), (9, 9)})


def _overlap():
    # Same-column neighboring destinations produce true double coverage.
    return _grid((19, 19), (10, 13),
                 {(8, 13), (9, 13), (10, 14), (11, 14), (11, 15), (12, 15)},
                 {(4, 4), (5, 4), (6, 9)})


def _reflected_overlap():
    return _grid((19, 19), (10, 13),
                 {(8, 13), (9, 13), (10, 12), (11, 12), (11, 11), (12, 11)},
                 {(4, 4), (5, 4), (6, 9)})


def test_reference_transplants_literal_green_relative_offsets(audit):
    grid = _hook()
    identity = {(1, 3), (2, 3), (2, 4), (3, 4), (4, 4), (4, 5),
                (7, 9), (8, 9), (8, 10), (9, 10), (10, 10), (10, 11)}
    reflected = {(1, 3), (2, 3), (2, 2), (3, 2), (4, 2), (4, 1),
                 (7, 9), (8, 9), (8, 8), (9, 8), (10, 8), (10, 7)}
    assert _colored(audit.reference(grid, IDENTITY)) == identity
    assert _colored(audit.reference(grid, MIRROR)) == reflected
    assert set(cell for row in audit.reference(grid, IDENTITY) for cell in row) <= {0, 8}


def test_count_rival_cannot_read_same_count_geometry(audit):
    inputs = [_hook(), _hook(True)]
    for setting in (IDENTITY, MIRROR):
        assert audit.reference(inputs[0], setting) != audit.reference(inputs[1], setting)
        for name in ("historical_count_identity", "historical_count_mirror_horizontal"):
            assert audit.rival_output(name, inputs[0], setting) == audit.rival_output(name, inputs[1], setting)
    unknown = _overlap()
    unknown[12][16] = 8  # Seven cells, connected, absent from the historical count bank.
    assert audit.self_check(unknown) == []
    assert _colored(audit.rival_output("historical_count_identity", unknown, IDENTITY)) == set()


def test_union_and_xor_are_distinct_on_literal_overlap(audit):
    for setting in (IDENTITY, MIRROR):
        expected = audit.reference(_overlap(), setting)
        xor = audit.rival_output("xor_overlaps", _overlap(), setting)
        assert expected[3][4] == 8
        assert xor[3][4] == 0


def test_independent_grammar_rejects_typed_and_boundary_errors(audit):
    malformed = _hook()
    malformed[0][0] = False
    assert audit.self_check(malformed)
    outside = _hook()
    outside[3][3] = 0
    outside[0][0] = 2
    assert audit.self_check(outside)
    single = _hook()
    single[9][9] = 0
    assert audit.self_check(single) == []


def test_count_witness_requires_all_declared_features_held_fixed(audit):
    pairs = [{"input": _overlap()}, {"input": _reflected_overlap()}]
    result = audit.paired_count_witness(pairs)
    assert result["different_outputs_by_setting"] == {"identity": True, "mirror_horizontal": True}
    pairs[1]["input"][6][9] = 0
    pairs[1]["input"][6][10] = 2
    with pytest.raises(ValueError, match="cardinality"):
        audit.paired_count_witness(pairs)


def test_complete_racket_rivals_match_independent_meanings(audit):
    unknown = _overlap()
    unknown[12][16] = 8
    grids = [_hook(), _hook(True), _overlap(), unknown]
    with audit.CachedEvaluator() as evaluator:
        assert evaluator.identity["backend"] == "racket"
        assert evaluator.identity["protected"] is True
        for setting in (IDENTITY, MIRROR):
            for grid in grids:
                assert evaluator.execute(audit.reference_program(setting), grid) == audit.reference(grid, setting)
                for name in audit.RIVAL_NAMES:
                    assert evaluator.execute(audit.rival_program(name, setting), grid) == audit.rival_output(name, grid, setting)
        count = evaluator.evaluations
        again = evaluator.execute(audit.reference_program(IDENTITY), grids[0])
        again[0][0] = 9
        assert evaluator.execute(audit.reference_program(IDENTITY), grids[0])[0][0] == 0
        assert evaluator.evaluations == count


def test_demo_fit_survivors_freeze_before_a_distinguishing_query(audit):
    symmetric = _grid((13, 13), (6, 6),
                      {(5, 6), (6, 5), (6, 7), (7, 6)}, {(3, 3), (9, 9)})
    episode = {"train": [{"input": symmetric, "output": audit.reference(symmetric, IDENTITY)}],
               "test": [{"input": _hook(), "output": audit.reference(_hook(), IDENTITY)}]}
    with audit.CachedEvaluator() as evaluator:
        with pytest.raises(ValueError, match="demonstration"):
            audit.audit_episode(episode, IDENTITY, evaluator)
        query_hash = audit.digest(_hook())
        assert query_hash not in {row["input_sha256"] for row in evaluator.records}


def test_two_demo_certificate_stays_fixed_while_query_is_verified(audit):
    for setting in (IDENTITY, MIRROR):
        episode = {"train": [{"input": grid, "output": audit.reference(grid, setting)}
                             for grid in (_overlap(), _reflected_overlap())],
                   "test": [{"input": _hook(), "output": audit.reference(_hook(), setting)}]}
        with audit.CachedEvaluator() as evaluator:
            result = audit.audit_episode(episode, setting, evaluator)
        assert result["certificate"]["survivors"] == ["setting:" + setting["stamp_transform"]]
        assert result["certificate_sha256_before_queries"] == result["certificate_sha256_after_queries"]
        assert len(result["queries"]) == 1
        assert all(row["refuting_demo_indices"] for row in result["certificate"]["hypotheses"]
                   if not row["name"].startswith("setting:"))


def test_rival_execution_errors_are_not_refutations(audit):
    train = [{"input": _hook(), "output": audit.reference(_hook(), IDENTITY)}]
    broken_program = audit.rival_program("xor_overlaps", IDENTITY)
    with audit.CachedEvaluator() as live:
        class BrokenRivalEvaluator:
            def execute(self, program, grid):
                if program == broken_program:
                    raise RuntimeError("controlled rival execution failure")
                return live.execute(program, grid)

        with pytest.raises(RuntimeError, match="controlled rival execution failure"):
            audit.fit_demonstrations(train, IDENTITY, BrokenRivalEvaluator())


def test_audit_rejects_corrupt_claim_labels(audit):
    wrong = audit.reference(_hook(), IDENTITY)
    wrong[0][0] = 8
    with audit.CachedEvaluator() as evaluator:
        with pytest.raises(ValueError, match="claim"):
            audit.fit_demonstrations([{"input": _hook(), "output": wrong}], IDENTITY, evaluator)


def test_cheap_screen_rejects_a_corrupted_native_query_claim(audit):
    adapter = audit._load_adapter()

    class CorruptedClaimAdapter:
        @staticmethod
        def generate(*args):
            episode = adapter.generate(*args)
            episode["test"][0]["output"][0][0] = 9
            return episode

    with pytest.raises(ValueError, match="claim"):
        audit.screen(CorruptedClaimAdapter())

