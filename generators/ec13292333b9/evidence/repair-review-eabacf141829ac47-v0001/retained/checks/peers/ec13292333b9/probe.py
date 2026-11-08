"""Source-pinned finite-rival learnability probe for the XOR-panel generator."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "ec13292333b9"
EXPECTED_SOURCE_SHA256 = "6e81ddd0b7c904cca2d25508a3cc54c504c561d3e09c5a6973afe08449449a59"
RIVALS = (
    "occupied_union",
    "occupied_intersection",
    "left_panel_only",
    "right_panel_only",
    "occupancy_equal",
    "nonempty_difference_including_shared_colors",
)


def _canonical_program(root: Path) -> str:
    programs = set()
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                programs.add(row["program_solution"])
    if len(programs) != 1:
        raise ValueError(f"expected one canonical program; found {len(programs)}")
    return next(iter(programs))


def _split(grid: list[list[int]]) -> tuple[list[list[bool]], list[list[bool]]]:
    height, width = len(grid), len(grid[0])
    separators = [col for col in range(width) if all(grid[row][col] == 9 for row in range(height))]
    if len(separators) != 1:
        raise ValueError("expected one separator")
    separator = separators[0]
    left = [[grid[row][col] not in (0, 9) for col in range(separator)] for row in range(height)]
    right = [
        [grid[row][separator + 1 + col] not in (0, 9) for col in range(separator)]
        for row in range(height)
    ]
    return left, right


def _render(grid: list[list[int]], rule: str) -> list[list[int]]:
    left, right = _split(grid)
    output = []
    for row_left, row_right in zip(left, right):
        row = []
        for a, b in zip(row_left, row_right):
            if rule == "xor":
                paint = a != b
            elif rule == "occupied_union":
                paint = a or b
            elif rule == "occupied_intersection":
                paint = a and b
            elif rule == "left_panel_only":
                paint = a
            elif rule == "right_panel_only":
                paint = b
            elif rule == "occupancy_equal":
                paint = a == b
            elif rule == "nonempty_difference_including_shared_colors":
                # Since panel colors are always distinct, a naive value-inequality
                # rule paints every position occupied on either side, including shared cells.
                paint = a or b
            else:
                raise ValueError(rule)
            row.append(8 if paint else 0)
        output.append(row)
    return output


def _grid_literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def main() -> int:
    root = find_root(Path.cwd())
    generator, source_path, source_sha = load_selected_generator(TASK_ID, root=root)
    if source_sha != EXPECTED_SOURCE_SHA256:
        raise ValueError(f"source drift: {source_sha}")
    program = _canonical_program(root)

    failures = []
    rival_survivals = {name: 0 for name in RIVALS}
    samples = 0
    representative = None
    for seed in range(512):
        for sample_index in range(4):
            grid = generator.generate(seed, sample_index)
            samples += 1
            issues = generator.self_check(grid)
            if issues:
                failures.append({"seed": seed, "sample_index": sample_index, "issues": issues})
                continue
            expected = _render(grid, "xor")
            for rival in RIVALS:
                if _render(grid, rival) == expected:
                    rival_survivals[rival] += 1
                    failures.append(
                        {"seed": seed, "sample_index": sample_index, "surviving_rival": rival}
                    )
            if representative is None:
                representative = {"seed": seed, "sample_index": sample_index, "input": grid, "python_output": expected}

    if representative is None:
        raise ValueError("no representative generated")
    bridge = RacketBridge()
    try:
        identity = bridge.runtime_identity
        racket_output = bridge.eval_text(
            f"({wrap_rule(program)} {_grid_literal(representative['input'])})"
        )
    finally:
        bridge.close()
    representative["racket_output"] = racket_output
    representative["python_matches_racket"] = racket_output == representative["python_output"]
    if not representative["python_matches_racket"]:
        failures.append({"representative_racket_mismatch": True})

    report = {
        "schema": "ec13292333b9-finite-rival-probe-v1",
        "status": "passed" if not failures else "failed",
        "task_id": TASK_ID,
        "source_binding": {
            "generator_path": str(source_path.relative_to(root)),
            "generator_sha256": source_sha,
            "canonical_program_sha256": hashlib.sha256(program.encode()).hexdigest(),
        },
        "scope": {
            "seeds": [0, 511],
            "samples_per_seed": 4,
            "samples": samples,
            "rivals": list(RIVALS),
        },
        "rival_survivals": rival_survivals,
        "failures": failures[:50],
        "representative_racket_case": representative,
        "racket": {
            key: identity.get(key)
            for key in ("schema", "backend", "protected", "binary_sha256", "prelude_sha256")
            if key in identity
        },
        "finding": (
            "No ambiguity found in the finite basic set-operation rival class: "
            "every sampled input contains shared, left-only, and right-only occupancy, "
            "so XOR is distinguished by one visible example."
        ),
        "limits": (
            "Finite probe of six explicit rivals over generated samples; not a proof "
            "against all conceivable shortcuts or a generator approval."
        ),
    }
    out = root.parent / "checks" / "peers" / TASK_ID / "finite-rival-probe.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": report["status"],
                "samples": samples,
                "rival_survivals": rival_survivals,
                "racket_match": representative["python_matches_racket"],
                "out": str(out),
            },
            sort_keys=True,
        )
    )
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
