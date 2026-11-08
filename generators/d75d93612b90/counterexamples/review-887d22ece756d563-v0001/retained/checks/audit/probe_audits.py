#!/usr/bin/env python3
"""Reproduce the two findings-only adversarial audits assigned to this review."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "repo" / "shared" / "runtime"))


def load_generator(task_id: str):
    path = ROOT / "repo" / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def components(grid: list[list[int]], color: int) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append(sorted(cells))
    return result


def is_filled_rectangle(cells: list[tuple[int, int]]) -> bool:
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return len(cells) == (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def prepare() -> None:
    # 8d4806d6a371: measure emitted geometry and override behavior.
    task = "8d4806d6a371"
    module, path = load_generator(task)
    component_count = 0
    every_component_rectangular = True
    self_check_failures: list[dict[str, object]] = []
    bands = [("easy", 810000), (None, 820000), ("hard", 830000)]
    for difficulty, seed_base in bands:
        for sample_index in range(80):
            seed = seed_base + sample_index
            grid = module.generate(seed, sample_index, difficulty=difficulty)
            comps = components(grid, 6)
            component_count += len(comps)
            every_component_rectangular &= all(is_filled_rectangle(c) for c in comps)
            errors = module.self_check(grid, difficulty=difficulty, meta={})
            if errors:
                self_check_failures.append(
                    {"difficulty": difficulty, "seed": seed, "sample_index": sample_index, "errors": errors}
                )

    override_seed, override_index, override_difficulty = 812345, 7, "hard"
    base = module.generate(override_seed, override_index, difficulty=override_difficulty)
    override_checks = {
        "unknown_override_accepted_and_identical": (
            module.generate(
                override_seed,
                override_index,
                difficulty=override_difficulty,
                typo_axis="ignored",
            )
            == base
        ),
        "anchor_corner_true_identical": (
            module.generate(
                override_seed,
                override_index,
                difficulty=override_difficulty,
                anchor_corner=True,
            )
            == base
        ),
        "anchor_corner_false_identical": (
            module.generate(
                override_seed,
                override_index,
                difficulty=override_difficulty,
                anchor_corner=False,
            )
            == base
        ),
    }

    irregular = [[0] * 7 for _ in range(7)]
    for r, c in [(0, 2), (1, 2), (1, 3), (4, 4), (4, 5), (5, 4), (5, 5)]:
        irregular[r][c] = 6
    validator_errors = module.self_check(irregular, meta={})
    if validator_errors:
        raise AssertionError(f"8d counterexample rejected: {validator_errors}")
    write_json(ROOT / "checks" / "audit" / task / "input.json", irregular)
    write_json(
        ROOT / "checks" / "audit" / task / "probe.json",
        {
            "task_id": task,
            "generator_sha256": sha256(path),
            "generator_version": module.VERSION,
            "sample_count": 240,
            "seed_ranges": {
                "easy": "810000..810079",
                "default": "820000..820079",
                "hard": "830000..830079",
            },
            "component_count": component_count,
            "all_magenta_components_filled_rectangles": every_component_rectangular,
            "self_check_failure_count": len(self_check_failures),
            "override_probe": {
                "seed": override_seed,
                "sample_index": override_index,
                "difficulty": override_difficulty,
                "results": override_checks,
            },
            "counterexample_validator_errors": validator_errors,
        },
    )

    # d75d93612b90: measure the fixed isolated object and invalid override behavior.
    task = "d75d93612b90"
    module, path = load_generator(task)
    fixed = {(1, 1), (1, 2), (2, 1), (2, 2)}
    every_sample_fixed = True
    every_sample_exactly_one_fixed_isolated = True
    self_check_failures = []
    direction_counts = {name: 0 for name in module.DIRECTIONS}
    bands = [("easy", 750000), (None, 760000), ("hard", 770000), ("challenge", 780000)]
    for difficulty, seed_base in bands:
        for sample_index in range(60):
            seed = seed_base + sample_index
            grid = module.generate(seed, sample_index, difficulty=difficulty)
            orange = components(grid, 7)
            gray = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 5}
            isolated: list[set[tuple[int, int]]] = []
            for comp in orange:
                if not any(
                    (r + dr, c + dc) in gray
                    for r, c in comp
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
                ):
                    isolated.append(set(comp))
            every_sample_fixed &= fixed in isolated
            every_sample_exactly_one_fixed_isolated &= len(isolated) == 1 and isolated[0] == fixed
            errors = module.self_check(grid, difficulty=difficulty, meta={})
            if errors:
                self_check_failures.append(
                    {"difficulty": difficulty, "seed": seed, "sample_index": sample_index, "errors": errors}
                )
            main = max(orange, key=len)
            sides: set[str] = set()
            for r, c in main:
                for name, dr, dc in (
                    ("top", -1, 0),
                    ("bottom", 1, 0),
                    ("left", 0, -1),
                    ("right", 0, 1),
                ):
                    if (r + dr, c + dc) in gray:
                        sides.add(name)
            for side in sides:
                direction_counts[side] += 1

    override_seed, override_index, override_difficulty = 751234, 9, "medium"
    invalid = module.generate(
        override_seed,
        override_index,
        difficulty=override_difficulty,
        direction="diagonal",
    )
    explicit_right = module.generate(
        override_seed,
        override_index,
        difficulty=override_difficulty,
        direction="right",
    )
    base = module.generate(override_seed, override_index, difficulty=override_difficulty)
    unknown = module.generate(
        override_seed,
        override_index,
        difficulty=override_difficulty,
        typo_axis="ignored",
    )

    moved = copy.deepcopy(explicit_right)
    for r in (1, 2):
        for c in (1, 2):
            if moved[r][c] != 7:
                raise AssertionError("expected fixed isolated 2x2 orange block")
            moved[r][c] = 0
    h, w = len(moved), len(moved[0])
    new_origin: tuple[int, int] | None = None
    for r in range(h - 1):
        for c in range(w - 1):
            cells = {(r + i, c + j) for i in range(2) for j in range(2)}
            if cells & fixed:
                continue
            margin = {
                (rr, cc)
                for rr in range(max(0, r - 1), min(h, r + 3))
                for cc in range(max(0, c - 1), min(w, c + 3))
            }
            if all(moved[rr][cc] == 0 for rr, cc in margin):
                new_origin = (r, c)
                break
        if new_origin is not None:
            break
    if new_origin is None:
        raise AssertionError("could not relocate isolated orange block")
    moved_cells = []
    for i in range(2):
        for j in range(2):
            rr, cc = new_origin[0] + i, new_origin[1] + j
            moved[rr][cc] = 7
            moved_cells.append([rr, cc])
    validator_errors = module.self_check(moved, difficulty=override_difficulty, meta={})
    if validator_errors:
        raise AssertionError(f"d75 counterexample rejected: {validator_errors}")
    write_json(ROOT / "checks" / "audit" / task / "input.json", moved)
    write_json(
        ROOT / "checks" / "audit" / task / "probe.json",
        {
            "task_id": task,
            "generator_sha256": sha256(path),
            "generator_version": module.VERSION,
            "sample_count": 240,
            "seed_ranges": {
                "easy": "750000..750059",
                "default": "760000..760059",
                "hard": "770000..770059",
                "challenge": "780000..780059",
            },
            "all_samples_have_fixed_top_left_isolated_2x2_orange": every_sample_fixed,
            "all_samples_have_exactly_one_isolated_orange_component_and_it_is_fixed": (
                every_sample_exactly_one_fixed_isolated
            ),
            "observed_contact_direction_counts": direction_counts,
            "self_check_failure_count": len(self_check_failures),
            "override_probe": {
                "seed": override_seed,
                "sample_index": override_index,
                "difficulty": override_difficulty,
                "invalid_direction_diagonal_accepted": True,
                "invalid_direction_identical_to_explicit_right": invalid == explicit_right,
                "invalid_direction_self_check_errors": module.self_check(
                    invalid, difficulty=override_difficulty, meta={}
                ),
                "unknown_override_identical_to_baseline": unknown == base,
            },
            "counterexample_moved_isolated_cells": moved_cells,
            "counterexample_validator_errors": validator_errors,
        },
    )


def finalize() -> None:
    # 8d filled-rectangle-only rival.
    task = "8d4806d6a371"
    probe = json.loads((ROOT / "checks" / "audit" / task / "probe.json").read_text())
    racket = json.loads((ROOT / "checks" / "audit" / task / "racket.json").read_text())
    input_grid = racket["results"][0]["input"]
    actual = racket["results"][0]["output"]
    rival = copy.deepcopy(input_grid)
    h, w = len(input_grid), len(input_grid[0])
    for comp in components(input_grid, 6):
        borders = set()
        for r, c in comp:
            if r == 0:
                borders.add("top")
            if r == h - 1:
                borders.add("bottom")
            if c == 0:
                borders.add("left")
            if c == w - 1:
                borders.add("right")
        if is_filled_rectangle(comp) and len(borders) == 1:
            for r, c in comp:
                rival[r][c] = 4
    disagreement = [
        [r, c]
        for r in range(h)
        for c in range(w)
        if actual[r][c] != rival[r][c]
    ]
    finding = {
        **probe,
        "executed_rule_hash": racket["executed_rule_hash"],
        "rule_text_sha256": racket["rule_text_sha256"],
        "input_sha256": racket["results"][0]["input_sha256"],
        "actual_output_sha256": racket["results"][0]["output_sha256"],
        "counterexample_input": input_grid,
        "actual_racket_output": actual,
        "rival_name": "filled_rectangles_only",
        "rival_definition": (
            "Recolor a magenta component only when it is a filled axis-aligned rectangle "
            "whose bounding box touches exactly one border; ignore non-rectangular components."
        ),
        "rival_output": rival,
        "disagreement_cells": disagreement,
        "counterexample_domain": (
            "Accepted by the target self_check and lawful for the canonical component rule, "
            "but impossible for this generator because it creates components only with draw_rect."
        ),
        "reproduced_defect": (
            "Unknown overrides are accepted, and the advertised anchor_corner axis is inert "
            "for the recorded seed/sample/difficulty."
        ),
        "possible_shortcut": (
            "A filled-rectangle-only component solver fits all 240 sampled inputs (997 components) "
            "yet fails this validator-accepted irregular component."
        ),
        "racket_command": racket["command"],
        "racket_cwd": racket["cwd"],
    }
    write_json(ROOT / "checks" / "audit" / task / "finding.json", finding)
    write_json(
        ROOT / "checks" / "audit" / task / "rival.json",
        {"task_id": task, "rival": finding["rival_name"], "output": rival},
    )

    # d75 fixed-location isolation rival.
    task = "d75d93612b90"
    probe = json.loads((ROOT / "checks" / "audit" / task / "probe.json").read_text())
    racket = json.loads((ROOT / "checks" / "audit" / task / "racket.json").read_text())
    input_grid = racket["results"][0]["input"]
    actual = racket["results"][0]["output"]
    rival = copy.deepcopy(actual)
    moved_cells = probe["counterexample_moved_isolated_cells"]
    for r, c in moved_cells:
        rival[r][c] = 5
    h, w = len(input_grid), len(input_grid[0])
    disagreement = [
        [r, c]
        for r in range(h)
        for c in range(w)
        if actual[r][c] != rival[r][c]
    ]
    finding = {
        **probe,
        "executed_rule_hash": racket["executed_rule_hash"],
        "rule_text_sha256": racket["rule_text_sha256"],
        "input_sha256": racket["results"][0]["input_sha256"],
        "actual_output_sha256": racket["results"][0]["output_sha256"],
        "counterexample_input": input_grid,
        "actual_racket_output": actual,
        "rival_name": "fixed_top_left_isolation",
        "rival_definition": (
            "Preserve orange only in the fixed top-left 2x2 location; otherwise apply the "
            "contacted-block transformation and leave any relocated isolated orange gray."
        ),
        "rival_output": rival,
        "disagreement_cells": disagreement,
        "counterexample_domain": (
            "Accepted by the target self_check and lawful for the canonical isolation rule, "
            "but outside this generator's fixed-top-left isolated-object subdistribution."
        ),
        "reproduced_defect": (
            "The out-of-domain direction value diagonal is accepted and silently executes the "
            "right branch; unknown overrides are also ignored."
        ),
        "possible_shortcut": (
            "Always preserve the fixed top-left 2x2 orange object and transform the only other "
            "orange object. This fits all 240 sampled inputs but fails after relocating the "
            "isolated object."
        ),
        "racket_command": racket["command"],
        "racket_cwd": racket["cwd"],
    }
    write_json(ROOT / "checks" / "audit" / task / "finding.json", finding)
    write_json(
        ROOT / "checks" / "audit" / task / "rival.json",
        {"task_id": task, "rival": finding["rival_name"], "output": rival},
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("prepare", "finalize"))
    args = parser.parse_args()
    if args.mode == "prepare":
        prepare()
    else:
        finalize()


if __name__ == "__main__":
    main()
