"""Saved-instance probe accounting and source-identity regression checks."""
import hashlib
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "workspace"))
from census_rotations import audit
from review_support import digest, load_generator, row_oracle


def synthetic_census(gen):
    rows = []
    for index, n_pairs in enumerate((4, 5)):
        pairs = []
        for sample_index in range(n_pairs):
            grid = gen.generate(271, sample_index, difficulty="easy")
            pairs.append({"input": grid, "output": row_oracle(grid)})
        instance = {"train": pairs[:3], "test": pairs[3:]}
        rows.append({"band": "easy", "index": index, "seed": 271, "sample_index": 0,
                     "instance": instance, "instance_sha256": digest(instance)})
    return {"task_id": "0d5077971eea", "generator_sha256": hashlib.sha256(Path(gen.__file__).read_bytes()).hexdigest(),
            "declared_rule_hash": gen.RULE_HASH, "status": "no_declared_ambiguity",
            "sampler": {"bands": ["easy"], "per_band": 2}, "lessons": rows}


def test_rotation_probe_accounts_for_overlapping_windows_and_unique_inputs():
    gen = load_generator()
    result = audit(synthetic_census(gen), gen)
    assert result["status"] == "no_declared_ambiguity"
    assert result["totals"]["materialized_lessons"] == 2
    assert result["totals"]["source_pairs"] == 9
    assert result["totals"]["windows"] == 9
    assert result["totals"]["query_pairs"] == 14
    assert result["unique_inputs"] == 5
    assert all(item["status"] == "fits_all" for item in result["canonical_rival_fit"].values())


def test_rotation_probe_refuses_stale_generator_and_corrupted_or_partial_instances():
    gen = load_generator()
    census = synthetic_census(gen)
    census["generator_sha256"] = "0" * 64
    result = audit(census, gen)
    assert result["status"] == "error" and result["windows"] == []
    census = synthetic_census(gen)
    input_grid = census["lessons"][0]["instance"]["train"][0]["input"]
    input_grid[0][0] = (input_grid[0][0] + 1) % 10
    result = audit(census, gen)
    assert result["status"] == "error"
    assert any("Instance hash mismatch" in error for error in result["errors"])
    census = synthetic_census(gen)
    census["lessons"] = census["lessons"][:1]
    result = audit(census, gen)
    assert result["status"] == "error"
    assert any("Incomplete saved population" in error for error in result["errors"])
