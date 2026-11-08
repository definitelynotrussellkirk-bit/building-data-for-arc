"""Exercise the saved-lesson command at its untrusted-data boundary."""
import copy
import json
from pathlib import Path
import subprocess
import sys

import pytest
from reviewer_support import canonical_pairs, find_root


def _workspace():
    root = find_root(__file__)
    for path in (root / "generators/2f58238f8bb6/workspace",
                 root / "puzzle_generators/per_puzzle/2f58238f8bb6/workspace"):
        if (path / "check_lesson.py").is_file():
            return path
    raise AssertionError("task workspace was not copied into the runtime")


def _run(tmp_path, lesson):
    path = tmp_path / "lesson.json"
    path.write_text(json.dumps(lesson))
    return subprocess.run([sys.executable, str(_workspace() / "check_lesson.py"), str(path)],
                          text=True, capture_output=True, timeout=30)


def _canonical_lesson():
    pairs = canonical_pairs("2f58238f8bb6", root=find_root(__file__))
    return {"train": copy.deepcopy(pairs[:2]), "test": [{"input": pairs[2]["input"]}]}


def test_cli_accepts_valid_lesson_without_consulting_query_label(tmp_path):
    lesson = _canonical_lesson()
    lesson["test"][0]["output"] = "deliberately invalid and irrelevant"
    result = _run(tmp_path, lesson)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["query_labels_consulted"] is False


@pytest.mark.parametrize("mutation", ["float_input", "float_label", "empty_query_keys"])
def test_cli_rejects_invalid_arc_data_before_mapping_check(tmp_path, mutation):
    lesson = _canonical_lesson()
    if mutation == "float_input":
        lesson["train"][0]["input"] = [[float(v) for v in row] for row in lesson["train"][0]["input"]]
    elif mutation == "float_label":
        lesson["train"][0]["output"] = [[float(v) for v in row] for row in lesson["train"][0]["output"]]
    else:
        lesson["test"][0]["input"][0] = [0] * len(lesson["test"][0]["input"][0])
    result = _run(tmp_path, lesson)
    assert result.returncode == 2, result.stdout + result.stderr
    assert json.loads(result.stderr)["status"] == "error"
