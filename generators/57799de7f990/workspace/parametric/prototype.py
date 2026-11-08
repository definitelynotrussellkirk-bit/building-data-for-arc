"""Task-local episode-level connection-axis prototype for 57799de7f990."""
from __future__ import annotations

import hashlib
import json
from copy import deepcopy

from reviewer_support import canonical_path, find_root

TASK_ID = "57799de7f990"
AXIS_MODES = ("both", "horizontal", "vertical")
DEFAULT = "both"
_HORIZONTAL_GUARD = "((= r1 r2) (not (find"
_VERTICAL_GUARD = "((= c1 c2) (not (find"


def parameters(seed):
    """Choose one hidden rule setting for the complete episode."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    return {"axis_mode": AXIS_MODES[seed % len(AXIS_MODES)]}


def canonical_record(root):
    """Load the unique canonical record for the parent ARC task."""
    matches = []
    with canonical_path(root).open() as source:
        for line in source:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    matches.append(row)
    if len(matches) != 1:
        raise ValueError(f"expected one canonical row for {TASK_ID}; found {len(matches)}")
    return matches[0]


def canonical_program(root):
    """Load the exact canonical Racket program for the parent ARC task."""
    return canonical_record(root)["program_solution"]


def instantiate(program, axis_mode=DEFAULT):
    """Return exact canonical text or a one-guard axis-restricted variant."""
    if axis_mode not in AXIS_MODES:
        raise ValueError(f"unsupported axis_mode: {axis_mode!r}")
    if program.count(_HORIZONTAL_GUARD) != 1 or program.count(_VERTICAL_GUARD) != 1:
        raise ValueError("canonical adjacency guard structure changed")
    if axis_mode == DEFAULT:
        return program
    if axis_mode == "horizontal":
        return program.replace(
            _VERTICAL_GUARD,
            "((and (= c1 c2) #f) (not (find",
            1,
        )
    return program.replace(
        _HORIZONTAL_GUARD,
        "((and (= r1 r2) #f) (not (find",
        1,
    )

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_BASE_FIXTURES = (
    (9, 11, ((2, 2), (2, 7), (6, 2))),
    (13, 13, ((2, 2), (2, 6), (2, 10), (7, 6), (11, 6))),
    (12, 15, ((2, 3), (2, 11), (6, 3), (10, 3), (10, 11))),
    (14, 16, ((2, 2), (2, 7), (2, 13), (7, 7), (11, 7), (11, 13))),
)


def _fixture_grid(height, width, centers):
    grid = [[0] * width for _ in range(height)]
    for row, col in centers:
        if not (1 <= row < height - 1 and 1 <= col < width - 1):
            raise ValueError("diamond center is too close to the boundary")
        for dr, dc in _CARDINAL:
            rr, cc = row + dr, col + dc
            if grid[rr][cc] != 0:
                raise ValueError("fixture diamond arms overlap")
            grid[rr][cc] = 2
    return grid


def fixture_inputs(seed):
    """Four deterministic lawful inputs; every one exhibits both axis cues."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    import random

    rng = random.Random(seed ^ 0x57799DE7)
    grids = []
    for height, width, base_centers in _BASE_FIXTURES:
        flip_rows = bool(rng.randrange(2))
        flip_cols = bool(rng.randrange(2))
        centers = []
        for row, col in base_centers:
            if flip_rows:
                row = height - 1 - row
            if flip_cols:
                col = width - 1 - col
            centers.append((row, col))
        grids.append(_fixture_grid(height, width, centers))
    return grids


def diamond_centers(grid):
    height = len(grid)
    width = len(grid[0])
    return [
        (row, col)
        for row in range(1, height - 1)
        for col in range(1, width - 1)
        if all(grid[row + dr][col + dc] == 2 for dr, dc in _CARDINAL)
    ]


