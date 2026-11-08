#!/usr/bin/env python3
"""Episode-level center-inset prototype for 04ec2218e2d8.

This is task-local authoring evidence, not a production parametric-rule API.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
)

TASK_ID = "04ec2218e2d8"
ALLOWED_INSET_DIVISORS = (4, 3)
DEFAULT_INSET_DIVISOR = 4
_CANONICAL_INSET = "(quotient (min hh ww) 4)"

# Every controlled input contains at least one component whose minimum bbox side
# is >= 9, so divisor 4 and divisor 3 produce different inset thicknesses.
_FIXTURE_SPECS = (
    {
        "scene_profile": "two_8x12_10x12",
        "component_style": "solid",
        "difficulty": "easy",
    },
    {
        "scene_profile": "two_8x8_10x12",
        "component_style": "interior_hole",
        "difficulty": "medium",
    },
    {
        "scene_profile": "three_6x6_10x6_14x10",
        "component_style": "edge_notch",
        "difficulty": "hard",
    },
    {
        "scene_profile": "two_8x12_10x12",
        "component_style": "edge_notch",
        "difficulty": "medium",
    },
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json_sha256(value: Any) -> str:
    return sha256_bytes(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    )


def normalized_rule_hash(program: str) -> str:
    return sha256_bytes(" ".join(program.split()).encode())[:12]


def canonical_program(root: str | Path) -> str:
    """Return the unique canonical Racket program across task variants."""
    programs = set()
    row_count = 0
    with canonical_path(root).open() as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            row_count += 1
            program = row.get("program_solution")
            if not isinstance(program, str) or not program:
                raise ValueError("canonical row has no Racket program")
            programs.add(program)
    if row_count == 0:
        raise ValueError(f"no canonical rows for {TASK_ID}")
    if len(programs) != 1:
        raise ValueError(
            f"canonical variants disagree on the Racket program for {TASK_ID}"
        )
    return programs.pop()


def _validate_divisor(inset_divisor: int) -> None:
    if type(inset_divisor) is not int:
        raise TypeError("inset_divisor must be an exact integer")
    if inset_divisor not in ALLOWED_INSET_DIVISORS:
        raise ValueError(
            f"inset_divisor must be one of {ALLOWED_INSET_DIVISORS}"
        )


def render_program(
    canonical: str,
    inset_divisor: int = DEFAULT_INSET_DIVISOR,
) -> str:
    """Instantiate exact Racket text for one fixed episode-level setting."""
    _validate_divisor(inset_divisor)
    if not canonical.startswith("(rule!") or not canonical.endswith(")"):
        raise ValueError("canonical program is not wrapped with rule!")
    if canonical.count(_CANONICAL_INSET) != 1:
        raise ValueError("canonical inset expression did not match pinned rule")
    if inset_divisor == DEFAULT_INSET_DIVISOR:
        return canonical
    return canonical.replace(
        _CANONICAL_INSET,
        f"(quotient (min hh ww) {inset_divisor})",
        1,
    )


def execute(
    bridge: RacketBridge,
    program: str,
    grid: list[list[int]],
) -> list[list[int]]:
    """Execute exact instantiated Racket bytes with the input bound to ``g``."""
    if not program.startswith("(rule!") or not program.endswith(")"):
        raise ValueError("expected rule! wrapper")
    bridge.define_grid("g", grid)
    body = program[len("(rule!") : -1].strip()
    output = bridge.eval_text(f"({body} g)")
    if (
        not isinstance(output, list)
        or not output
        or not isinstance(output[0], list)
        or not output[0]
        or any(
            not isinstance(row, list) or len(row) != len(output[0])
            for row in output
        )
    ):
        raise ValueError("Racket program did not return a nonempty rectangular grid")
    return output


def select_inset_divisor(seed: int) -> int:
    """Deterministically choose one hidden rule setting for a whole episode."""
    if type(seed) is not int:
        raise TypeError("seed must be an exact integer (bool is not accepted)")
    if seed < 0:
        raise ValueError("seed must be nonnegative")
    return ALLOWED_INSET_DIVISORS[seed % len(ALLOWED_INSET_DIVISORS)]


def fixture_inputs(
    seed: int,
    *,
    root: str | Path | None = None,
) -> list[list[list[int]]]:
    """Create four lawful controlled inputs that distinguish both settings."""
    if type(seed) is not int:
        raise TypeError("seed must be an exact integer (bool is not accepted)")
    if seed < 0:
        raise ValueError("seed must be nonnegative")
    resolved_root = Path(root) if root is not None else find_root(__file__)
    generator, _source, _digest = load_selected_generator(
        TASK_ID,
        root=resolved_root,
    )
    grids = []
    for index, spec in enumerate(_FIXTURE_SPECS):
        grid = generator.generate(
            seed * 1009 + index,
            seed * 1013 + index,
            difficulty=spec["difficulty"],
            scene_profile=spec["scene_profile"],
            component_style=spec["component_style"],
        )
        findings = generator.self_check(
            grid,
            difficulty=spec["difficulty"],
            meta={
                "overrides": {
                    "scene_profile": spec["scene_profile"],
                    "component_style": spec["component_style"],
                }
            },
        )
        if findings:
            raise ValueError(
                f"controlled fixture {index} failed selected self_check: {findings}"
            )
        grids.append(grid)
    return grids


def _build_episode(
    seed: int,
    inset_divisor: int,
    canonical: str,
    bridge: RacketBridge,
    *,
    root: str | Path,
) -> dict[str, Any]:
    programs = {
        divisor: render_program(canonical, divisor)
        for divisor in ALLOWED_INSET_DIVISORS
    }
    rival_divisor = next(
        divisor
        for divisor in ALLOWED_INSET_DIVISORS
        if divisor != inset_divisor
    )
    generator, _source, generator_digest = load_selected_generator(
        TASK_ID,
        root=root,
    )

    pairs = []
    rival_outputs = []
    difference_counts = []
    grids = fixture_inputs(seed, root=root)
    for grid in grids:
        chosen_output = execute(bridge, programs[inset_divisor], grid)
        rival_output = execute(bridge, programs[rival_divisor], grid)
        pairs.append({"input": grid, "output": chosen_output})
        rival_outputs.append(rival_output)
        difference_counts.append(
            sum(
                chosen_output[row][col] != rival_output[row][col]
                for row in range(len(grid))
                for col in range(len(grid[0]))
            )
        )

    demo_differences = [
        index
        for index, count in enumerate(difference_counts[:3])
        if count > 0
    ]
    query_differs = difference_counts[3] > 0
    if demo_differences != [0, 1, 2] or not query_differs:
        raise ValueError(
            "controlled episode failed to distinguish both inset settings"
        )

    return {
        "schema": "04ec2218e2d8-parametric-inset-episode-v1",
        "seed": seed,
        "parameters": {"inset_divisor": inset_divisor},
        "setting_selected_once": True,
        "inset_formula": f"max(2, floor(min(height,width)/{inset_divisor}))",
        "program": programs[inset_divisor],
        "program_sha256": sha256_bytes(programs[inset_divisor].encode()),
        "program_normalized_hash": normalized_rule_hash(programs[inset_divisor]),
        "generator_sha256": generator_digest,
        "train": pairs[:3],
        "test": pairs[3:],
        "input_controls": [dict(spec) for spec in _FIXTURE_SPECS],
        "rival": {
            "inset_divisor": rival_divisor,
            "program_sha256": sha256_bytes(programs[rival_divisor].encode()),
            "program_normalized_hash": normalized_rule_hash(programs[rival_divisor]),
            "demo_differences": demo_differences,
            "query_differs": query_differs,
            "differing_cell_counts": {
                "train": difference_counts[:3],
                "test": difference_counts[3:],
            },
            "status": "distinguished",
            "outputs": {
                "train": rival_outputs[:3],
                "test": rival_outputs[3:],
            },
        },
        "label_authority": (
            "included protected Racket bridge executing the exact instantiated "
            "program text"
        ),
        "selected_generator_self_check": all(
            generator.self_check(grid) == []
            for grid in grids
        ),
    }


def generate_episode(
    seed: int,
    *,
    inset_divisor: int | None = None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Choose one divisor once and keep it fixed for all episode pairs."""
    if type(seed) is not int:
        raise TypeError("seed must be an exact integer (bool is not accepted)")
    if seed < 0:
        raise ValueError("seed must be nonnegative")
    selected = select_inset_divisor(seed) if inset_divisor is None else inset_divisor
    _validate_divisor(selected)

    root = find_root(__file__)
    canonical = canonical_program(root)
    if bridge is not None:
        return _build_episode(
            seed,
            selected,
            canonical,
            bridge,
            root=root,
        )
    with RacketBridge() as owned_bridge:
        return _build_episode(
            seed,
            selected,
            canonical,
            owned_bridge,
            root=root,
        )


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Return a solver-visible challenge without hidden rule or query labels."""
    return {
        "train": deepcopy(episode["train"]),
        "test": [
            {"input": deepcopy(pair["input"])}
            for pair in episode["test"]
        ],
    }


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def materialize(output: str | Path, *, seed: int = 481) -> dict[str, Any]:
    """Write two complete episodes and finite, source-bound Racket evidence."""
    if type(seed) is not int:
        raise TypeError("seed must be an exact integer (bool is not accepted)")
    if seed < 0:
        raise ValueError("seed must be nonnegative")

    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    root = find_root(__file__)
    source_paths = [
        Path(__file__),
        Path(__file__).parents[2] / "tests" / "test_parametric_inset.py",
        Path(__file__).parent / "README.md",
    ]
    source_hashes = {
        str(path.relative_to(root)): sha256_bytes(path.read_bytes())
        for path in source_paths
        if path.is_file()
    }

    canonical = canonical_program(root)
    programs = {
        divisor: render_program(canonical, divisor)
        for divisor in ALLOWED_INSET_DIVISORS
    }
    generator, _source, generator_digest = load_selected_generator(
        TASK_ID,
        root=root,
    )

    with RacketBridge() as bridge:
        episodes = [
            generate_episode(seed + offset, bridge=bridge)
            for offset in range(len(ALLOWED_INSET_DIVISORS))
        ]
        observed_settings = {
            episode["parameters"]["inset_divisor"]
            for episode in episodes
        }
        if observed_settings != set(ALLOWED_INSET_DIVISORS):
            raise ValueError(
                f"retained seeds did not cover both settings: {observed_settings}"
            )

        witness_input = fixture_inputs(seed, root=root)[0]
        witness_outputs = {
            divisor: execute(bridge, program, witness_input)
            for divisor, program in programs.items()
        }
        canonical_checks = []
        for index, pair in enumerate(canonical_pairs(TASK_ID, root=root)):
            actual = execute(bridge, canonical, pair["input"])
            canonical_checks.append(
                {
                    "pair_index": index,
                    "input_sha256": _json_sha256(pair["input"]),
                    "expected_output_sha256": _json_sha256(pair["output"]),
                    "actual_output_sha256": _json_sha256(actual),
                    "matches": actual == pair["output"],
                }
            )
        runtime_identity = bridge.runtime_identity

    for index, episode in enumerate(episodes):
        episode["prototype_source_sha256"] = source_hashes
        _write_json(
            output / "public" / f"episode-{index}.json",
            public_challenge(episode),
        )
        _write_json(
            output / "private" / f"episode-{index}.json",
            episode,
        )

    for divisor, program in programs.items():
        path = output / "private" / f"program-inset-{divisor}.rkt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(program)

    differing_cells = [
        {
            "row": row,
            "col": col,
            "inset_4": witness_outputs[4][row][col],
            "inset_3": witness_outputs[3][row][col],
        }
        for row in range(len(witness_input))
        for col in range(len(witness_input[0]))
        if witness_outputs[4][row][col] != witness_outputs[3][row][col]
    ]
    _write_json(
        output / "private" / "setting-difference-witness.json",
        {
            "input": witness_input,
            "input_controls": _FIXTURE_SPECS[0],
            "outputs": {
                str(divisor): value
                for divisor, value in witness_outputs.items()
            },
            "different": bool(differing_cells),
            "differing_cell_count": len(differing_cells),
            "differing_cells": differing_cells,
        },
    )
    _write_json(
        output / "private" / "canonical-default-check.json",
        {
            "canonical_program_sha256": sha256_bytes(canonical.encode()),
            "canonical_normalized_rule_hash": normalized_rule_hash(canonical),
            "generator_sha256": generator_digest,
            "all_match": all(row["matches"] for row in canonical_checks),
            "pairs": canonical_checks,
        },
    )

    episode_parameters = {
        str(episode["parameters"]["inset_divisor"]): {
            "episode_index": index,
            "seed": episode["seed"],
            "program_sha256": episode["program_sha256"],
            "program_normalized_hash": episode["program_normalized_hash"],
        }
        for index, episode in enumerate(episodes)
    }
    report = {
        "schema": "04ec2218e2d8-parametric-inset-report-v1",
        "status": "prototype",
        "task_id": TASK_ID,
        "parameter": {
            "name": "inset_divisor",
            "allowed_values": list(ALLOWED_INSET_DIVISORS),
            "default": DEFAULT_INSET_DIVISOR,
            "formula": "t = max(2, floor(min(component_height, component_width) / inset_divisor))",
        },
        "episode_parameters": episode_parameters,
        "setting_selection": "ALLOWED_INSET_DIVISORS[seed mod 2], once per episode",
        "reasoning_invariants": [
            "identify each 4-connected cyan object",
            "compute each object's own bounding box",
            "preserve non-object cells inside the bounding box",
            "paint the center yellow and the outer ring by the same four bbox quadrants",
        ],
        "input_constraints": [
            "the selected generator's lawful 23x23 black/cyan component grammar",
            "every controlled episode pair contains at least one component with minimum bbox side at least 9 so divisors 4 and 3 disagree",
        ],
        "default_program_exact_canonical": programs[4] == canonical,
        "canonical_program_sha256": sha256_bytes(canonical.encode()),
        "canonical_normalized_rule_hash": normalized_rule_hash(canonical),
        "program_hashes": {
            str(divisor): {
                "sha256": sha256_bytes(program.encode()),
                "normalized": normalized_rule_hash(program),
            }
            for divisor, program in programs.items()
        },
        "generator_sha256": generator_digest,
        "canonical_pairs_checked": len(canonical_checks),
        "canonical_pairs_all_match": all(
            row["matches"] for row in canonical_checks
        ),
        "complete_episodes": len(episodes),
        "pairs_per_episode": {"train": 3, "test": 1},
        "all_labels_and_rivals_executed_in_racket": True,
        "all_demonstrations_refute_other_declared_setting": all(
            episode["rival"]["demo_differences"] == [0, 1, 2]
            for episode in episodes
        ),
        "all_queries_distinguish_other_declared_setting": all(
            episode["rival"]["query_differs"]
            for episode in episodes
        ),
        "witness_differing_cell_count": len(differing_cells),
        "runtime_identity": runtime_identity,
        "source_sha256": source_hashes,
        "limitations": [
            "Only divisors 4 (canonical) and 3 (proposed) are instantiated.",
            "The alternative changes inset thickness but keeps the original object roles, palette, bbox quadrants, and cell-only painting behavior.",
            "Evidence covers two retained seeds and four controlled inputs per episode.",
            "The controls deliberately include bbox sizes that expose the divisor; inputs with minimum side 6 through 8 do not distinguish these settings.",
            "Only the declared opposite divisor is checked as a rival; finite evidence does not establish unique induction against all rules.",
            "This task-local prototype has no production API, approval, or training-admission claim.",
        ],
    }
    _write_json(output / "report.json", report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=481)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = materialize(args.out, seed=args.seed)
    print(
        json.dumps(
            {
                "status": report["status"],
                "task_id": report["task_id"],
                "complete_episodes": report["complete_episodes"],
                "episode_parameters": report["episode_parameters"],
                "out": str(args.out),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
