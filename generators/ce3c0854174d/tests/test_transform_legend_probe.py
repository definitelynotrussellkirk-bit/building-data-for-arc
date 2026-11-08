"""Behavioral checks for the standalone visible-example ambiguity probe."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

from reviewer_support import find_root


def load_probe():
    root = find_root(__file__)
    paths = [root / "generators/ce3c0854174d/workspace/transform_legend_probe.py",
             root / "puzzle_generators/per_puzzle/ce3c0854174d/workspace/transform_legend_probe.py"]
    path = next((path for path in paths if path.is_file()), None)
    assert path is not None, "Standalone legend probe has not been implemented"
    spec = importlib.util.spec_from_file_location("legend_probe_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def grid(script, square=False):
    result = [[0] * 8 for _ in range(6)]
    result[0][:len(script)] = script
    result[2][1:3] = [7, 7] if square else [7, 0]
    result[3][1:4] = [7, 7, 0] if square else [7, 7, 7]
    return result


def challenge(unseen=False):
    return {"train": [{"input": grid([1]), "output": [[7, 7], [7, 0], [7, 0]]}],
            "test": [{"input": grid([4] if unseen else [1])}]}


def test_identifies_observed_asymmetric_transform_and_predicts_query():
    module, _ = load_probe()
    report = module.analyze(challenge())
    assert report["status"] == "identifiable"
    assert report["candidates"]["1"] == ["cw90"]
    assert report["queries"][0]["predictions"][0]["output"] == [[7, 7], [7, 0], [7, 0]]


def test_unseen_symbol_retains_two_incompatible_query_predictions():
    module, _ = load_probe()
    report = module.analyze(challenge(unseen=True))
    assert report["status"] == "ambiguous"
    predictions = report["queries"][0]["predictions"]
    assert len(predictions) == 2
    assert predictions[0]["output"] != predictions[1]["output"]


def test_nonunique_legend_is_not_a_false_positive_when_query_is_equivalent():
    module, _ = load_probe()
    pair = {"input": grid([1], square=True), "output": [[7, 7], [7, 7]]}
    report = module.analyze({"train": [pair], "test": [{"input": pair["input"]}]})
    assert len(report["candidates"]["1"]) == 8
    assert report["status"] == "identifiable"


def test_top_aligned_gallery_tracks_cumulative_state():
    module, _ = load_probe()
    pair = {"input": grid([1, 3]),
            "output": [[7, 7, 0, 7, 7], [7, 0, 0, 0, 7], [7, 0, 0, 0, 7]]}
    report = module.analyze({"train": [pair], "test": [{"input": pair["input"]}]})
    assert report["candidates"]["1"] == ["cw90"]
    assert report["candidates"]["3"] == ["flip_lr"]
    assert report["status"] == "identifiable"


def test_inconsistent_visible_label_is_reported():
    module, _ = load_probe()
    task = challenge()
    task["train"][0]["output"] = [[7]]
    assert module.analyze(task)["status"] == "inconsistent"


def test_query_labels_are_ignored_and_input_is_not_mutated():
    module, _ = load_probe()
    task = challenge(unseen=True)
    task["test"][0]["output"] = [[8]]
    before = copy.deepcopy(task)
    assert module.analyze(task)["status"] == "ambiguous"
    assert task == before


def test_truncated_enumeration_cannot_claim_identifiability():
    module, _ = load_probe()
    report = module.analyze(challenge(unseen=True), max_mappings=1)
    assert report["status"] == "incomplete"


def test_cli_emits_retained_ambiguity_with_nonzero_exit(tmp_path):
    _, path = load_probe()
    source, output = tmp_path / "challenge.json", tmp_path / "report.json"
    source.write_text(json.dumps(challenge(unseen=True)))
    result = subprocess.run([sys.executable, str(path), "--challenge", str(source),
                             "--out", str(output)], capture_output=True, text=True)
    assert result.returncode == 1, result.stderr
    assert json.loads(output.read_text())["status"] == "ambiguous"