def visible_connection_axes(grid):
    """Axes on which adjacent centers leave at least one background cell to paint."""
    centers = diamond_centers(grid)
    axes = set()
    by_row = {}
    by_col = {}
    for row, col in centers:
        by_row.setdefault(row, []).append(col)
        by_col.setdefault(col, []).append(row)
    for row, columns in by_row.items():
        for left, right in zip(sorted(columns), sorted(columns)[1:]):
            if any(grid[row][col] == 0 for col in range(left + 1, right)):
                axes.add("horizontal")
    for col, rows in by_col.items():
        for top, bottom in zip(sorted(rows), sorted(rows)[1:]):
            if any(grid[row][col] == 0 for row in range(top + 1, bottom)):
                axes.add("vertical")
    return axes


def execute(bridge, program, grid):
    """Execute one exact instantiated Racket rule body through the included bridge."""
    if not program.startswith("(rule! ") or not program.endswith(")"):
        raise ValueError("expected a canonical rule! wrapper")
    bridge.define_grid("g", grid)
    body = program[len("(rule! "):-1]
    expression = f"({body} g)" if body.lstrip().startswith("(lambda") else body
    output = bridge.eval_text(expression)
    if (
        not isinstance(output, list)
        or not output
        or not isinstance(output[0], list)
        or not output[0]
        or any(not isinstance(row, list) or len(row) != len(output[0]) for row in output)
    ):
        raise ValueError("Racket did not return a nonempty rectangular grid")
    return output


def _sha256(data):
    return hashlib.sha256(data).hexdigest()


def episode(seed, canonical, bridge):
    """Build one complete private episode whose rule setting is fixed by seed."""
    params = parameters(seed)
    chosen = params["axis_mode"]
    program = instantiate(canonical, chosen)
    inputs = fixture_inputs(seed)
    pairs = [
        {"input": deepcopy(grid), "output": execute(bridge, program, grid)}
        for grid in inputs
    ]

    rivals = []
    for rival_mode in AXIS_MODES:
        if rival_mode == chosen:
            continue
        rival_program = instantiate(canonical, rival_mode)
        rival_outputs = [execute(bridge, rival_program, grid) for grid in inputs]
        demo_differences = [
            index
            for index, pair in enumerate(pairs[:3])
            if pair["output"] != rival_outputs[index]
        ]
        query_differs = pairs[3]["output"] != rival_outputs[3]
        status = "distinguished" if demo_differences else "ambiguous"
        rivals.append(
            {
                "axis_mode": rival_mode,
                "demo_differences": demo_differences,
                "query_differs": query_differs,
                "status": status,
            }
        )
        if query_differs and not demo_differences:
            raise ValueError(
                f"query requires unresolved axis_mode distinction: {chosen!r} vs {rival_mode!r}"
            )

    return {
        "seed": seed,
        "parameters": params,
        "program": program,
        "program_sha256": _sha256(program.encode()),
        "train": pairs[:3],
        "test": pairs[3:],
        "rivals": rivals,
        "input_constraints": (
            "zero background; color-2 complete four-arm diamonds; 3..7 centers; "
            "at least one visible horizontal and one visible vertical connection"
        ),
        "label_authority": "included Racket bridge executing the exact instantiated program",
    }


def public_challenge(private_episode):
    """Remove hidden parameter, rule text, rival evidence, and query answers."""
    return {
        "train": deepcopy(private_episode["train"]),
        "test": [{"input": deepcopy(pair["input"])} for pair in private_episode["test"]],
    }


def _write_json(path, data):
    from pathlib import Path

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def _prototype_source_hashes():
    from pathlib import Path

    here = Path(__file__).resolve().parent
    task_home = here.parents[1]
    candidates = [
        here / "prototype.py",
        here / "README.md",
        task_home / "tests" / "test_parametric_axis_mode.py",
    ]
    return {
        str(path.relative_to(task_home)): _sha256(path.read_bytes())
        for path in candidates
        if path.exists()
    }


