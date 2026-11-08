"""Compare valid draws and malformed calls with this task in an original ZIP.

Run through review.py run; the baseline module is explicitly executed as trusted
review input. This authoring probe never opens solve episodes or private labels.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import types
import zipfile

from reviewer_support import find_root, load_selected_generator


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def outcome(module, kwargs):
    try:
        return {"status": "accepted", "grid": module.generate(**kwargs)}
    except (TypeError, ValueError) as exc:
        return {"status": "rejected", "exception": type(exc).__name__, "message": str(exc)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-zip", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error("output must be new")
    root = find_root(__file__)
    task = "7a37505e7bd0"
    current, current_path, current_sha = load_selected_generator(task, root=root)
    with zipfile.ZipFile(args.source_zip) as archive:
        baseline_path = f"WORK/repo/generators/{task}/generator.py"
        baseline_bytes = archive.read(baseline_path)
        base_relative = "shared/runtime/puzzle_generators/base.py"
        base_bytes = archive.read("WORK/repo/" + base_relative)
        if base_bytes != (root / base_relative).read_bytes():
            raise ValueError("shared generator API differs from original packet")
    baseline = types.ModuleType("_review_original_controls")
    baseline.__file__ = baseline_path
    exec(compile(baseline_bytes, baseline_path, "exec"), baseline.__dict__)
    original_rows, current_rows, mismatches = [], [], []
    seeds = [-17, 0, 1, 17, 991, 2**63]
    bands = [None, "easy", "medium", "hard"]
    for seed in seeds:
        for band in bands:
            for index in range(10):
                for controls in [{}, {"color_count": None}, *({"color_count": n} for n in range(1, 6))]:
                    kwargs = {"seed": seed, "sample_index": index, "difficulty": band, **controls}
                    before, after = baseline.generate(**kwargs), current.generate(**kwargs)
                    original_rows.append({"kwargs": kwargs, "grid": before})
                    current_rows.append({"kwargs": kwargs, "grid": after})
                    if before != after:
                        mismatches.append({"kwargs": kwargs, "before": before, "after": after})
    malformed = []
    for field, value in [("seed", True), ("sample_index", False), ("sample_index", -1),
                         ("difficulty", "__invalid_difficulty__"), ("difficulty", 1.0),
                         ("color_count", True), ("color_count", "5"), ("color_count", 1.75)]:
        kwargs = {"seed": 991, "sample_index": 0, "difficulty": "medium", field: value}
        malformed.append({"kwargs": kwargs, "before": outcome(baseline, kwargs),
                          "after": outcome(current, kwargs)})
    result = {
        "schema": "arcpuzzles-task-controls-comparison-v1", "task_id": task,
        "command": [sys.executable, *sys.argv], "cwd": str(Path.cwd()),
        "baseline_member": baseline_path,
        "baseline_generator_sha256": hashlib.sha256(baseline_bytes).hexdigest(),
        "generator_sha256": current_sha, "generator_path": str(current_path),
        "shared_base_sha256": hashlib.sha256(base_bytes).hexdigest(),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "seed_values": seeds, "sample_indices": [0, 9], "difficulties": bands,
        "color_count_controls": ["omitted", None, 1, 2, 3, 4, 5],
        "valid_call_count": len(original_rows), "mismatch_count": len(mismatches),
        "baseline_draws_sha256": digest(original_rows), "final_draws_sha256": digest(current_rows),
        "mismatches": mismatches, "malformed_call_witnesses": malformed,
        "limitations": "Finite valid-input comparison; the same packet-bound shared API executes both modules.",
    }
    passed = not mismatches and all(row["before"]["status"] == "accepted" and
                                   row["after"]["status"] == "rejected" for row in malformed)
    result["passed"] = passed
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"passed": passed, "valid_call_count": len(original_rows),
                      "mismatch_count": len(mismatches), "malformed_witnesses": len(malformed)}))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
