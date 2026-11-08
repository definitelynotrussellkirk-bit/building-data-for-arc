"""Exercise native expression generators through the complete Racket check."""
import hashlib
import shutil

import pytest

from arcpuzzles import Catalog


@pytest.mark.skipif(shutil.which("racket") is None, reason="Racket runtime required")
@pytest.mark.parametrize("task_id", ["generic_gather_gen1", "generic_gather_gen2", "generic_gather_gen3"])
@pytest.mark.parametrize("seed,difficulty", [(0, "easy"), (17, "medium"), (42, "hard")])
def test_native_expression_outputs_are_verified_by_racket(task_id, seed, difficulty):
    episode, = Catalog().generate(task_id, seed=seed, difficulty=difficulty,
                                  n_train=1, n_test=1, allow_unapproved=True)
    assert episode["train"] and episode["test"]
    assert episode["program_normalization"] == "expression_to_rule"
    assert episode["emitted_program"] in episode["program"]
    expected = hashlib.sha256(" ".join(episode["program"].split()).encode()).hexdigest()[:12]
    assert episode["provenance"]["rule_hash"] == episode["executed_rule_hash"] == expected
    assert episode["provenance"]["approved"] is False