def materialize(output):
    """Execute and retain bounded Racket evidence for all three settings."""
    from pathlib import Path
    from arc_repl.racket_bridge import RacketBridge

    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    root = find_root(__file__)
    record = canonical_record(root)
    canonical = record["program_solution"]
    source_hashes = _prototype_source_hashes()
    bridge = RacketBridge()
    try:
        canonical_pairs = record["train"] + record["test"]
        for index, pair in enumerate(canonical_pairs):
            observed = execute(bridge, canonical, pair["input"])
            if observed != pair["output"]:
                raise ValueError(f"canonical Racket parity failed on pair {index}")

        episodes = [episode(seed, canonical, bridge) for seed in range(len(AXIS_MODES))]
        if {item["parameters"]["axis_mode"] for item in episodes} != set(AXIS_MODES):
            raise ValueError("retained seeds do not cover every axis_mode")

        rule_hashes = {}
        for mode in AXIS_MODES:
            program = instantiate(canonical, mode)
            rule_path = output / "private" / "rules" / f"axis-mode-{mode}.rkt"
            rule_path.parent.mkdir(parents=True, exist_ok=True)
            rule_path.write_text(program)
            rule_hashes[mode] = _sha256(program.encode())

        for seed, item in enumerate(episodes):
            item["prototype_source_sha256"] = source_hashes
            item["canonical_content_hash"] = record.get("content_hash")
            _write_json(output / "private" / f"episode-{seed}.json", item)
            _write_json(output / "public" / f"episode-{seed}.json", public_challenge(item))

        witness_input = fixture_inputs(42)[0]
        witness_outputs = {
            mode: execute(bridge, instantiate(canonical, mode), witness_input)
            for mode in AXIS_MODES
        }
        if len({json.dumps(value, sort_keys=True) for value in witness_outputs.values()}) != len(AXIS_MODES):
            raise ValueError("shared witness does not distinguish every axis_mode")
        witness = {
            "input": witness_input,
            "outputs": witness_outputs,
            "program_sha256": rule_hashes,
            "purpose": "one lawful input whose Racket outputs differ for every allowed setting",
        }
        _write_json(output / "private" / "shared-input-witness.json", witness)

        all_rivals_distinguished = all(
            rival["status"] == "distinguished"
            for item in episodes
            for rival in item["rivals"]
        )
        report = {
            "schema": "arcpuzzles-parametric-prototype-report-v1",
            "status": "prototype",
            "task_id": TASK_ID,
            "parameter": {
                "axis_mode": {
                    "allowed": list(AXIS_MODES),
                    "original_default": DEFAULT,
                }
            },
            "default_program_exact": instantiate(canonical, DEFAULT) == canonical,
            "canonical_program_sha256": _sha256(canonical.encode()),
            "canonical_content_hash": record.get("content_hash"),
            "canonical_pairs_verified": len(canonical_pairs),
            "episode_count": len(episodes),
            "episode_seeds": list(range(len(AXIS_MODES))),
            "rule_sha256": rule_hashes,
            "all_rivals_distinguished": all_rivals_distinguished,
            "prototype_source_sha256": source_hashes,
            "label_authority": "included Racket bridge executing exact saved program bytes",
            "input_constraints": (
                "complete color-2 diamonds on zero background; each retained input has "
                "visible horizontal and vertical aligned-center connections"
            ),
            "scope": (
                "three retained seeds, four controlled inputs per episode, one query per episode; "
                "proposed prototype only, not a production API or approval"
            ),
            "limitations": [
                "controlled constructive fixtures rather than the full production sampler",
                "finite rival set limited to the two other declared axis_mode values",
                "hidden episode parameter is inferred only from demonstrations",
            ],
        }
        _write_json(output / "report.json", report)

        files = {}
        for path in sorted(p for p in output.rglob("*") if p.is_file() and p.name != "manifest.json"):
            files[str(path.relative_to(output))] = _sha256(path.read_bytes())
        manifest = {
            "schema": "arcpuzzles-parametric-prototype-evidence-v1",
            "task_id": TASK_ID,
            "status": "prototype",
            "files": files,
        }
        _write_json(output / "manifest.json", manifest)
        return report
    finally:
        bridge.shutdown()


if __name__ == "__main__":
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(materialize(args.out), indent=2, sort_keys=True))
