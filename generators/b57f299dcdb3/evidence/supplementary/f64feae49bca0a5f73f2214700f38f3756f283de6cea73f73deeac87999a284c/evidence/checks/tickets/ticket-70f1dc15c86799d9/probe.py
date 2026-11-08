#!/usr/bin/env python3
"""Retain one lawful current-source refuter of the global-frequency shortcut."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys
import time

from reviewer_support import find_root, load_selected_generator

HERE = Path(__file__).resolve().parent
if str(HERE.parent) not in sys.path:
    sys.path.insert(0, str(HERE.parent))
from portable_replay import (  # noqa: E402
    apply_grounded_rule,
    grid_sha256,
    grounded_rule,
    normalized_rule_sha256,
    sha256_file,
    write_json,
)

TICKET_ID = "ticket-70f1dc15c86799d9"
TASK_ID = "b57f299dcdb3"
PINNED_SOURCE_SHA256 = "ec5c95c23f3dfaad028a0cc9c138a4997fcebdb1e4b3bcd179c5f855f0a3a4c6"
MANIFEST_REL = Path(
    "generators/b57f299dcdb3/counterexamples/"
    "review-7dadbd7417f0ad83-v0001/audit_assets.json"
)
WITNESS_REL = Path(
    "generators/b57f299dcdb3/counterexamples/review-7dadbd7417f0ad83-v0001/"
    "retained/checks/audit/b57f299dcdb3-counterexample/counterexample.json"
)


def global_frequency_rival(grid: list[list[int]]) -> tuple[list[list[int]], dict[int, int]]:
    counts = Counter(value for row in grid for value in row)
    background = max(counts, key=counts.get)
    eligible = Counter({color: count for color, count in counts.items() if color not in (0, 4, background)})
    if not eligible:
        return [[0]], {}
    return [[max(eligible, key=eligible.get)]], dict(sorted(eligible.items()))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(HERE / "result.json"))
    parser.add_argument("--witness-out", default=str(HERE / "witness.json"))
    args = parser.parse_args()
    started = time.monotonic()

    root = find_root(__file__)
    module, source_path, source_sha = load_selected_generator(TASK_ID, root=root)
    manifest_path = root / MANIFEST_REL
    witness_path = root / WITNESS_REL
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    retained = json.loads(witness_path.read_text(encoding="utf-8"))
    manifest_rows = {row["path"]: row for row in manifest["files"]}
    witness_manifest = manifest_rows.get(WITNESS_REL.as_posix())
    if witness_manifest is None:
        raise SystemExit("retained witness absent from assets manifest")

    recipe = retained["recipe"]
    regenerated = module.generate(
        recipe["seed"],
        recipe["sample_index"],
        difficulty=recipe["difficulty"],
        **recipe["overrides"],
    )
    grid = retained["input"]
    checker_errors = module.self_check(grid)
    python_output = module.solve_python(grid)
    racket_output, runtime_identity = apply_grounded_rule(TASK_ID, grid)
    rival_output, eligible_counts = global_frequency_rival(grid)
    rule_source = grounded_rule(TASK_ID)

    # Preserve the exact grounded-rule digest as evidence even if a future
    # catalog refresh changes it; the declared short hash is the binding check.
    normalized_rule = normalized_rule_sha256(rule_source)
    checks = {
        "source_hash_matches_ticket": source_sha == PINNED_SOURCE_SHA256,
        "retained_witness_source_matches_ticket": retained.get("generator_sha256") == PINNED_SOURCE_SHA256,
        "witness_hash_matches_assets_manifest": sha256_file(witness_path) == witness_manifest.get("sha256"),
        "recipe_regenerates_exact_witness": regenerated == grid,
        "current_source_accepts_witness": checker_errors == [],
        "python_matches_retained_intended_output": python_output == retained["intended_racket_output"],
        "canonical_racket_matches_python": racket_output == python_output,
        "declared_rule_hash_matches": normalized_rule.startswith(module.RULE_HASH),
        "rival_reimplementation_matches_retained": rival_output == retained["rival"]["output"],
        "global_frequency_shortcut_is_refuted": racket_output != rival_output,
        "observed_counts_match_retained": {
            str(k): v for k, v in eligible_counts.items()
        } == retained["observed"]["eligible_global_counts"],
    }
    passed = all(checks.values())

    portable_witness = {
        "schema": "arc-ticket-portable-witness-v1",
        "ticket_id": TICKET_ID,
        "task_id": TASK_ID,
        "generator_sha256": source_sha,
        "rule_hash": module.RULE_HASH,
        "grounded_rule_normalized_sha256": normalized_rule,
        "recipe": recipe,
        "input": grid,
        "canonical_output": racket_output,
        "rival": {
            "name": "global_most_frequent_eligible_role",
            "eligible_global_counts": {str(k): v for k, v in eligible_counts.items()},
            "output": rival_output,
        },
        "plus_center_colors": [
            color for _, _, color in module._plus_centers(grid, module._mode(grid))
        ],
        "current_self_check_errors": checker_errors,
        "input_sha256": grid_sha256(grid),
        "canonical_output_sha256": grid_sha256(racket_output),
        "rival_output_sha256": grid_sha256(rival_output),
    }
    write_json(Path(args.witness_out), portable_witness)

    result = {
        "schema": "arc-supplementary-ticket-result-v1",
        "ticket_id": TICKET_ID,
        "type": "adversarial_witness",
        "status": "finding" if passed else "unknown",
        "finding_reproduced": passed,
        "summary": (
            "A lawful generated grid refutes the plausible shortcut 'return the globally most "
            "frequent eligible role color': the shortcut returns 9, while the intended plus-object "
            "census returns 2. The recipe regenerates exactly and current Python agrees with canonical Racket."
            if passed
            else "The bounded witness failed one or more source, regeneration, or execution checks."
        ),
        "checks": checks,
        "checker_errors": checker_errors,
        "source": {"path": str(source_path.relative_to(root)), "sha256": source_sha},
        "retained_source": {
            "manifest": str(MANIFEST_REL),
            "witness": str(WITNESS_REL),
        },
        "outputs": {
            "input_sha256": grid_sha256(grid),
            "canonical": racket_output,
            "rival": rival_output,
        },
        "runtime_identity": runtime_identity,
        "elapsed_seconds": round(time.monotonic() - started, 6),
        "limitations": [
            "This is one source-bound witness, not a new shortcut success-rate census.",
            "It establishes that the shortcut is semantically wrong, not the frequency with which assembled lessons disambiguate it.",
            "The underlying source already has an unresolved retained audit; this ticket does not assess or change approval.",
        ],
    }
    write_json(Path(args.out), result)
    print(json.dumps({"status": result["status"], "finding_reproduced": passed, "checks": checks}, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
