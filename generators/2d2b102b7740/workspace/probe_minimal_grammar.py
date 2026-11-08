#!/usr/bin/env python3
"""Record minimal-shape validator and reference-execution evidence for any task.

Example, from a packet root:
  python3 review.py run python3 generators/2d2b102b7740/workspace/probe_minimal_grammar.py \
    --task 2d2b102b7740 --input ../checks/input.json --out ../checks/minimal.json

Input is one JSON grid (or {"input": grid}), not a challenge or labelled lesson.
The five fixtures reproduce the linter's geometry and palette selection without
importing its private functions. Names describe shapes, not semantic verdicts.
Reference success does not establish semantic validity or exempt any lint check.
--timeout bounds the public reference worker batch, not Python self_check or
source copying. --out must be new; existing evidence is never overwritten.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import inspect
import json
import math
from pathlib import Path
import sys


# Bind imports to this checkout, including the public task_tests copied runtime.
# No current-directory, sibling-checkout, or predecessor imports are required.
for ancestor in Path(__file__).resolve().parents:
    support = next((p for p in (ancestor / "reviewer_support.py",
                               ancestor / "shared/runtime/reviewer_support.py") if p.is_file()), None)
    if support is not None:
        sys.path.insert(0, str(support.parent))
        break
else:
    raise RuntimeError("No local reviewer_support.py; keep this tool in a library or copied task-test runtime")

from reviewer_support import find_root, normalize_grid

ROOT = find_root(__file__)
for relative in ("shared/runtime", "src"):
    candidate = ROOT / relative
    if candidate.is_dir():
        sys.path.insert(0, str(candidate))


def grid_sha256(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def minimal_fixtures(grid):
    """Return palette metadata and five independent grids, including clipped shapes.

    The modal-color tie breaks by first row-major occurrence, as in the linter.
    The foreground is the smallest other color. Uniform inputs cannot select a
    foreground and are rejected explicitly; no unobserved color is invented.
    """
    grid = normalize_grid(grid)
    h, w = len(grid), len(grid[0])
    if h > 30 or w > 30:
        raise ValueError("Input dimensions must be between 1 and 30")
    counts = Counter(value for row in grid for value in row)
    background = counts.most_common(1)[0][0]
    other = sorted(set(counts) - {background})
    if not other:
        raise ValueError("Input needs at least two colors to select a foreground")
    foreground = other[0]

    def blank(color):
        return [[color] * w for _ in range(h)]

    fixtures = [("all_background", blank(background)),
                ("full_one_color", blank(foreground))]
    for name, cells in (
        ("singleton", [(h // 2, w // 2)]),
        ("solid_2x2", [(r, c) for r in range(min(2, h)) for c in range(min(2, w))]),
        ("short_line", [(h // 2, c) for c in range(min(4, w))]),
    ):
        fixture = blank(background)
        for r, c in cells:
            fixture[r][c] = foreground
        fixtures.append((name, fixture))
    return {"height": h, "width": w, "background": background, "foreground": foreground,
            "modal_tie_break": "first_row_major_occurrence",
            "foreground_selection": "smallest_nonmodal_color",
            "shapes_clipped_to_input_dimensions": True}, fixtures


def check_grid(checker, grid, difficulty):
    """Keep exceptions distinct from ordinary rejection; never retry a failing hook."""
    if not callable(checker):
        return {"status": "missing", "violations": None}
    try:
        signature = inspect.signature(checker)
        try:
            signature.bind(grid, difficulty=difficulty)
        except TypeError:
            signature.bind(grid)
            violations = checker(deepcopy(grid))
        else:
            violations = checker(deepcopy(grid), difficulty=difficulty)
        # The public generator contract is an empty/nonempty violations list.
        # Retain unexpected return types rather than silently calling them passes.
        if not isinstance(violations, (list, tuple)) or not all(isinstance(v, str) for v in violations):
            return {"status": "error", "violations": None,
                    "error": "self_check must return a list or tuple of violation strings",
                    "returned": repr(violations)}
        return {"status": "rejected" if violations else "accepted", "violations": list(violations)}
    except Exception as exc:
        return {"status": "error", "violations": None,
                "error": f"{type(exc).__name__}: {exc}"}


def load_generator(source, task):
    """Execute the exact hashed bytes, bypassing stale timestamp-valid bytecode."""
    source_bytes = source.read_bytes()
    source_hash = hashlib.sha256(source_bytes).hexdigest()
    spec = importlib.util.spec_from_file_location(f"minimal_probe_generator_{task}", source)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {source}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    exec(compile(source_bytes, str(source), "exec", dont_inherit=True), module.__dict__)
    return module, source_hash


def probe(task, input_path, *, difficulty=None, timeout=120):
    """Use only public Catalog methods and the selected generator's self_check."""
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("timeout must be finite and positive")
    if not (ROOT / "catalog/puzzles.jsonl").is_file():
        raise RuntimeError("Catalog library missing: run in the library or a public task_tests snapshot")
    from arcpuzzles import Catalog

    raw = Path(input_path).read_bytes()
    payload = json.loads(raw)
    if isinstance(payload, dict):
        if set(payload) != {"input"}:
            raise ValueError('Input object must contain only "input"; select one grid explicitly')
        payload = payload["input"]
    grid = normalize_grid(payload)
    palette, fixtures = minimal_fixtures(grid)
    catalog = Catalog(ROOT)
    row = catalog.describe(task)
    if not row["has_generator"] or row["kind"] != "per_puzzle":
        raise ValueError("This probe requires a per-puzzle generator with a canonical Racket rule")
    source = (ROOT / row["generator"]).resolve()
    if not source.is_relative_to(ROOT):
        raise ValueError("Generator path escapes the selected library")
    module, source_hash = load_generator(source, row["id"])
    checker = getattr(module, "self_check", None)
    cases = [{"name": name, "input": value, "input_sha256": grid_sha256(value),
              "validator": check_grid(checker, value, difficulty),
              "racket": {"status": "not_observed", "output": None, "output_sha256": None}}
             for name, value in [("supplied_input", grid), *fixtures]]
    report = {
        "schema": "minimal-grammar-probe-v1", "task_id": row["id"], "requested_task": task,
        "status": "recorded", "semantic_verdict": "not_assessed", "changes_lint_or_approval": False,
        "note": "Validator acceptance and completed Racket execution are separate observations. "
                "Neither establishes semantic validity. Review the task's grammar and exact outputs; "
                "this report never automatically exempts a lint check or changes approval.",
        "settings": {"difficulty": difficulty, "reference": "canonical", "timeout_seconds": timeout,
                     "timeout_scope": "reference worker batch; excludes Python self_check and source copying"},
        "sources": {"generator_path": row["generator"], "generator_sha256": source_hash,
                    "catalog_rule_hash": row["rule_hash"],
                    "tool_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    "input_file_sha256": hashlib.sha256(raw).hexdigest()},
        "fixture_construction": palette, "cases": cases,
    }
    try:
        receipt = catalog.apply(row["id"], [deepcopy(case["input"]) for case in cases],
                                reference="canonical", allow_unapproved=True, timeout=timeout)
        report["reference_execution"] = {"status": "completed", "receipt": receipt}
        for case, result in zip(cases, receipt["results"], strict=True):
            if result["input_sha256"] != case["input_sha256"]:
                raise ValueError("Reference result input hash does not match the fixture")
            case["racket"] = {"status": "completed" if result["valid_output"] and result["error"] is None else "failed",
                              "output": result["output"], "output_sha256": result["output_sha256"],
                              "valid_grid_output": result["valid_output"], "error": result["error"]}
        report["sources"]["executed_rule_hash"] = receipt["executed_rule_hash"]
        report["sources"]["rule_text_sha256"] = receipt["rule_text_sha256"]
        report["source_bindings_match"] = (receipt["generator_sha256"] == source_hash
                                           and receipt["rule_hash_matches_catalog"])
    except Exception as exc:
        report["status"] = "reference_failed"
        report["reference_execution"] = {"status": "failed", "error": f"{type(exc).__name__}: {exc}",
                                         "run": getattr(exc, "run", None)}
        report["source_bindings_match"] = None
    try:
        current_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    except OSError as exc:
        current_hash = None
        report["sources"]["generator_read_error_after"] = f"{type(exc).__name__}: {exc}"
    report["sources"]["generator_sha256_after"] = current_hash
    if current_hash != source_hash or report["source_bindings_match"] is False:
        report["status"] = "source_changed"
        report["source_bindings_match"] = False
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--task", required=True, help="Catalog task ID or unambiguous alias")
    parser.add_argument("--input", required=True, type=Path, help="One representative JSON input grid")
    parser.add_argument("--out", required=True, type=Path, help="New evidence JSON; existing paths are refused")
    parser.add_argument("--difficulty", choices=("easy", "medium", "hard"), default=None)
    parser.add_argument("--timeout", type=float, default=120, help="Reference worker batch timeout, seconds (default: 120)")
    args = parser.parse_args(argv)
    try:
        if args.out.exists() or args.out.is_symlink():
            raise FileExistsError(f"Output already exists: {args.out}; choose a new --out")
        report = probe(args.task, args.input, difficulty=args.difficulty, timeout=args.timeout)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        # Exclusive creation also prevents overwriting evidence created during the run.
        with args.out.open("x", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, ensure_ascii=False, allow_nan=False)
            handle.write("\n")
    except Exception as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    print(f"{report['status']}: {args.out}; semantic validity is not assessed")
    return 0 if report["status"] == "recorded" else 2


if __name__ == "__main__":
    raise SystemExit(main())
