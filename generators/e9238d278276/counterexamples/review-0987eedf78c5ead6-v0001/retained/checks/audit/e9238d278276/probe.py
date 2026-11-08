"""Bounded, read-only source audit; Racket apply is the label authority.

Only this audit directory is written. No private runner imports are used.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
WORK = OUT.parents[2]
OUTER = WORK.parent
REPO = WORK / "repo"
PYTHON = WORK / ".venv/bin/python3"
TASK = "e9238d278276"
GENERATOR_HASH = "4f8315cf1cccc08a6944643a59c9d492ccba6c277a3af16ccbded3d8f2bab15e"
GENERATOR_PATH = REPO / "generators" / TASK / "generator.py"
AUTHORITY_PATH = REPO / "shared/data/base/solutions/banks/9f3a2c87618d/E41__e9238d278276.json"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def stable_pack(grid, *, start_row=0):
    """Independent diagnostic logic; its result is never treated as a label."""
    result = [[0] * len(grid[0]) for _ in grid]
    for col in range(len(grid[0])):
        values = [row[col] for row in grid[start_row:] if row[col] != 0]
        for row, value in enumerate(values):
            result[row][col] = value
    return result


def run_public_apply():
    argv = [
        str(PYTHON), "review.py", "run", str(PYTHON), "-m", "arcpuzzles",
        "apply", TASK, "--input", f"../checks/audit/{TASK}/input.json",
        "--out", f"../checks/audit/{TASK}/racket.json",
    ]
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    start = time.monotonic()
    result = subprocess.run(argv, cwd=OUTER, env=env, capture_output=True, text=True, timeout=180)
    for stream in ("stdout", "stderr"):
        (OUT / f"apply.{stream}.log").write_text(getattr(result, stream), encoding="utf-8")
    save("apply.command.json", {
        "argv": argv,
        "cwd": str(OUTER),
        "payload_cwd": str(REPO),
        "exit_code": result.returncode,
        "duration_seconds": time.monotonic() - start,
        "stdout": f"apply.stdout.log",
        "stderr": f"apply.stderr.log",
        "input_sha256": sha((OUT / "input.json").read_bytes()),
        "output_sha256": sha((OUT / "racket.json").read_bytes()) if (OUT / "racket.json").exists() else None,
    })
    if result.returncode:
        raise RuntimeError(result.stderr or result.stdout)
    print(result.stdout)
    print(result.stderr)


def prepare():
    assert sha(GENERATOR_PATH.read_bytes()) == GENERATOR_HASH
    sys.path.insert(0, str(REPO / "src"))
    from arcpuzzles import Catalog
    metadata = Catalog(REPO).get(TASK)
    save("metadata.json", metadata)

    # Import only the selected canonical source and its ordinary shared helpers.
    sys.path.insert(0, str(REPO / "shared/runtime"))
    spec = importlib.util.spec_from_file_location("e923_audited_generator", GENERATOR_PATH)
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)

    variant = metadata["variants"][0]
    program = variant["program_solution"]
    save("source_identity.json", {
        "task_id": TASK,
        "generator_path": str(GENERATOR_PATH.relative_to(REPO)),
        "generator_sha256": sha(GENERATOR_PATH.read_bytes()),
        "rule_hash": metadata["rule_hash"],
        "generator_declared_rule_hash": gen.RULE_HASH,
        "rule_program_utf8_sha256": sha(program.encode()),
        "rule_program": program,
        "authority_path": str(AUTHORITY_PATH.relative_to(REPO)),
        "authority_file_sha256": sha(AUTHORITY_PATH.read_bytes()),
    })

    cases = []
    def add(name, grid, source, **recipe):
        cases.append({
            "index": len(cases), "name": name, "source": source, **recipe,
            "input": grid,
            "self_check": gen.self_check(grid),
            "strict_canonical_like": gen.strict_canonical_like(grid),
            "observed_axes": gen.observe_overrides(grid),
            "top_row_nonzeros": sum(value != 0 for value in grid[0]),
            "diagnostic_upward_output": stable_pack(grid),
            "rival_output": stable_pack(grid, start_row=1),
        })

    for split in ("train", "test"):
        for i, pair in enumerate(variant[split]):
            add(f"canonical_{split}_{i}", pair["input"], "canonical", canonical_output=pair["output"])

    for band in ("easy", "medium", "hard"):
        for index in range(4):
            grid = gen.generate(923012, index, difficulty=band)
            add(f"generated_{band}_{index}", grid, "generated", seed=923012,
                sample_index=index, difficulty=band, overrides={})

    boundary_overrides = [
        {"grid_h": 6, "grid_w": 6, "n_cols": 3, "n_distinct_colors": 2, "order_profile": "mixed"},
        {"grid_h": 16, "grid_w": 16, "n_cols": 6, "n_distinct_colors": 9, "order_profile": "descending"},
        {"grid_h": 6, "grid_w": 16, "n_cols": 3, "n_distinct_colors": 9, "order_profile": "mixed"},
        {"grid_h": 16, "grid_w": 6, "n_cols": 6, "n_distinct_colors": 2, "order_profile": "descending"},
    ]
    for index, overrides in enumerate(boundary_overrides):
        grid = gen.generate(923099, index, difficulty="medium", **overrides)
        add(f"override_boundary_{index}", grid, "generated", seed=923099,
            sample_index=index, difficulty="medium", overrides=overrides)
        assert gen.observe_overrides(grid) == overrides

    witness = copy.deepcopy(variant["train"][0]["input"])
    assert witness[1][2] == 5 and witness[0][2] == 0
    witness[0][2], witness[1][2] = 5, 0
    add("top_row_retention_witness", witness, "hand_constructed_from_canonical_train_0",
        transformation="Move color 5 from (row=1,col=2) to (row=0,col=2); zero-based coordinates.",
        seed=None, sample_index=None, difficulty=None, overrides=None)
    assert gen.self_check(witness) == []
    assert gen.strict_canonical_like(witness) == []
    assert all(not case["self_check"] for case in cases)
    save("cases.json", cases)
    save("input.json", {"inputs": [case["input"] for case in cases]})
    save("witness.input.json", {"input": witness})
    save("prepare.receipt.json", {
        "argv": [str(PYTHON), str(OUT / "probe.py")], "cwd": str(Path.cwd()),
        "generated_input_count": 16, "canonical_input_count": 3,
        "hand_constructed_input_count": 1, "total_racket_inputs": len(cases),
        "generator_sha256_before": GENERATOR_HASH,
        "generator_sha256_after": sha(GENERATOR_PATH.read_bytes()),
        "domain_status": "All 20 inputs pass the selected generator's self_check.",
        "overrides_status": "All four tested explicit boundary overrides round-trip exactly.",
        "runner_imports": "None; direct canonical generator import and public arcpuzzles.Catalog read only.",
    })
    run_public_apply()
    assert sha(GENERATOR_PATH.read_bytes()) == GENERATOR_HASH
    print(f"Prepared {len(cases)} inputs; witness index is {len(cases) - 1}.")


if __name__ == "__main__":
    prepare()
