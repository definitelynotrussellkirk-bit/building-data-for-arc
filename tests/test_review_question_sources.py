import json
import hashlib

from arcpuzzles.catalog import Catalog
from arcpuzzles.review_question_sources import export_question_sources


def test_source_bundle_registers_generators_with_zero_instances(library, tmp_path):
    result = export_question_sources(Catalog(library), tmp_path / "sources")
    rows = [json.loads(l) for l in (tmp_path / "sources/generators.jsonl").read_text().splitlines()]
    assert len(rows) == 3
    assert all(len(r["generator_hash"]) == 64 for r in rows)
    assert result["counts"]["questions"] == 0


def test_export_with_a_late_invalid_episode_is_quarantined_entirely(library, tmp_path):
    directory = library / "var/datasets/broken"
    directory.mkdir(parents=True)
    public = {"train": [{"input": [[1]], "output": [[2]]}], "test": [{"input": [[3]]}]}
    rows = [{"episode_id": "first", **public}, {"episode_id": "second", **public}]
    labels = [{"episode_id": "first", "task_id": "fixture", "test_outputs": [[[4]]],
               "provenance": {"generator_sha256": "a" * 64}},
              {"episode_id": "second", "task_id": "fixture", "test_outputs": [[[4]]]}]
    files = {}
    for name, content in (("public.jsonl", rows), ("labels.private.jsonl", labels)):
        raw = "".join(json.dumps(row) + "\n" for row in content).encode()
        (directory / name).write_bytes(raw)
        files[name] = {"sha256": hashlib.sha256(raw).hexdigest()}
    (directory / "manifest.json").write_text(json.dumps({"files": files}))
    result = export_question_sources(Catalog(library), tmp_path / "sources")
    assert result["counts"]["questions"] == 0
    assert result["counts"]["generators"] == 3
    assert result["counts"]["excluded_exports"] == 1
