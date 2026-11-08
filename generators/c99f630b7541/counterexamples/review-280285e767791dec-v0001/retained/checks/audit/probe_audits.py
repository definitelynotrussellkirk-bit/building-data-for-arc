from __future__ import annotations

import json
from pathlib import Path
from reviewer_support import find_root, load_selected_generator

HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)


def dump(task: str, payload: dict) -> None:
    out = HERE / task
    out.mkdir(parents=True, exist_ok=True)
    (out / "audit_record.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def probe_rank_blobs() -> None:
    task = "2c4317f69f0a"
    gen, source, sha = load_selected_generator(task, root=ROOT)
    collisions = {"palette_kind": {}, "texture": {}}
    samples = range(100)
    for value in ("warm", "cool", "varied"):
        same = 0
        for i in samples:
            a = gen.generate("audit-dead-palette", i, difficulty="medium", palette_kind="default")
            b = gen.generate("audit-dead-palette", i, difficulty="medium", palette_kind=value)
            same += a == b
        collisions["palette_kind"][value] = {"identical": same, "total": 100}
    for value in ("warm", "cool", "varied"):
        same = 0
        for i in samples:
            a = gen.generate("audit-dead-texture", i, difficulty="medium", texture="default")
            b = gen.generate("audit-dead-texture", i, difficulty="medium", texture=value)
            same += a == b
        collisions["texture"][value] = {"identical": same, "total": 100}

    rejected = []
    for axis in ("grid_h", "grid_w"):
        for value in (7, 13, 14):
            try:
                grid = gen.generate("audit-axis-domain", 0, **{axis: value})
                rejected.append({"axis": axis, "value": value, "accepted": True,
                                 "shape": [len(grid), len(grid[0])]})
            except Exception as exc:
                rejected.append({"axis": axis, "value": value, "accepted": False,
                                 "exception": type(exc).__name__, "message": str(exc)})

    failures = []
    for i in range(1000):
        grid = gen.generate("audit-selfcheck", i)
        errs = gen.self_check(grid, difficulty=None, meta={})
        if errs:
            failures.append({"sample_index": i, "errors": errs, "grid": grid})
            if len(failures) == 5:
                break

    example = gen.generate("audit-dead-palette", 0, difficulty="medium", palette_kind="default")
    (HERE / task / "input.json").write_text(json.dumps(example, indent=2) + "\n")
    dump(task, {
        "schema": "review-audit-probe-v1",
        "task_id": task,
        "source_path": str(source.relative_to(ROOT)),
        "source_sha256": sha,
        "finding": "advertised meaningful controls are dead and advertised grid domains are rejected",
        "paired_collisions": collisions,
        "advertised_domain_trials": rejected,
        "ordinary_selfcheck_scan": {"samples": 1000, "failures_found": failures},
        "command": ["python3", "review.py", "run", "python3", "../checks/audit/probe_audits.py"],
        "cwd": "packet_root",
    })


def probe_cross() -> None:
    task = "c99f630b7541"
    gen, source, sha = load_selected_generator(task, root=ROOT)
    same = 0
    selfcheck_failures = []
    for i in range(100):
        a = gen.generate("audit-dead-booleans", i, difficulty="medium",
                         asymmetry=False, anchor_corner=False)
        b = gen.generate("audit-dead-booleans", i, difficulty="medium",
                         asymmetry=True, anchor_corner=True)
        same += a == b
        errs = gen.self_check(b, difficulty="medium", meta={})
        if errs:
            selfcheck_failures.append({"sample_index": i, "errors": errs})

    trials = []
    for axis in ("n_eights", "n_twos"):
        for value in (1, 5, 6, 7, 8):
            try:
                grid = gen.generate("audit-count-domain", 0, difficulty="medium", **{axis: value})
                trials.append({"axis": axis, "value": value, "accepted": True,
                               "shape": [len(grid), len(grid[0])]})
            except Exception as exc:
                trials.append({"axis": axis, "value": value, "accepted": False,
                               "exception": type(exc).__name__, "message": str(exc)})

    example = gen.generate("audit-dead-booleans", 0, difficulty="medium",
                           asymmetry=False, anchor_corner=False)
    (HERE / task / "input.json").write_text(json.dumps(example, indent=2) + "\n")
    dump(task, {
        "schema": "review-audit-probe-v1",
        "task_id": task,
        "source_path": str(source.relative_to(ROOT)),
        "source_sha256": sha,
        "finding": "two advertised booleans are dead and advertised count domains exceed runtime domains",
        "paired_boolean_collision": {"identical": same, "total": 100,
                                      "self_check_failures": selfcheck_failures},
        "advertised_domain_trials": trials,
        "prior_unresolved_audit_reproduced": True,
        "command": ["python3", "review.py", "run", "python3", "../checks/audit/probe_audits.py"],
        "cwd": "packet_root",
    })


if __name__ == "__main__":
    probe_rank_blobs()
    probe_cross()
    print(json.dumps({"probed": ["2c4317f69f0a", "c99f630b7541"]}))
