"""Focused tests of probe enumeration, authority batching and evidence semantics."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest
from reviewer_support import find_root


@pytest.fixture
def probe():
    root = find_root(__file__)
    source = next(path for path in (
        root / "generators/80f776fb3ce5/workspace/probe_local_contract.py",
        root / "puzzle_generators/per_puzzle/80f776fb3ce5/workspace/probe_local_contract.py",
    ) if path.is_file())
    spec = importlib.util.spec_from_file_location("local_contract_probe_test", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_complete_binary_corpus_and_independent_guard(probe):
    binary = probe.cases(True)
    assert len(binary) == 512
    assert len({tuple(v for row in c["input"] for v in row) for c in binary}) == 512
    assert sum(probe.expected(c["input"]) != c["input"] for c in binary) == 16
    extended = probe.cases()
    assert len(extended) == 568
    assert len({tuple(v for row in c["input"] for v in row) for c in extended}) == 568
    for case in extended[512:]:
        grid = case["input"]
        out = probe.expected(grid)
        assert all(out[r][c] == grid[r][c] for r in range(3) for c in range(3) if (r, c) != (1, 1))
        assert (out != grid) == (case["kind"] == "diagonal_palette")


def test_public_authority_batches_and_failures(probe):
    seen = []
    class Catalog:
        def apply(self, task, grids, **options):
            seen.append(len(grids))
            assert task == probe.TASK_ID and options == {"timeout": 5}
            return {"rule_hash_matches_catalog": True,
                    "results": [{"output": probe.expected(g), "error": None} for g in grids]}
    grids = [c["input"] for c in probe.cases()]
    outputs, receipts = probe.apply_batches(Catalog(), grids, 5)
    assert seen == [64] * 8 + [56]
    assert len(outputs) == 568 and len(receipts) == 9
    class BadCatalog:
        def apply(self, *args, **kwargs):
            return {"rule_hash_matches_catalog": True,
                    "results": [{"output": None, "error": "Racket failure"}]}
    with pytest.raises(ValueError, match="Racket failure"):
        probe.apply_batches(BadCatalog(), [grids[0]], 5)


def test_dynamic_rivals_receipts_and_validator_distinction(probe, tmp_path):
    source = tmp_path / "generator.py"
    source.write_text("# source identity fixture\n")
    source_hash = probe.sha(source.read_bytes())
    generator = SimpleNamespace(
        self_check=lambda g: [] if probe.expected(g) != g else ["no eligible target"],
        SEMANTIC_RIVALS={"identity": lambda g: g},
        LESSON_COMPETITORS={"identity": lambda g: g},
        CANONICAL_SHORTCUTS={},
    )
    class Catalog:
        def describe(self, task):
            return {"generator_sha256": source_hash, "rule_hash": "fixture"}
        def apply(self, task, grids, **options):
            return {"generator_sha256": source_hash, "rule_hash_matches_catalog": True,
                    "results": [{"input": g, "output": probe.expected(g), "error": None} for g in grids]}
    report = probe.build_report(generator, Catalog(), source, find_root(__file__), binary_only=True)
    assert report["verdict"] == "PASS"
    assert report["counts"]["validator_accepted"] == 16
    assert report["generated_support"]["tested"] is False
    assert set(report["rivals"]) == {"SEMANTIC_RIVALS.identity", "LESSON_COMPETITORS.identity"}
    for score in report["rivals"].values():
        assert score["canonical_fit"] == 0 and score["canonical_total"] == 3
        assert score["local_refuted"] == 16
        assert score["minimal_witness"]["validator"]["accepted"]
    class CorruptCatalog(Catalog):
        def apply(self, task, grids, **options):
            record = super().apply(task, grids, **options)
            record["results"][0]["output"][0][0] = 9
            return record
    assert probe.build_report(generator, CorruptCatalog(), source, find_root(__file__), binary_only=True)["verdict"] == "FAIL"


def test_output_overwrite_is_rejected_before_authority(probe, tmp_path):
    out = tmp_path / "existing.json"
    out.write_text("keep\n")
    with pytest.raises(SystemExit) as caught:
        probe.main(["--out", str(out)])
    assert caught.value.code == 2
    assert out.read_text() == "keep\n"
