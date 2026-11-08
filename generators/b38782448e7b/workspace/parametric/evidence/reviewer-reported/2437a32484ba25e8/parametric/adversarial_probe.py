#!/usr/bin/env python3
"""Independent bounded attack on the b38782448e7b parametric prototype."""
from __future__ import annotations

from collections import Counter
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import find_root

ROOT = find_root(__file__)
PROTOTYPE = ROOT / "generators/b38782448e7b/workspace/parametric/prototype.py"


def load_prototype():
    spec = importlib.util.spec_from_file_location("b38782448e7b_parametric_probe", PROTOTYPE)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load prototype")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def independent_rule(grid, gate_mode: str, third_color_mode: str):
    counts = Counter(value for row in grid for value in row)
    ordered = counts.most_common()
    if len(ordered) > 1 and ordered[0][1] == ordered[1][1]:
        raise ValueError("non-unique modal background")
    bg = ordered[0][0]
    output = [row[:] for row in grid]
    for col, marker in enumerate(grid[0]):
        if marker == bg:
            continue
        fires = (
            marker != grid[1][col]
            if gate_mode == "different"
            else marker == grid[1][col]
        )
        if not fires:
            continue
        for row in range(1, len(grid)):
            value = grid[row][col]
            if value == marker:
                output[row][col] = bg
            elif value == bg or third_color_mode == "overwrite":
                output[row][col] = marker
            else:
                output[row][col] = value
    return output


def expect_rejection(prototype, evidence: Path, mutation: str) -> str:
    with tempfile.TemporaryDirectory(prefix="b38782448e7b-adversarial-") as tmp:
        copy = Path(tmp) / "evidence"
        shutil.copytree(evidence, copy)
        if mutation == "public_bytes":
            target = next((copy / "public").glob("challenge-*.json"))
            target.write_bytes(target.read_bytes().replace(b"\n", b" \n", 1))
            expected = "public bytes"
        elif mutation == "rule_bytes":
            target = next((copy / "private" / "rules").glob("*.rkt"))
            target.write_text(target.read_text() + "\n", encoding="utf-8")
            expected = "rule bytes mismatch"
        else:
            raise ValueError(mutation)
        try:
            prototype.verify_evidence(copy, root=ROOT)
        except ValueError as exc:
            if expected not in str(exc):
                raise AssertionError(f"{mutation} rejected for wrong reason: {exc}") from exc
            return str(exc)
        raise AssertionError(f"verifier accepted {mutation} mutation")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    p = load_prototype()

    parity_cases = []
    with RacketBridge(max_calls_before_restart=256) as bridge:
        for seed in range(4):
            for index in range(3):
                grid = p.prototype_input(seed, index, root=ROOT)
                outputs = {}
                for setting in p.SETTINGS:
                    actual = p.execute(bridge, p.program_for(*setting, root=ROOT), grid)
                    expected = independent_rule(grid, *setting)
                    if actual != expected:
                        raise AssertionError(f"Racket/Python parity failed: seed={seed} index={index} setting={setting}")
                    outputs[p.setting_key(setting)] = p.grid_sha256(actual)
                if len(set(outputs.values())) != len(p.SETTINGS):
                    raise AssertionError(f"setting collapse: seed={seed} index={index}")
                parity_cases.append({"seed": seed, "index": index, "output_sha256": outputs})

    forbidden = ("gate_mode", "third_color_mode", "query_answers", "rival_checks", "(rule!")
    public_files = sorted((args.evidence / "public").glob("challenge-*.json"))
    for path in public_files:
        text = path.read_text(encoding="utf-8")
        leaked = [token for token in forbidden if token in text]
        if leaked:
            raise AssertionError(f"public leak in {path.name}: {leaked}")

    report = {
        "schema": "b38782448e7b-parametric-adversarial-v1",
        "status": "pass",
        "parity_input_count": len(parity_cases),
        "parity_execution_count": len(parity_cases) * len(p.SETTINGS),
        "all_four_settings_distinct_per_input": True,
        "public_file_count": len(public_files),
        "public_redaction_scan": "pass",
        "mutation_rejections": {
            "public_bytes": expect_rejection(p, args.evidence, "public_bytes"),
            "rule_bytes": expect_rejection(p, args.evidence, "rule_bytes"),
        },
        "cases": parity_cases,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "cases"}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
