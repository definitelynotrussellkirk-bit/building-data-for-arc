"""Exercise real reference generation, legacy projections and failed export accounting."""
import json
import shutil

import pytest

from arcpuzzles import Catalog, datasets
from arcpuzzles.catalog import jsonl


TASK = "6c68e1b008a5"


def test_export_rejects_conflicting_options_before_creating_output(tmp_path):
    catalog = Catalog()
    output = tmp_path / "invalid"
    for options in ({"filters": {"approved": False}}, {"render": "chatml"},
                    {"max_attempts": 0}, {"filters": {"limit": 2}}, {"task_ids": []}):
        with pytest.raises(ValueError):
            catalog.export(output, count=1, **options)
        assert not output.exists()


@pytest.mark.skipif(shutil.which("racket") is None, reason="Racket runtime required")
def test_chat_exports_keep_all_queries_and_private_answers(tmp_path):
    catalog = Catalog()
    options = dict(count=1, task_ids=[TASK], seed=17, n_train=2, n_test=2)
    grids, code = tmp_path / "grids", tmp_path / "code"
    first = catalog.export(grids, style="grids", render="chatml", **options)
    second = catalog.export(code, style="code", render="harmony", **options)
    assert first["rendered_rows"] == 2 and second["rendered_rows"] == 1
    assert datasets.verify_dataset(grids) == first
    assert datasets.verify_dataset(code) == second
    assert (grids / "public.jsonl").read_bytes() == (code / "public.jsonl").read_bytes()
    task, = jsonl(grids / "public.jsonl")
    labels, = jsonl(grids / "labels.private.jsonl")
    lineage, = jsonl(grids / "lineage.private.jsonl")
    assert lineage["verified"] is False and lineage["family_id"] is None
    assert lineage["reasons"] == ["missing_or_ambiguous_lineage"]
    assert lineage["episode_id"] == labels["episode_id"]
    assert set(task) == {"episode_id", "train", "test"}
    assert all(set(p) == {"input"} for p in task["test"])
    rows = jsonl(grids / "data.private.jsonl")
    assert [r["query_index"] for r in rows] == [0, 1]
    for i, row in enumerate(rows):
        expected = "".join("".join(str(v) for v in line) + "\n" for line in labels["test_outputs"][i])
        assert row["messages"][-1] == {"role": "assistant", "content": expected}
    assert "<|start|>assistant<|channel|>final<|message|>" in jsonl(code / "data.private.jsonl")[0]["text"]
    with pytest.raises(FileExistsError):
        catalog.export(grids, **options)
    (grids / "labels.private.jsonl").write_text("{}\n")
    with pytest.raises(ValueError, match="changed"):
        datasets.verify_dataset(grids)


@pytest.mark.skipif(shutil.which("racket") is None, reason="Racket runtime required")
def test_dsl_export_preserves_query_and_execution_targets(tmp_path):
    output = tmp_path / "dsl"
    result = Catalog().export(output, count=1, task_ids=[TASK], seed=17, n_train=2,
                              style="dsl", modes=["predict", "exec"])
    assert result["status"] == "complete"
    assert result["row_counts"] == {"<predict>": 1, "<exec>": 2}
    episode, = jsonl(output / "episodes.private.jsonl")
    rows = jsonl(output / "data.private.jsonl")
    assert all(row["source_provenance"]["approved"] for row in rows)
    assert all(row["episode_id"] == episode["episode_id"] for row in rows)
    predict = next(r for r in rows if r["task_type"] == "<predict>")
    assert "<predict>" == predict["input_tokens"][0]
    assert predict["program_tokens"]  # Integer-grid target, never a gold program.
    assert datasets.verify_dataset(output)["rendered_rows"] == 3


def test_failed_generation_keeps_receipt_and_never_reports_complete(tmp_path, monkeypatch):
    def fail(*args, **kwargs):
        raise datasets.GenerationFailure(TASK, {"exit_code": 7, "timed_out": False,
                                                "stderr": "reproducible fixture failure", "stdout": ""})
    monkeypatch.setattr(datasets, "generate_in_runtime", fail)
    output = tmp_path / "failed"
    result = Catalog().export(output, count=1, task_ids=[TASK], max_attempts=2)
    assert result["status"] == "incomplete" and result["attempted_episodes"] == 2
    assert result["accepted_episodes"] == 0
    failures = jsonl(output / "rejections.jsonl")
    assert len(failures) == 2 and failures[0]["process"]["exit_code"] == 7
    assert json.loads((output / "manifest.json").read_text()) == result
    with pytest.raises(ValueError, match="not a complete"):
        datasets.verify_dataset(output)


@pytest.mark.skipif(shutil.which("racket") is None, reason="Racket runtime required")
def test_export_binds_verified_official_lineage_without_exposing_it(tmp_path):
    output = tmp_path / "verified-lineage"
    result = Catalog().export(output, count=1, task_ids=["1674812130ff"],
                              seed=17, n_train=2, n_test=2, max_attempts=2,
                              timeout=30)
    assert result["status"] == "complete"
    row, = jsonl(output / "lineage.private.jsonl")
    label, = jsonl(output / "labels.private.jsonl")
    public, = jsonl(output / "public.jsonl")
    assert row["episode_id"] == label["episode_id"] == public["episode_id"]
    assert row["verified"] is True
    assert row["family_id"] == "official:training:e729b7be"
    assert row["generator_sha256"] == label["provenance"]["generator_sha256"]
    assert row["evidence"]["source_hashes"]["generator_sha256"] == row["generator_sha256"]
    assert "family_id" not in public and "evidence" not in public
    assert datasets.verify_dataset(output) == result

    row["family_id"] = "official:training:00000000"
    (output / "lineage.private.jsonl").write_text(json.dumps(row) + "\n")
    manifest = json.loads((output / "manifest.json").read_text())
    path = output / "lineage.private.jsonl"
    manifest["files"][path.name] = {"sha256": datasets.sha256(path), "bytes": path.stat().st_size}
    manifest["dataset_id"] = datasets._identity({k: v for k, v in manifest.items() if k != "dataset_id"})
    (output / "manifest.json").write_text(json.dumps(manifest) + "\n")
    with pytest.raises(ValueError, match="lineage"):
        datasets.verify_dataset(output)
