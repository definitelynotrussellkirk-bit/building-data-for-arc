"""Public Racket evidence for three lawful minimal input families.

Run from the packet root:
  python3 run_with_racket.py python3 generators/e521d16d403e/workspace/lawful_minimal_probe.py --out ../checks/lawful-minimal-v4_0_1.json
This reports a detector limitation; it does not suppress any detector finding.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

from arcpuzzles import Catalog
from reviewer_support import find_root


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    output = Path(args.out)
    if output.exists():
        raise FileExistsError(output)
    root = find_root(__file__)
    source = root / "generators/e521d16d403e/generator.py"
    if not source.is_file():
        source = root / "puzzle_generators/per_puzzle/e521d16d403e/generator.py"
    source_bytes = source.read_bytes()
    spec = importlib.util.spec_from_file_location("lawful_minimal_subject", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    cases = []
    for height, width in ((10, 10), (14, 18)):
        for color in (2, 5, 9):
            for kind in ("full_one_color", "short_line", "solid_2x2"):
                grid = [[0] * width for _ in range(height)]
                if kind == "full_one_color":
                    grid = [[color] * width for _ in range(height)]
                    expected = [row[:] for row in grid]
                elif kind == "short_line":
                    grid[height // 2][:4] = [color] * 4
                    expected = [[color] * 4]
                else:
                    grid[0][:2] = grid[1][:2] = [color] * 2
                    expected = [[color] * 2 for _ in range(2)]
                cases.append({"kind": kind, "dimensions": [height, width], "color": color,
                              "input": grid, "expected_crop": expected,
                              "self_check": module.self_check(grid)})
    authority = Catalog(root).apply("e521d16d403e", [case["input"] for case in cases], timeout=180)
    if source.read_bytes() != source_bytes:
        raise RuntimeError("Generator changed during the probe; do not bind mixed-source evidence")
    for case, result in zip(cases, authority["results"], strict=True):
        case["racket_result"] = result
        case["matches_expected_crop"] = result["output"] == case["expected_crop"]
    report = {
        "task_id": "e521d16d403e", "generator_version": module.VERSION,
        "generator_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "detector_contract": {
            "path": "shared/tools/generator_defect_lint.py",
            "function": "probe_selfcheck_minimal_impostors",
            "supported_task_lawful_minimal_hook": False,
            "explanation": "The detector exempts only singleton canonical-input geometry; no module declaration is read for these three families."
        },
        "authority": {key: value for key, value in authority.items() if key != "results"},
        "cases": cases,
        "summary": {"cases": len(cases), "self_check_accepted": sum(not case["self_check"] for case in cases),
                    "racket_expected_crop_matches": sum(case["matches_expected_crop"] for case in cases),
                    "racket_errors": sum(bool(case["racket_result"].get("error")) for case in cases)},
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report["summary"], indent=2))
    if report["summary"]["racket_expected_crop_matches"] != len(cases):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
