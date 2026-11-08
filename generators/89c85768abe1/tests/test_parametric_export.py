"""Real-runtime export checks and adversarial serialized-bundle checks."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[3]
EXPORTER = ROOT / "generators/89c85768abe1/workspace/parametric/export.py"


def load_exporter():
    assert EXPORTER.is_file(), "The task-local parametric exporter is missing"
    spec = importlib.util.spec_from_file_location("export_89c85768abe1_tests", EXPORTER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                       allow_nan=False) + "\n").encode()


def rows(path):
    return [json.loads(line) for line in path.read_bytes().splitlines()]


def rewrite_inventory(directory):
    manifest = json.loads((directory / "manifest.json").read_text())
    manifest["files"] = [
        {"path": path.relative_to(directory).as_posix(), "bytes": path.stat().st_size,
         "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        for path in sorted(directory.rglob("*"), key=lambda item: item.relative_to(directory).as_posix())
        if path.is_file() and path.name != "manifest.json"
    ]
    (directory / "manifest.json").write_bytes(encoded(manifest))


@pytest.fixture(scope="module")
def bundle(tmp_path_factory):
    exporter = load_exporter()
    destination = tmp_path_factory.mktemp("rectangle-export") / "batch"
    result = exporter.export(destination, seeds=[3], demos=3, queries=4)
    assert result["status"] == "verified"
    return destination


def test_exports_real_racket_labels_and_private_query_turn_mapping(bundle):
    exporter = load_exporter()
    result = exporter.verify(bundle)
    assert result["episodes"] == 2
    assert result["racket_labels"] == 14
    public = rows(bundle / "public.jsonl")
    private = rows(bundle / "private.jsonl")
    assert [row["episode_id"] for row in public] == sorted(row["episode_id"] for row in public)
    assert {row["settings"]["mode"] for row in private} == {"all", "largest_component"}
    for visible, hidden in zip(public, private):
        assert set(visible) == {"episode_id", "train", "test"}
        assert len(visible["train"]) == 3 and len(visible["test"]) == 4
        assert all(set(pair) == {"input"} for pair in visible["test"])
        assert hidden["racket"]["backend"] == "racket"
        assert hidden["racket"]["protected"] is True
        assert hidden["teaching"]["accepted"] is True
        assert len(hidden["turns"]) == 4
        for index, mapping in enumerate(hidden["turns"]):
            payload = (bundle / "turns" / (mapping["turn_id"] + ".json")).read_bytes()
            assert hashlib.sha256(payload).hexdigest() == mapping["turn_id"]
            assert mapping["query_index"] == index
            assert json.loads(payload) == {"train": visible["train"],
                "test": [{"input": hidden["test"][index]["input"]}]}


def test_public_and_turn_bytes_ignore_private_fields_and_future_queries():
    exporter = load_exporter()
    episode = {
        "train": [{"input": [[0, 2]], "output": [[2, 2]]}],
        "test": [{"input": [[3, 0]], "output": [[3, 3]]},
                 {"input": [[4, 0]], "output": [[4, 4]]}],
        "program_solution": "private original program", "seed": 17,
        "settings": {"mode": "all"},
    }
    public_before = encoded(exporter._public(episode))
    turn_before = encoded(exporter._turn(episode, 0))
    changed = copy.deepcopy(episode)
    changed.update(program_solution="different secret", seed=99,
                   settings={"mode": "largest_component"}, private_nonce="hidden")
    changed["test"][0]["output"] = [[9]]
    changed["test"][1]["output"] = [[8, 8]]
    assert encoded(exporter._public(changed)) == public_before
    assert encoded(exporter._turn(changed, 0)) == turn_before
    changed["test"][1]["input"] = [[7, 7, 7]]
    changed["test"].append({"input": [[6]], "output": [[6]]})
    assert encoded(exporter._turn(changed, 0)) == turn_before
    changed["test"] = changed["test"][:1]
    assert encoded(exporter._turn(changed, 0)) == turn_before


@pytest.mark.parametrize("change", ["public_mask", "public_id", "private_answer", "turn_future", "turn_order"])
def test_rehashed_tampering_is_rejected(bundle, tmp_path, change):
    exporter = load_exporter()
    destination = tmp_path / change
    shutil.copytree(bundle, destination)
    public = rows(destination / "public.jsonl")
    private = rows(destination / "private.jsonl")
    if change == "public_mask":
        public[0]["test"][0]["output"] = [[9]]
        (destination / "public.jsonl").write_bytes(b"".join(encoded(row) for row in public))
    elif change == "public_id":
        public[0]["episode_id"] = "0" * 64
        (destination / "public.jsonl").write_bytes(b"".join(encoded(row) for row in public))
    elif change == "private_answer":
        answer = private[0]["test"][0]["output"]
        answer[0][0] = (answer[0][0] + 1) % 10
        (destination / "private.jsonl").write_bytes(b"".join(encoded(row) for row in private))
    elif change == "turn_future":
        turn = private[0]["turns"][0]["turn_id"]
        path = destination / "turns" / (turn + ".json")
        value = json.loads(path.read_text())
        value["query_count"] = 4
        path.write_bytes(encoded(value))
    else:
        private[0]["turns"][0], private[0]["turns"][1] = private[0]["turns"][1], private[0]["turns"][0]
        (destination / "private.jsonl").write_bytes(b"".join(encoded(row) for row in private))
    rewrite_inventory(destination)
    expected_error = {
        "public_mask": "Public masked projection",
        "public_id": "Public IDs|public/private IDs",
        "private_answer": "Protected Racket label mismatch",
        "turn_future": "Turn visible prefix",
        "turn_order": "Private turn order",
    }[change]
    with pytest.raises(ValueError, match=expected_error):
        exporter.verify(destination)


@pytest.mark.parametrize("options", [
    {"demos": 0}, {"demos": 1}, {"demos": 7}, {"queries": 0}, {"queries": 5},
    {"queries": True}, {"seed": True},
    {"seeds": [3, 3]}, {"modes": ["all", "all"]}, {"modes": ["unknown"]},
])
def test_invalid_counts_and_duplicate_requests_create_no_output(tmp_path, options):
    exporter = load_exporter()
    destination = tmp_path / "must-not-exist"
    options = dict(options)
    if "seed" in options:
        options["seeds"] = [options.pop("seed")]
    with pytest.raises(ValueError):
        exporter.export(destination, **options)
    assert not destination.exists()


def test_duplicate_visible_challenges_are_refused_before_publication(tmp_path, monkeypatch):
    exporter = load_exporter()
    adapter = exporter._load_adapter()
    fixed = adapter.generate(3, {"mode": "all"}, 3, 4)
    # Force a visible collision with two real, valid episodes and real Racket labels.
    proxy = SimpleNamespace(
        generate=lambda seed, settings, demos, queries: copy.deepcopy(fixed),
        program=adapter.program, teaching_report=adapter.teaching_report,
        public_challenge=adapter.public_challenge, visible_turn=adapter.visible_turn,
    )
    monkeypatch.setattr(exporter, "_load_adapter", lambda: proxy)
    destination = tmp_path / "duplicate"
    with pytest.raises(ValueError, match="[Dd]uplicate visible"):
        exporter.export(destination, seeds=[3, 4], modes=["all"])
    assert not destination.exists()


def test_existing_destination_is_never_replaced(bundle):
    exporter = load_exporter()
    before = (bundle / "manifest.json").read_bytes()
    with pytest.raises(FileExistsError):
        exporter.export(bundle, seeds=[5])
    assert (bundle / "manifest.json").read_bytes() == before
