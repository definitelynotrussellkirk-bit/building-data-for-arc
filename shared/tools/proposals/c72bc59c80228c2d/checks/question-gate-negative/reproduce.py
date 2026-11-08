#!/usr/bin/env python3
"""Reproduce an episode-level hidden-rule ambiguity for the proposed gate."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path


def sha_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def json_sha(value) -> str:
    return sha_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def load_prototype(work: Path):
    path = work / "repo/generators/156bae9e7b79/workspace/parametric/prototype.py"
    spec = importlib.util.spec_from_file_location("triangle_growth_rate_prototype", path)
    if not spec or not spec.loader:
        raise RuntimeError(f"cannot load prototype at {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def make_grid(key: list[int], *, line_bottom: int) -> list[list[int]]:
    width = len(key)
    if width % 2 != 1 or key[width // 2] != 5:
        raise ValueError("key must have odd width and gray at its center")
    height = 5
    line_col = width // 2
    grid = [list(key)] + [[5] * width for _ in range(height - 1)]
    for row in range(1, line_bottom + 1):
        grid[row][line_col] = 8
    return grid


def main() -> None:
    from arc_repl.isolated_verifier import verify_candidate

    script = Path(__file__).resolve()
    work = script.parents[2]
    prototype, prototype_path = load_prototype(work)
    out = script.with_name("report.json")

    # All three demos have a one-row active line, so growth_rate is unobservable.
    # The query has two active rows, making rate 1 and rate 2 disagree on row 2.
    inputs = [
        make_grid([1, 2, 5, 3, 4], line_bottom=1),
        make_grid([6, 1, 5, 2, 7], line_bottom=1),
        make_grid([4, 3, 5, 9, 1], line_bottom=1),
        make_grid([1, 2, 5, 3, 4], line_bottom=2),
    ]
    racket_path = str(Path(os.environ["RACKET_PATH"]).resolve(strict=True))
    predictions = {}
    receipts = {}
    rule_rows = []
    for rate in prototype.ALLOWED_GROWTH_RATES:
        program = prototype.rule_source(rate)
        canary = {"input": inputs[0], "output": prototype.python_mirror(inputs[0], rate)}
        task = {"train": [canary], "test": [{"input": grid} for grid in inputs]}
        receipt = verify_candidate(task, program, racket_path=racket_path)
        if receipt.get("status") != "pass" or receipt.get("backend") != "racket":
            raise RuntimeError(f"Racket execution failed for growth_rate={rate}: {receipt}")
        observed = receipt["test_outputs"]
        expected = [prototype.python_mirror(grid, rate) for grid in inputs]
        if observed != expected:
            raise RuntimeError(f"Racket/Python mismatch for growth_rate={rate}")
        predictions[rate] = observed
        receipts[str(rate)] = receipt
        rule_rows.append({
            "growth_rate": rate,
            "program_sha256": sha_bytes(program.encode()),
            "canonical_default": rate == prototype.DEFAULT_GROWTH_RATE,
        })

    score = prototype.score_rotation(predictions, chosen_rate=1, query_index=3)
    rival = score["rivals"][0]
    if rival["status"] != "ambiguous_query" or rival["demonstration_mismatches"] or not rival["query_disagrees"]:
        raise RuntimeError(f"negative witness did not reproduce ambiguity: {score}")

    report = {
        "schema": "episode-parameter-ambiguity-counterexample-v1",
        "task_id": prototype.TASK_ID,
        "finding": "all visible demonstrations fit growth_rate 1 and 2, but the settings disagree on the query",
        "status": "reproduced",
        "chosen_parameters": {"growth_rate": 1},
        "rival_parameters": {"growth_rate": 2},
        "demonstration_count": 3,
        "query_index": 3,
        "score": score,
        "inputs": inputs,
        "input_sha256": [json_sha(grid) for grid in inputs],
        "outputs": {str(rate): outputs for rate, outputs in predictions.items()},
        "output_sha256": {str(rate): [json_sha(grid) for grid in outputs] for rate, outputs in predictions.items()},
        "rules": rule_rows,
        "receipts": receipts,
        "runtime": {
            "backend": "racket",
            "racket_path": racket_path,
            "racket_sha256": sha_bytes(Path(racket_path).read_bytes()),
        },
        "source_sha256": {
            prototype_path.relative_to(work / "repo").as_posix(): sha_bytes(prototype_path.read_bytes()),
            script.relative_to(work).as_posix(): sha_bytes(script.read_bytes()),
        },
        "scope": "Deliberate negative authoring witness outside the production sampler; it demonstrates the gate failure class, not a defect in the repaired canonical curriculum.",
        "cheapest_gate": "For each episode, compare every finite declared setting on the same demonstrations and query; block when a query-changing setting has zero demonstration mismatches.",
        "cwd": str(Path.cwd()),
    }
    out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "report": str(out), "score": score}, sort_keys=True))


if __name__ == "__main__":
    main()
