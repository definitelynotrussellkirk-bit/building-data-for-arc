"""Bounded sampler coverage; run via review.py run. No Racket execution."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import time

from reviewer_support import find_root


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise ValueError("output must be new")
    root = find_root(__file__)
    path = root / "generators/0083f06314c3/workspace/parametric/prototype.py"
    spec = importlib.util.spec_from_file_location("orientation_sampling", path)
    prototype = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prototype)
    started, rows, failures = time.monotonic(), [], []
    requests = [(seed, demos) for seed in range(7) for demos in range(2, 7)]
    requests.append((2**63-1, 3))
    for setting in prototype.SETTINGS:
        for seed, demos in requests:
            try:
                episode = prototype.generate(seed, setting, demos, 4)
                teach = prototype.teaching_check({"settings": setting, "train": episode["train"][:2]})
                assert not teach["surviving_rivals"]
                pairs = episode["train"] + episode["test"]
                assert len({json.dumps(p["input"]) for p in pairs}) == demos+4
                large = episode["test"][3]["input"]
                assert len(large) == len(large[0]) == 30
                board = prototype._parts(large)[2]
                assert all(any(row[c] for row in board) for c in (0, len(board[0])-1))
                assert all(any(board[r]) for r in (0, len(board)-1))
                rows.append({"seed": seed, "settings": setting, "demos": demos, "queries": 4,
                             "two_demo_teaching": teach,
                             "stress_board_nonzero": sum(bool(v) for row in board for v in row)})
            except Exception as error:
                failures.append({"seed": seed, "settings": setting, "demos": demos,
                                 "error": type(error).__name__+": "+str(error)})
    report = {"schema": "arcpuzzles-bounded-sampling-check-v1", "task_id": prototype.TASK_ID,
              "status": "failed" if failures else "passed", "requested": len(requests)*2,
              "successful": len(rows), "failures": failures,
              "elapsed_seconds": round(time.monotonic()-started, 3),
              "prototype_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
              "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "canonical_generator_sha256": prototype.BASE_SHA256,
              "rows": rows, "racket_executions": 0,
              "limits": "Python constructive sampling and finite demo-only rivals; authoritative labels require protected-Racket qualification."}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x") as stream:
        json.dump(report, stream, indent=2)
        stream.write("\n")
    print(json.dumps({k: report[k] for k in ("status", "requested", "successful", "failures", "elapsed_seconds")}))
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
