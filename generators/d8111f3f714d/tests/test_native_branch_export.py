"""Projection/publication checks; reference labels are exercised by make_examples."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import find_root, public_challenge_bytes


ROOT = find_root(__file__)
HOME = ROOT / "generators/d8111f3f714d/workspace/parametric"


def load(name):
    spec = importlib.util.spec_from_file_location("_branch_export_test_" + name, HOME / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def episode(offset=0):
    # Format-only fixtures, not claimed to satisfy the branch puzzle grammar.
    pairs = []
    for index in range(7):
        grid = [[0] * 10 for _ in range(10)]
        grid[index + 1][offset + 1] = 2
        output = deepcopy(grid)
        output[index + 1][offset + 2] = 3
        pairs.append({"input": grid, "output": output, "private_pair_note": index})
    return {"train": pairs[:3], "test": pairs[3:],
            "program_solution": "private exact source", "parameters": {"branch_direction": "toward_trunk"},
            "meta": {"seed": 17, "private_note": "retained"}}


def test_saved_actor_projections_have_exact_ids_and_complete_private_records(tmp_path):
    export = load("export")
    episodes = [episode(0), episode(3)]
    folder = tmp_path / "batch"
    manifest = export.write_episodes(episodes, folder, context={"test_only": True})
    assert manifest["complete"] is True and manifest["training_admitted"] is False
    assert manifest["native_acceptance"] == "owner_pending"
    metadata = [json.loads(line) for line in (folder / "private/metadata.jsonl").read_text().splitlines()]
    assert [row["controller_id"] for row in metadata] == sorted(row["controller_id"] for row in metadata)
    assert len(list((folder / "turns").glob("*.json"))) == 8
    assert len(list((folder / "private/controllers").glob("*.json"))) == 2
    for row in metadata:
        original = next(item for item in episodes if item == row["episode"])
        assert len(row["turn_ids"]) == 4
        controller = folder / "private/controllers" / (row["controller_id"] + ".json")
        assert controller.read_bytes() == public_challenge_bytes(original)
        for identifier, pair in zip(row["turn_ids"], original["test"], strict=True):
            raw = (folder / "turns" / (identifier + ".json")).read_bytes()
            assert hashlib.sha256(raw).hexdigest() == identifier
            assert raw == public_challenge_bytes({"train": original["train"], "test": [pair]})
            public = json.loads(raw)
            assert set(public) == {"train", "test"}
            assert len(public["test"]) == 1 and set(public["test"][0]) == {"input"}
            assert all(set(pair) == {"input", "output"} for pair in public["train"])
    files = {p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file()}
    assert files == set(manifest["files"]) | {"manifest.json"}
    assert all(hashlib.sha256((folder / name).read_bytes()).hexdigest() == digest
               for name, digest in manifest["files"].items())
    assert json.loads((folder / "private/context.json").read_bytes()) == {"test_only": True}


def test_first_turn_ignores_private_metadata_future_inputs_and_total_query_count():
    export = load("export")
    original = episode()
    first = export.turn_bytes(original, 0)
    hidden = deepcopy(original)
    hidden["parameters"] = {"branch_direction": "away_to_edge"}
    hidden["program_solution"] = "different private program"
    hidden["meta"] = {"seed": 999999, "query_count": 4}
    hidden["test"][0]["output"][0][0] = 3
    hidden["test"][3]["input"][0][0] = 2
    assert export.turn_bytes(hidden, 0) == first
    hidden["test"] = hidden["test"][:1]
    assert export.turn_bytes(hidden, 0) == first
    visible = deepcopy(original)
    visible["train"][0]["output"][0][0] = 3
    assert export.turn_bytes(visible, 0) != first
    for invalid in (True, -1, 4, 0.0):
        with pytest.raises(ValueError):
            export.turn_bytes(original, invalid)


def test_writer_rejects_noninteger_visible_and_private_label_cells_before_creation(tmp_path):
    export = load("export")
    for index, (split, key, value) in enumerate([
        ("train", "input", True), ("train", "output", 3.0),
        ("test", "input", False), ("test", "output", 3.0),
        ("test", "output", float("nan")), ("test", "output", 10),
    ]):
        bad = episode()
        bad[split][0][key][0][0] = value
        folder = tmp_path / str(index)
        with pytest.raises(ValueError):
            export.write_episodes([bad], folder)
        assert not folder.exists()


def test_writer_rejects_counts_shapes_duplicates_and_invalid_json_before_creation(tmp_path):
    export = load("export")
    bads = []
    bad = episode(); bad["train"] = bad["train"][:1]; bads.append(bad)
    bad = episode(); bad["test"] = []; bads.append(bad)
    bad = episode(); bad["test"][0]["output"].pop(); bads.append(bad)
    bad = episode(); bad["test"][0]["input"] = deepcopy(bad["train"][0]["input"]); bads.append(bad)
    bad = episode(); bad["meta"]["nonfinite"] = float("inf"); bads.append(bad)
    for index, bad in enumerate(bads):
        folder = tmp_path / str(index)
        with pytest.raises(ValueError):
            export.write_episodes([bad], folder)
        assert not folder.exists()
    with pytest.raises(ValueError):
        export.write_episodes([], tmp_path / "empty")


def test_duplicate_visible_turns_are_rejected_despite_different_private_answers(tmp_path):
    export = load("export")
    first = episode()
    second = deepcopy(first)
    second["meta"]["seed"] = 42
    second["test"][0]["output"][0][0] = 3
    second["test"][3]["input"][0][0] = 2
    folder = tmp_path / "duplicate"
    with pytest.raises(ValueError, match="duplicate"):
        export.write_episodes([first, second], folder)
    assert not folder.exists()


def test_existing_destination_and_dangling_symlink_are_never_overwritten(tmp_path):
    export = load("export")
    folder = tmp_path / "existing"
    folder.mkdir()
    marker = folder / "keep.txt"
    marker.write_text("keep")
    with pytest.raises(FileExistsError):
        export.write_episodes([episode()], folder)
    assert marker.read_text() == "keep"
    link = tmp_path / "dangling"
    link.symlink_to(tmp_path / "missing", target_is_directory=True)
    with pytest.raises(FileExistsError):
        export.write_episodes([episode()], link)
    assert link.is_symlink()


def test_publication_failure_does_not_publish_a_complete_manifest(tmp_path, monkeypatch):
    export = load("export")
    original = Path.open
    def fail_actor_file(self, *args, **kwargs):
        if self.parent.name == "turns":
            raise OSError("simulated interrupted publication")
        return original(self, *args, **kwargs)
    monkeypatch.setattr(Path, "open", fail_actor_file)
    folder = tmp_path / "interrupted"
    with pytest.raises(OSError, match="interrupted"):
        export.write_episodes([episode()], folder)
    assert not (folder / "manifest.json").exists()


def test_example_builder_refuses_an_unprotected_execution_claim(tmp_path, monkeypatch):
    builder = load("make_examples")
    monkeypatch.setattr(builder, "evaluate_contract", lambda *a, **k:
                        {"racket": {"backend": "test", "protected": False}})
    folder = tmp_path / "not_native"
    report = tmp_path / "report.json"
    with pytest.raises(ValueError, match="protected Racket"):
        builder.build_examples(folder, report=report, seed=0, demos=3, queries=4)
    assert not folder.exists() and not report.exists()
