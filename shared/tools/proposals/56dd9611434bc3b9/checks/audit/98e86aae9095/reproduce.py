from __future__ import annotations

from collections import deque
import hashlib
import json
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "98e86aae9095"
ROOT = find_root(__file__)
OUT = ROOT.parent / "checks" / "audit" / TASK_ID / "reproduction.json"


def canonical_record() -> dict[str, Any]:
    found = []
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            found.append(row)
    assert len(found) == 1
    return found[0]


def grid_literal(grid: list[list[int]]) -> str:
    rows = " ".join("(" + " ".join(map(str, row)) + ")" for row in grid)
    return f"'({rows})"


def eval_rule(bridge: RacketBridge, program: str, grid: list[list[int]]):
    # These canonical authorities are already bare-bridge-safe body forms.
    # Bind the standard g/h/w convention without importing repository-only
    # source-normalization helpers into the portable audit runtime.
    body = strip_rule_wrapper(program)
    callable_text = (
        "(lambda (g) (let* ((h (rows g)) (w (cols g))) "
        + body
        + "))"
    )
    return bridge.eval_text(f"({callable_text} {grid_literal(grid)})")


def component_sizes(grid: list[list[int]], color: int) -> list[int]:
    work = [row[:] for row in grid]
    work[-1][0] = 0
    for c in range(len(work[0])):
        work[0][c] = 0
    seen: set[tuple[int, int]] = set()
    sizes = []
    for r, row in enumerate(work):
        for c, value in enumerate(row):
            if value != color or (r, c) in seen:
                continue
            seen.add((r, c))
            queue = deque([(r, c)])
            size = 0
            while queue:
                rr, cc = queue.popleft()
                size += 1
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < len(work)
                        and 0 <= nc < len(work[0])
                        and work[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            sizes.append(size)
    return sorted(sizes, reverse=True)


generator, source_path, source_sha = load_selected_generator(TASK_ID, root=ROOT)
record = canonical_record()
program = record["program_solution"]

no_shape = generator.generate(17, 0, difficulty="medium", texture="no_shape")
no_shape_self_check = generator.self_check(no_shape)
try:
    with RacketBridge() as bridge:
        no_shape_output = eval_rule(bridge, program, no_shape)
    no_shape_execution = {"status": "returned", "output": no_shape_output}
except Exception as exc:  # retain exact runtime symptom
    no_shape_execution = {
        "status": "error",
        "type": type(exc).__name__,
        "message": str(exc),
    }

base = generator.generate(17, 0, difficulty="medium")
axis_pairs = {
    "shape": (0, 3),
    "sequence": (0, 3),
    "palette_kind": ("default", "warm"),
}
axis_results = {}
for name, (left, right) in axis_pairs.items():
    a = generator.generate(17, 0, difficulty="medium", **{name: left})
    b = generator.generate(17, 0, difficulty="medium", **{name: right})
    axis_results[name] = {
        "left": left,
        "right": right,
        "equal": a == b,
        "left_sha256": hashlib.sha256(json.dumps(a).encode()).hexdigest(),
        "right_sha256": hashlib.sha256(json.dumps(b).encode()).hexdigest(),
    }

try:
    unknown_grid = generator.generate(17, 0, difficulty="medium", unknown_axis=99)
    unknown_override = {
        "accepted": True,
        "equal_to_base": unknown_grid == base,
        "grid_sha256": hashlib.sha256(json.dumps(unknown_grid).encode()).hexdigest(),
    }
except Exception as exc:
    unknown_override = {
        "accepted": False,
        "type": type(exc).__name__,
        "message": str(exc),
    }

ordinary = []
component_histogram: dict[str, int] = {}
placement_failures = []
for sample_index in range(600):
    grid = generator.generate(20261022, sample_index, difficulty="medium")
    key = grid[-1][0]
    sizes = component_sizes(grid, key)
    component_histogram[str(len(sizes))] = component_histogram.get(str(len(sizes)), 0) + 1
    if not sizes:
        placement_failures.append(sample_index)
    ordinary.append({"sample_index": sample_index, "key": key, "key_component_sizes": sizes})

result = {
    "schema": "audit-reproduction-v1",
    "task_id": TASK_ID,
    "source": {
        "path": str(Path(source_path).relative_to(ROOT)),
        "sha256": source_sha,
    },
    "authority": {
        "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
    },
    "self_check_accepts_no_shape": {
        "grid": no_shape,
        "self_check": no_shape_self_check,
        "accepted": no_shape_self_check == [],
        "authority_execution": no_shape_execution,
    },
    "declared_axis_inertness": axis_results,
    "unknown_override": unknown_override,
    "ordinary_key_component_census": {
        "seed": 20261022,
        "difficulty": "medium",
        "draws": len(ordinary),
        "component_count_histogram": component_histogram,
        "missing_key_shape_sample_indices": placement_failures,
        "all_have_exactly_one_key_component": component_histogram == {"1": 600},
        "first_five": ordinary[:5],
    },
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({
    "task_id": TASK_ID,
    "source_sha256": source_sha,
    "no_shape_self_check": no_shape_self_check,
    "no_shape_authority_status": no_shape_execution["status"],
    "axis_equal": {k: v["equal"] for k, v in axis_results.items()},
    "unknown_override_accepted": unknown_override["accepted"],
    "component_histogram": component_histogram,
    "out": str(OUT),
}, indent=2, sort_keys=True))
