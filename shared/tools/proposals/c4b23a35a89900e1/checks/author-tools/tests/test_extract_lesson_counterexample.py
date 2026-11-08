import json
import subprocess
import sys
from pathlib import Path

TOOL = Path(__file__).resolve().parents[1] / "extract_lesson_counterexample.py"


def test_extracts_named_rotation_witness_and_sidecars(tmp_path: Path) -> None:
    report = {
        "schema": "summary-v1",
        "task_id": "abc",
        "source_binding": {"generator_sha256": "g", "rule_callable_sha256": "r"},
        "status": "ambiguous",
        "summary": {"ambiguous_rotations": 1},
        "first_witnesses": {
            "declared:CANONICAL_SHORTCUTS:shortcut": {
                "scope": "rotation",
                "recipe": {"band": "easy", "seed": 7, "sample_index": 3},
                "query_index": 2,
                "train_indices": [0, 1, 3, 4],
                "warnings": ["shortcut survives"],
                "instance": {"train": [], "test": []},
                "prediction": {
                    "query_index": 0,
                    "input": [[1, 0]],
                    "expected_output": [[1, 0]],
                    "rival_output": [[0, 0]],
                },
            }
        },
    }
    report_path = tmp_path / "summary.json"
    report_path.write_text(json.dumps(report))
    out = tmp_path / "counterexample.json"
    subprocess.run(
        [sys.executable, str(TOOL), str(report_path), "--rival", "shortcut", "--out", str(out)],
        check=True,
    )
    extracted = json.loads(out.read_text())
    assert extracted["task_id"] == "abc"
    assert extracted["witness_key"] == "declared:CANONICAL_SHORTCUTS:shortcut"
    assert extracted["prediction"]["rival_output"] == [[0, 0]]
    assert json.loads((tmp_path / "counterexample.query-input.json").read_text()) == [[1, 0]]
    assert json.loads((tmp_path / "counterexample.expected-output.json").read_text()) == [[1, 0]]
    assert json.loads((tmp_path / "counterexample.rival-output.json").read_text()) == [[0, 0]]
