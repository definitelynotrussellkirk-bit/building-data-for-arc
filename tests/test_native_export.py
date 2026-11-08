"""Verify native row completeness, target separation and portable tensor artifacts."""
import json
import shutil

import pytest

from arcpuzzles import Catalog
from arcpuzzles.catalog import jsonl
from arcpuzzles.datasets import verify_dataset


TASK = "6c68e1b008a5"
OPTIONS = dict(count=1, task_ids=[TASK], seed=17, n_train=2, n_test=2, style="native", difficulty="medium")


def test_native_option_conflicts_fail_before_creating_output(tmp_path):
    output = tmp_path / "invalid"
    for options in ({"tensors": "native", "group_queries": True},
                    {"tensors": "native", "n_train": 11}, {"canvas_size": True},
                    {"style": "grids", "group_queries": True}, {"tensors": "unknown"}):
        with pytest.raises(ValueError):
            Catalog().export(output, **dict(OPTIONS, **options))
        assert not output.exists()


@pytest.mark.skipif(shutil.which("racket") is None, reason="Racket runtime required")
def test_native_json_preserves_individual_and_grouped_queries(tmp_path):
    singles, grouped = tmp_path / "singles", tmp_path / "grouped"
    assert Catalog().export(singles, **OPTIONS)["rendered_rows"] == 2
    assert Catalog().export(grouped, group_queries=True, **OPTIONS)["rendered_rows"] == 1
    assert (singles / "public.jsonl").read_bytes() == (grouped / "public.jsonl").read_bytes()
    episode, = jsonl(singles / "episodes.private.jsonl")
    rows = jsonl(singles / "data.private.jsonl")
    combined, = jsonl(grouped / "data.private.jsonl")
    assert combined["format"] == "arc_native_episode_v2"
    assert combined["queries"] == episode["test"]
    assert [r["query"] for r in rows] == episode["test"]
    assert [r["query_index"] for r in rows] == [0, 1]
    assert all(r["demo_pairs"] == episode["train"] and r["format"] == "arc_native_episode_v1" for r in rows)
    assert all(r["difficulty"] == "medium" for r in [*rows, combined])
    assert all(r["source_provenance"]["approved"] and r["episode_id"] == episode["episode_id"] for r in rows)
    for directory in (singles, grouped):
        assert verify_dataset(directory)["status"] == "complete"
        public, = jsonl(directory / "public.jsonl")
        assert all(set(pair) == {"input"} for pair in public["test"])
        assert not list(directory.glob("*.safetensors"))


@pytest.mark.skipif(shutil.which("racket") is None, reason="Racket runtime required")
@pytest.mark.parametrize("kind,grouped", [("native", False), ("bottleneck", True)])
def test_private_tensors_preserve_labels_without_teacher_forcing(tmp_path, kind, grouped):
    torch = pytest.importorskip("torch")
    safetensors = pytest.importorskip("safetensors")
    from safetensors.torch import load_file

    output = tmp_path / kind
    manifest = Catalog().export(output, tensors=kind, group_queries=grouped, **OPTIONS)
    assert manifest["status"] == "complete"
    assert verify_dataset(output) == manifest
    public, = jsonl(output / "public.jsonl")
    private, = jsonl(output / "labels.private.jsonl")
    rows = jsonl(output / "data.private.jsonl")
    assert len(rows) == (1 if grouped else 2)
    for row in rows:
        artifact = row["tensor_artifact"]
        path = output / artifact["file"]
        values = load_file(str(path))
        assert set(values) == set(artifact["tensors"])
        assert all(t.device.type == "cpu" for t in values.values())
        with safetensors.safe_open(str(path), framework="pt") as stored:
            identity = json.loads(stored.metadata()["arcpuzzles"])
        assert identity["episode_id"] == public["episode_id"]
        indices = range(2) if grouped else [row["query_index"]]
        if kind == "native":
            target_mask = values["role_ids"] == 3
            assert torch.all(values["cell_ids"][target_mask] == 10)
            assert torch.all(values["labels"][~target_mask] == -100)
            labels = values["labels"][target_mask].reshape(1, 30, 30)
            inputs = values["cell_ids"][values["role_ids"] == 2].reshape(1, 30, 30)
        else:
            labels = values["labels"].reshape(2, 30, 30)
            inputs = values["query_input_ids"].reshape(2, 30, 30)
            assert values["query_mask"].tolist() == [True, True]
        for slot, query_index in enumerate(indices):
            expected = private["test_outputs"][query_index]
            h, w = len(expected), len(expected[0])
            assert labels[slot, :h, :w].tolist() == expected
            assert torch.all(labels[slot, h:, :] == -100)
            assert torch.all(labels[slot, :h, w:] == -100)
            inp = public["test"][query_index]["input"]
            assert inputs[slot, :len(inp), :len(inp[0])].tolist() == inp
    with path.open("ab") as damaged:
        damaged.write(b"changed")
    with pytest.raises(ValueError, match="changed"):
        verify_dataset(output)


@pytest.mark.skipif(shutil.which("racket") is None, reason="Racket runtime required")
def test_too_small_tensor_canvas_retains_failed_export(tmp_path):
    pytest.importorskip("torch")
    pytest.importorskip("safetensors")
    output = tmp_path / "too-small"
    result = Catalog().export(output, tensors="native", canvas_size=1, max_attempts=1, **OPTIONS)
    assert result["status"] == "incomplete" and result["accepted_episodes"] == 0
    assert len(jsonl(output / "episodes.private.jsonl")) == 1
    assert not jsonl(output / "public.jsonl")
    assert "exceeds canvas" in jsonl(output / "rejections.jsonl")[-1]["reason"]
    with pytest.raises(ValueError, match="not a complete"):
        verify_dataset(output)
