"""Replayable adversarial audit for generator 0083f06314c3.

The documented rule maps selector color 2 to template A and *every other*
selector color to template B.  The generator never emits selector color 1.
This probe verifies that a rival assigning color 1 to A fits every generated
and canonical lesson, yet differs on a self_check-valid color-1 input.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import types
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any

PACKET = Path(__file__).resolve().parents[2]
REPO = PACKET / "repo"
RUNTIME = REPO / "shared" / "runtime"
sys.path.insert(0, str(RUNTIME))
# The review packet stores the production ``scripts`` package under
# ``shared/tools``. Register a namespace alias so rule_wrap can import it.
scripts_package = types.ModuleType("scripts")
scripts_package.__path__ = [str(REPO / "shared" / "tools")]
sys.modules.setdefault("scripts", scripts_package)

from puzzle_generators import runner  # noqa: E402

TASK_ID = "0083f06314c3"
EXPECTED_GENERATOR_SHA256 = "1dc411f3292d41aa1ff31fac19da37eff4bf1a65d0fc972b965126915e352089"


def _load_generator(path: Path):
    spec = importlib.util.spec_from_file_location("audit_0083_generator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _normalize_grid(grid: Any):
    if isinstance(grid, list) and grid and isinstance(grid[0], str):
        return [[int(ch) for ch in row] for row in grid]
    return grid


def _as_pairs(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    return [value] if isinstance(value, dict) else value


def _canonical_material(task_id: str) -> tuple[str, list[dict[str, Any]]]:
    source = None
    pairs: list[dict[str, Any]] = []
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != task_id:
                continue
            source = source or row.get("program_solution")
            for pair in _as_pairs(row.get("train")) + _as_pairs(row.get("test")):
                if isinstance(pair, dict) and pair.get("input") is not None:
                    pairs.append(
                        {
                            "input": _normalize_grid(pair["input"]),
                            "output": _normalize_grid(pair.get("output")),
                        }
                    )
    if not isinstance(source, str) or not source.strip():
        raise RuntimeError(f"no canonical rule source for {task_id}")
    return source, pairs


def _selector_location_and_color(gen, grid: list[list[int]]) -> tuple[int, int, int]:
    ranges, errors = gen._panel_ranges(grid)
    if errors or len(ranges) != 4:
        raise ValueError(errors or f"expected four panels, got {len(ranges)}")
    c0, c1 = ranges[2]
    cells = [
        (r, c, grid[r][c])
        for r in range(len(grid))
        for c in range(c0, c1 + 1)
        if grid[r][c] not in (0, 9)
    ]
    if len(cells) != 1:
        raise ValueError(f"expected one selector cell, got {cells!r}")
    return cells[0]


def color1_chooses_a_rival(gen, grid: list[list[int]]):
    _r, _c, selector = _selector_location_and_color(gen, grid)
    # Canonical branch except for the deliberately uncovered selector color 1.
    template_index = 0 if selector in (1, 2) else 1
    return gen._solve_with_template(grid, template_index)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds-per-profile", type=int, default=20)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    generator_path = REPO / "generators" / TASK_ID / "generator.py"
    generator_sha = _sha256(generator_path)
    if generator_sha != EXPECTED_GENERATOR_SHA256:
        raise RuntimeError(
            f"generator hash drift: {generator_sha} != {EXPECTED_GENERATOR_SHA256}"
        )
    gen = _load_generator(generator_path)
    rule_source, canonical_pairs = _canonical_material(TASK_ID)
    rule_hash = hashlib.sha256(" ".join(rule_source.split()).encode()).hexdigest()[:12]

    selector_counts: Counter[int] = Counter()
    generated_total = generated_rival_fits = 0
    generated_self_check_failures: list[dict[str, Any]] = []
    counterexample = None

    bridge, function_name = runner._open_bridge_with_rule(runner.wrap_rule(rule_source))
    try:
        for difficulty_index, difficulty in enumerate(("easy", "medium", "hard")):
            for profile in range(4):
                for offset in range(args.seeds_per_profile):
                    seed = 83_000 + difficulty_index * 10_000 + profile * 1_000 + offset
                    grid = gen.generate(seed, profile, difficulty=difficulty)
                    findings = gen.self_check(deepcopy(grid))
                    if findings:
                        generated_self_check_failures.append(
                            {"difficulty": difficulty, "seed": seed, "profile": profile, "findings": findings}
                        )
                    _r, _c, selector = _selector_location_and_color(gen, grid)
                    selector_counts[selector] += 1
                    actual = runner._apply_rule(bridge, function_name, grid)
                    rival = color1_chooses_a_rival(gen, grid)
                    generated_total += 1
                    generated_rival_fits += int(rival == actual)

                    if counterexample is None and selector != 2:
                        modified = deepcopy(grid)
                        r, c, _ = _selector_location_and_color(gen, modified)
                        modified[r][c] = 1
                        valid = gen.self_check(deepcopy(modified))
                        actual_modified = runner._apply_rule(bridge, function_name, modified)
                        rival_modified = color1_chooses_a_rival(gen, modified)
                        if not valid and actual_modified != rival_modified:
                            counterexample = {
                                "derived_from": {
                                    "difficulty": difficulty,
                                    "seed": seed,
                                    "profile": profile,
                                    "original_selector": selector,
                                },
                                "self_check_findings": valid,
                                "input": modified,
                                "actual_racket_output": actual_modified,
                                "color1_chooses_a_rival_output": rival_modified,
                                "canonical_panel1_output": gen._solve_with_template(modified, 1),
                                "rival_panel0_output": gen._solve_with_template(modified, 0),
                            }

        canonical_rows = []
        for index, pair in enumerate(canonical_pairs):
            grid = pair["input"]
            actual = runner._apply_rule(bridge, function_name, grid)
            _r, _c, selector = _selector_location_and_color(gen, grid)
            rival = color1_chooses_a_rival(gen, grid)
            canonical_rows.append(
                {
                    "index": index,
                    "selector": selector,
                    "self_check_findings": gen.self_check(deepcopy(grid)),
                    "stored_output_matches_racket": pair["output"] == actual,
                    "rival_matches_racket": rival == actual,
                }
            )
    finally:
        bridge.shutdown()

    report = {
        "schema": "arcpuzzles-adversarial-audit-v1",
        "task_id": TASK_ID,
        "generator_path": str(generator_path.relative_to(PACKET)),
        "generator_sha256": generator_sha,
        "canonical_rule_hash": rule_hash,
        "rival": "selector color 1 chooses template A; color 2 also chooses A; all other colors choose B",
        "generated_census": {
            "bands": ["easy", "medium", "hard"],
            "profiles": [0, 1, 2, 3],
            "seeds_per_profile": args.seeds_per_profile,
            "total": generated_total,
            "selector_color_counts": {str(key): value for key, value in sorted(selector_counts.items())},
            "selector_color_1_seen": selector_counts[1] > 0,
            "rival_matches_racket": generated_rival_fits,
            "self_check_failures": generated_self_check_failures,
        },
        "canonical_census": {
            "total": len(canonical_rows),
            "rival_matches_racket": sum(row["rival_matches_racket"] for row in canonical_rows),
            "rows": canonical_rows,
        },
        "counterexample": counterexample,
        "finding_reproduced": (
            generated_total > 0
            and generated_rival_fits == generated_total
            and not generated_self_check_failures
            and selector_counts[1] == 0
            and all(row["rival_matches_racket"] for row in canonical_rows)
            and counterexample is not None
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "finding_reproduced": report["finding_reproduced"],
        "generated_rival_fit": f"{generated_rival_fits}/{generated_total}",
        "selector_colors": dict(sorted(selector_counts.items())),
        "counterexample": counterexample is not None,
    }, sort_keys=True))
    return 0 if report["finding_reproduced"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
