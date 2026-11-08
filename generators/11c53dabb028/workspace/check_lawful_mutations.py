"""Racket-backed authoring witnesses for lawful generic mutation shapes.

Run through the packet's run_with_racket.py wrapper.  This is an authoring
probe, not a visible-only solve, and deliberately reads the canonical authority.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import sys


TASK_ID = "11c53dabb028"


def _load_environment():
    try:
        from reviewer_support import find_root
    except ModuleNotFoundError as exc:
        if exc.name != "reviewer_support":
            raise
        for ancestor in Path(__file__).resolve().parents:
            runtime = ancestor / "shared" / "runtime"
            if (runtime / "reviewer_support.py").is_file():
                sys.path.insert(0, str(runtime))
                break
        else:
            raise
        from reviewer_support import find_root

    root = find_root(__file__)
    try:
        from arcpuzzles import Catalog
    except ModuleNotFoundError as exc:
        if exc.name != "arcpuzzles":
            raise
        sys.path.insert(0, str(root / "src"))
        from arcpuzzles import Catalog

    name = f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
    try:
        generator = importlib.import_module(name)
    except ModuleNotFoundError as exc:
        if exc.name not in {"puzzle_generators.per_puzzle", f"puzzle_generators.per_puzzle.{TASK_ID}", name}:
            raise
        spec = importlib.util.spec_from_file_location(
            "lawful_mutations_generator", root / "generators" / TASK_ID / "generator.py",
        )
        assert spec is not None and spec.loader is not None
        generator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(generator)
    return root, Catalog(root), generator


def complement_tiling(grid):
    """Independent transparent expression of the task's recorded input law."""
    height, width = len(grid), len(grid[0])
    color = next(cell for row in grid for cell in row if cell != 0)
    return [
        [color if grid[row % height][column % width] == 0 else 0 for column in range(2 * width)]
        for row in range(2 * height)
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, help="A new report directory")
    args = parser.parse_args()
    output = Path(args.out).resolve()
    output.mkdir(parents=True, exist_ok=False)
    root, catalog, generator = _load_environment()
    fixture_path = Path(__file__).with_name("lawful_mutations.json")
    fixtures = json.loads(fixture_path.read_text())
    cases = fixtures["cases"]
    source_hash = hashlib.sha256(Path(generator.__file__).read_bytes()).hexdigest()
    receipt = catalog.apply(TASK_ID, [case["input"] for case in cases], reference="canonical", timeout=300)
    (output / "racket.json").write_text(json.dumps(receipt, indent=2) + "\n")
    checked = []
    for case, actual in zip(cases, receipt["results"], strict=True):
        grid = case["input"]
        expected = complement_tiling(grid)
        reasons = generator.self_check(grid)
        checked.append({
            "name": case["name"],
            "self_check_reasons": reasons,
            "expected_output": expected,
            "racket_error": actual["error"],
            "matches": not reasons and actual["error"] is None and actual["output"] == expected,
        })
    report = {
        "task_id": TASK_ID,
        "cwd": str(Path.cwd()),
        "library_root": str(root),
        "argv": ["python3", *sys.argv],
        "generator_sha256": source_hash,
        "fixture_sha256": hashlib.sha256(fixture_path.read_bytes()).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "source_matches_reference_receipt": receipt["generator_sha256"] == source_hash,
        "rule_hash_matches_catalog": receipt["rule_hash_matches_catalog"],
        "cases": checked,
        "counts": {"passed": sum(case["matches"] for case in checked), "total": len(checked)},
    }
    passed = (
        report["source_matches_reference_receipt"]
        and report["rule_hash_matches_catalog"]
        and all(case["matches"] for case in checked)
    )
    report["passed"] = passed
    report["exit_code"] = 0 if passed else 1
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: value for key, value in report.items() if key != "cases"}, indent=2))
    return report["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
