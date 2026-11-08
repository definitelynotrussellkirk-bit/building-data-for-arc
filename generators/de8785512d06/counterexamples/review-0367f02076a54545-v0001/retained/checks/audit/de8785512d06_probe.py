"""Audit only: check network completeness and ordinary-color equivariance."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from reviewer_support import find_root, load_selected_generator

TASK = "de8785512d06"


def components(grid, color):
    unseen = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == color}
    parts = []
    while unseen:
        stack = [min(unseen)]
        unseen.remove(stack[0])
        part = []
        while stack:
            r, c = stack.pop()
            part.append([r, c])
            for p in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if p in unseen:
                    unseen.remove(p)
                    stack.append(p)
        parts.append(sorted(part))
    return parts


def rename(grid, mapping):
    return [[mapping.get(v, v) for v in row] for row in grid]


def confirm_existing(out):
    """Bind the Python observations to retained public Racket execution."""
    evidence = json.loads((out / "findings.json").read_text())
    receipt = json.loads((out / "racket.json").read_text())
    assert receipt["generator_sha256"] == evidence["generator_sha256"]
    assert receipt["executed_rule_hash"] == evidence["rule_hash"]
    assert receipt["rule_hash_matches_catalog"]
    confirmed = {}
    for name, finding in evidence["findings"].items():
        result = receipt["results"][finding["racket_input_index"]]
        assert result["valid_output"] and result["error"] is None
        assert result["input"] == finding["input"]
        assert result["output"] == finding["mirror_output"]
        row = {"input": result["input"], "racket_output": result["output"],
               "input_sha256": result["input_sha256"],
               "output_sha256": result["output_sha256"],
               "seed": finding["seed"], "sample_index": finding["sample_index"],
               "difficulty": finding["difficulty"], "overrides": {},
               "self_check": finding["self_check"]}
        if name == "disconnected":
            actual = {c: components(result["output"], int(c))
                      for c in finding["output_components"]}
            assert actual == finding["output_components"]
            row["disconnected_component_counts"] = {c: len(v) for c, v in actual.items()}
        else:
            renamed = receipt["results"][finding["racket_permuted_input_index"]]
            assert renamed["valid_output"] and renamed["error"] is None
            assert renamed["input"] == finding["permuted_input"]
            assert renamed["output"] == finding["mirror_permuted_output"]
            assert renamed["output"] != finding["equivariant_rival_output"]
            differences = [[r, c, value, finding["equivariant_rival_output"][r][c]]
                           for r, line in enumerate(renamed["output"])
                           for c, value in enumerate(line)
                           if value != finding["equivariant_rival_output"][r][c]]
            row.update({"mapping": finding["mapping"],
                        "permuted_input": renamed["input"],
                        "permuted_self_check": finding["permuted_self_check"],
                        "racket_permuted_output": renamed["output"],
                        "rival_output": finding["equivariant_rival_output"],
                        "differences_row_column_racket_rival": differences})
        confirmed[name] = row
    report = {"status": "Racket_confirmed", "task_id": TASK,
              "generator_sha256": evidence["generator_sha256"],
              "rule_hash": evidence["rule_hash"],
              "rule_text_sha256": receipt["rule_text_sha256"],
              "racket_receipt_sha256": hashlib.sha256((out / "racket.json").read_bytes()).hexdigest(),
              "racket_checks": len(receipt["results"]),
              "population_counts_use_python_mirror": True,
              "counterexamples": confirmed,
              "command": json.loads((out / "command.json").read_text())}
    (out / "confirmed-counterexamples.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--confirm-existing", action="store_true")
    args = parser.parse_args()
    out = args.out.resolve()
    if args.confirm_existing:
        report = confirm_existing(out)
        print(json.dumps({"status": report["status"], "racket_checks": report["racket_checks"]}))
        return
    out.mkdir(parents=True, exist_ok=False)
    root = find_root(__file__)
    gen, source, source_hash = load_selected_generator(TASK, root=root)
    (out / "audited_generator.py").write_bytes(source.read_bytes())
    findings = {}
    totals = Counter()
    for band in ("easy", "medium", "hard"):
        for seed in range(12):
            grid = gen.generate(seed, 2, difficulty=band)
            errors = gen.self_check(grid)
            assert not errors, errors
            labels = Counter(v for row in grid for v in row)
            bg = labels.most_common(1)[0][0]
            active = sorted(c for c in labels if c not in (bg, 8))
            expected = gen.rule_mirror(grid)
            disconnected = {str(c): components(expected, c) for c in active
                            if labels[c] > 1 and len(components(expected, c)) > 1}
            totals[band + ":draws"] += 1
            if disconnected:
                totals[band + ":disconnected"] += 1
                findings.setdefault("disconnected", {
                    "seed": seed, "sample_index": 2, "difficulty": band,
                    "overrides": {}, "input": grid, "mirror_output": expected,
                    "self_check": errors, "output_components": disconnected,
                    "observed_profile": gen.observe_overrides(grid),
                })
            mapping = {active[0]: active[-1], active[-1]: active[0]}
            permuted = rename(grid, mapping)
            permuted_errors = gen.self_check(permuted)
            output_permuted = gen.rule_mirror(permuted)
            equivariant = output_permuted == rename(expected, mapping)
            if not permuted_errors and not equivariant:
                totals[band + ":accepted_rename_changes_geometry"] += 1
                findings.setdefault("recoloring", {
                    "seed": seed, "sample_index": 2, "difficulty": band,
                    "overrides": {}, "input": grid, "mirror_output": expected,
                    "permuted_input": permuted, "mirror_permuted_output": output_permuted,
                    "equivariant_rival_output": rename(expected, mapping),
                    "mapping": mapping, "self_check": errors,
                    "permuted_self_check": permuted_errors,
                    "observed_profile": gen.observe_overrides(grid),
                    "permuted_observed_profile": gen.observe_overrides(permuted),
                })
    inputs = []
    for finding in findings.values():
        finding["racket_input_index"] = len(inputs)
        inputs.append(finding["input"])
        if "permuted_input" in finding:
            finding["racket_permuted_input_index"] = len(inputs)
            inputs.append(finding["permuted_input"])
    (out / "inputs.json").write_text(json.dumps(inputs, indent=2) + "\n")
    evidence = {
        "task_id": TASK, "generator_sha256": source_hash, "rule_hash": gen.RULE_HASH,
        "sampling": {"seeds": [0, 11], "sample_index": 2,
                     "bands": ["easy", "medium", "hard"], "scope": "36 ordinary procedural-profile draws"},
        "counts": dict(totals), "findings": findings,
        "status": "python_mirror_hypotheses_pending_Racket_confirmation",
    }
    (out / "findings.json").write_text(json.dumps(evidence, indent=2) + "\n")
    if inputs:
        argv = [sys.executable, "-m", "arcpuzzles", "apply", TASK,
                "--input", str(out / "inputs.json"), "--out", str(out / "racket.json")]
        result = subprocess.run(argv, text=True, capture_output=True)
        (out / "apply.log").write_text(result.stdout + result.stderr)
        (out / "command.json").write_text(json.dumps({"cwd": str(Path.cwd()), "argv": argv,
            "exit_code": result.returncode, "evidence_paths": [str(out / "racket.json")]}, indent=2) + "\n")
        if result.returncode:
            raise SystemExit(result.returncode)
        confirm_existing(out)
    print(json.dumps({"counts": dict(totals), "findings": list(findings), "out": str(out)}))


if __name__ == "__main__":
    main()
