"""Bounded before/after control probe, with canonical Racket labels after repair."""
from __future__ import annotations

import argparse
import json
from itertools import product
from pathlib import Path

from reviewer_support import find_root, load_selected_generator


TASK_ID = "85dcd5c922b9"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--baseline", type=Path)
    args = parser.parse_args()
    root = find_root(__file__)
    gen, source, digest = load_selected_generator(TASK_ID, root=root)
    report = {
        "task_id": TASK_ID,
        "source_path": str(source.relative_to(root)),
        "generator_sha256": digest,
        "declared_rule_hash": gen.RULE_HASH,
        "probe_scope": "one public integer-control boundary; seven malformed requests, twelve legal controls, three default comparisons",
        "invalid_requests": [],
        "valid_controls": [],
        "none_matches_omitted": [],
    }
    for value in (2.75, 3.99, 2.0, "2", "3", True, False):
        row = {"value": value, "python_type": type(value).__name__}
        try:
            grid = gen.generate(27, 0, first_row_load=value, blank_row="last")
        except (TypeError, ValueError) as exc:
            row.update(rejected=True, error_type=type(exc).__name__, error=str(exc))
        else:
            row.update(
                rejected=False,
                input=grid,
                observed=gen.observe_overrides(grid),
                self_check=gen.self_check(grid, meta={"overrides": {"first_row_load": value}}),
            )
        report["invalid_requests"].append(row)

    for index, load, blank in product(range(3), (2, 3), ("none", "last")):
        overrides = {"first_row_load": load, "blank_row": blank}
        grid = gen.generate(27, index, **overrides)
        report["valid_controls"].append({
            "seed": 27,
            "sample_index": index,
            "overrides": overrides,
            "input": grid,
            "observed": gen.observe_overrides(grid),
            "self_check": gen.self_check(grid, meta={"overrides": overrides}),
        })
    for index in range(3):
        report["none_matches_omitted"].append(
            gen.generate(27, index, first_row_load=None) == gen.generate(27, index)
        )

    if args.baseline:
        from arcpuzzles import Catalog

        baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
        report["baseline_generator_sha256"] = baseline["generator_sha256"]
        report["legal_controls_unchanged"] = report["valid_controls"] == baseline["valid_controls"]
        receipt = Catalog(root).apply(
            TASK_ID,
            [row["input"] for row in report["valid_controls"]],
            reference="canonical",
            check_generator_domain=True,
            timeout=120,
        )
        report["racket_receipt"] = receipt
        report["racket_matches_python_mirror"] = [
            row["error"] is None and row["output"] == gen.rule_mirror(control["input"])
            for row, control in zip(receipt["results"], report["valid_controls"], strict=True)
        ]
        report["passed"] = (
            all(row["rejected"] for row in report["invalid_requests"])
            and all(not row["self_check"] for row in report["valid_controls"])
            and all(report["none_matches_omitted"])
            and report["legal_controls_unchanged"]
            and all(report["racket_matches_python_mirror"])
            and receipt["generator_sha256"] == digest
            and receipt["rule_hash_matches_catalog"]
        )
    else:
        report["accepted_noninteger_requests"] = sum(
            not row["rejected"] for row in report["invalid_requests"]
        )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")
    print(json.dumps({
        "report": str(args.out),
        "generator_sha256": digest,
        "accepted_noninteger_requests": sum(not row["rejected"] for row in report["invalid_requests"]),
        "valid_control_count": len(report["valid_controls"]),
        "passed": report.get("passed"),
    }))
    return 0 if report.get("passed", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
