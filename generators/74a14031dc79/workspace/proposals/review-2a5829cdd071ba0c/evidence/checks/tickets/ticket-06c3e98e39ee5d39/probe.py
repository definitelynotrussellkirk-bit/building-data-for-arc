from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

TASK_ID = "66e63986855b"
TICKET_ID = "ticket-06c3e98e39ee5d39"
SEED_HEX = "7423d9cbb9ddd6fc6e4abbb1d5534073d4e00c67386a9f777aeb39bfd6dfdd7c"
EXPECTED_SOURCE_SHA256 = "8f78ef0944e40e80f9b86e9d5fdb2c9515fd05240e400d097e9993c5af79bc2f"
SOURCE = Path("generators") / TASK_ID / "generator.py"
EVIDENCE = Path("../checks/tickets") / TICKET_ID
INPUT_PATH = EVIDENCE / "input.json"
RACKET_PATH = EVIDENCE / "racket.json"
RESULT_PATH = EVIDENCE / "result.json"


def load_generator():
    spec = importlib.util.spec_from_file_location(f"ticket_{TASK_ID}", SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SOURCE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha_grid(grid) -> str:
    return hashlib.sha256(
        json.dumps(grid, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def differing_cells(left, right):
    return [
        [row, col, left[row][col], right[row][col]]
        for row in range(len(left))
        for col in range(len(left[0]))
        if left[row][col] != right[row][col]
    ]


def main() -> None:
    source_sha = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    if source_sha != EXPECTED_SOURCE_SHA256:
        raise AssertionError(f"pinned source drift: {source_sha}")
    module = load_generator()
    seed = int(SEED_HEX, 16)
    sample_index = 1  # Current v4 default schedule forces asymmetric_front on odd indices.
    grid = module.generate(seed, sample_index)
    errors = module.strict_canonical_like(grid)
    if errors:
        raise AssertionError(f"generated input is outside task manifold: {errors}")
    observed = module.observe_overrides(grid)
    if observed.get("profile") != "asymmetric_front":
        raise AssertionError(f"expected scheduled asymmetric witness, saw {observed}")
    if not module.SEMANTIC_WITNESSES["unequal_mirrored_row_fronts"](grid):
        raise AssertionError("generated input did not expose unequal mirrored row fronts")

    INPUT_PATH.write_text(json.dumps([grid], indent=2) + "\n", encoding="utf-8")
    RACKET_PATH.unlink(missing_ok=True)
    subprocess.run(
        [
            sys.executable,
            "-m",
            "arcpuzzles",
            "apply",
            TASK_ID,
            "--input",
            str(INPUT_PATH),
            "--out",
            str(RACKET_PATH),
        ],
        check=True,
        timeout=120,
    )
    receipt = json.loads(RACKET_PATH.read_text(encoding="utf-8"))
    row = receipt["results"][0]
    if not row.get("valid_output") or row.get("error") is not None:
        raise AssertionError(f"canonical Racket application failed: {row}")
    canonical = row["output"]
    mirror = module.rule_mirror(grid)
    if canonical != mirror:
        raise AssertionError("Python mirror disagrees with canonical Racket label")
    rival = module.copy_upper_half(grid)
    differences = differing_cells(canonical, rival)
    completed = bool(differences)
    result = {
        "schema": "arcpuzzles-ticket-adversarial-witness-v1",
        "ticket_id": TICKET_ID,
        "task_id": TASK_ID,
        "source": {"path": str(SOURCE), "sha256": source_sha},
        "probe_seed_hex": SEED_HEX,
        "sample_index": sample_index,
        "difficulty": None,
        "shortcut": {
            "name": "copy_upper_half",
            "description": (
                "Infer the lower output rows by vertically copying the upper-half "
                "frontiers instead of processing every row independently."
            ),
            "canonical_fit_context": (
                "The generator's retained shortcut analysis reports that this rival "
                "fits all four usable canonical pairs."
            ),
        },
        "input": grid,
        "input_sha256": sha_grid(grid),
        "observed_axes": observed,
        "strict_canonical_like_errors": errors,
        "canonical_racket": {
            "output": canonical,
            "output_sha256": sha_grid(canonical),
            "executed_rule_hash": receipt.get("executed_rule_hash"),
            "catalog_rule_hash": receipt.get("catalog_rule_hash"),
            "rule_hash_matches_catalog": receipt.get("rule_hash_matches_catalog"),
            "valid_output": row.get("valid_output"),
        },
        "shortcut_output": rival,
        "shortcut_output_sha256": sha_grid(rival),
        "differing_cells": differences,
        "differing_cell_count": len(differences),
        "status": "completed" if completed else "bounded_unknown",
        "summary": (
            f"A current default asymmetric_front input is lawful and Racket-labeled; "
            f"copy_upper_half disagrees on {len(differences)} cells."
            if completed else
            "The one retained lawful input did not distinguish copy_upper_half."
        ),
        "scope": "One pinned source, one seed/sample, one generated witness, one canonical Racket application.",
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "profile": observed.get("profile"),
        "input_sha256": result["input_sha256"],
        "canonical_output_sha256": result["canonical_racket"]["output_sha256"],
        "shortcut_output_sha256": result["shortcut_output_sha256"],
        "differing_cell_count": len(differences),
        "executed_rule_hash": receipt.get("executed_rule_hash"),
        "result": str(RESULT_PATH),
    }, indent=2, sort_keys=True))
    if not completed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
