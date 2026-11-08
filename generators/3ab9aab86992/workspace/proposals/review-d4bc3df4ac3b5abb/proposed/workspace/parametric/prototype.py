#!/usr/bin/env python3
"""Isolated episode-level ``corner_basis`` rule prototype for 3ab9aab86992.

The selected production generator and canonical Racket authority stay unchanged.
The prototype varies which vertex of each tiny L determines the corresponding
large output corner:

* ``elbow`` (default/canonical): the occupied elbow vertex chooses the corner.
* ``missing`` (proposed): the missing vertex of the 2x2 bounding box chooses it.

The object grammar, color transfer, enlargement, and border-L construction are
identical in both settings.  One setting is chosen once per complete episode.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_path, find_root


TASK_ID = "3ab9aab86992"
PROTOTYPE_VERSION = "1.0.0"
STATUS = "proposed prototype; not production-approved"
ALLOWED_CORNER_BASES = ("elbow", "missing")
DEFAULT_CORNER_BASIS = "elbow"
PARAMETER = {
    "name": "corner_basis",
    "values": list(ALLOWED_CORNER_BASES),
    "default": DEFAULT_CORNER_BASIS,
    "input_constraints": (
        "unchanged tiny-L grammar; demonstrations use incomplete orientation sets "
        "or distinct colors so opposite-corner settings differ"
    ),
}
ROOT = find_root(__file__)
SELECTED_SOURCE = ROOT / "generators" / TASK_ID / "generator.py"
SELECTED_SOURCE_SHA256 = hashlib.sha256(SELECTED_SOURCE.read_bytes()).hexdigest()


def _load_task_generator():
    """Load the transported task source without mixing package roots.

    The inherited frozen test imports this same repository mirror through
    ``shared/runtime``. Reusing that dependency tree keeps a staged pytest
    process source-consistent while still hashing the exact task source bytes.
    """
    dependency_root = ROOT / "shared" / "runtime"
    spec = importlib.util.spec_from_file_location(
        f"parametric_generator_{SELECTED_SOURCE_SHA256}", SELECTED_SOURCE
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {SELECTED_SOURCE}")
    module = importlib.util.module_from_spec(spec)
    before = list(sys.path)
    try:
        sys.path.insert(0, str(dependency_root))
        spec.loader.exec_module(module)
    finally:
        sys.path[:] = before
    return module


GENERATOR = _load_task_generator()
_NEIGHBORS = ((-1, 0), (1, 0), (0, -1), (0, 1))
_CANONICAL_CORNER_BLOCK = """((and tl tr bl) 'tl)
                                                      ((and tl tr br) 'tr)
                                                      ((and tl bl br) 'bl)
                                                      (else 'br)"""
_MISSING_CORNER_BLOCK = """((and tl tr bl) 'br)
                                                      ((and tl tr br) 'bl)
                                                      ((and tl bl br) 'tr)
                                                      (else 'tl)"""


def _validate_basis(corner_basis: str) -> str:
    if corner_basis not in ALLOWED_CORNER_BASES:
        raise ValueError(
            f"corner_basis must be one of {ALLOWED_CORNER_BASES}, got {corner_basis!r}"
        )
    return corner_basis


def choose_parameters(episode_seed: int) -> dict[str, str]:
    """Choose the hidden rule once for the whole episode."""
    if type(episode_seed) is not int:
        raise TypeError("episode seed must be an integer (not bool)")
    digest = hashlib.sha256(
        f"{TASK_ID}|corner_basis|{episode_seed}".encode("utf-8")
    ).digest()
    return {"corner_basis": ALLOWED_CORNER_BASES[digest[0] % 2]}


def canonical_record(root: Path | None = None) -> dict[str, Any]:
    """Return the exact selected task row from the canonical ledger."""
    root = ROOT if root is None else Path(root)
    rows = []
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    rows.append(row)
    if len(rows) != 1:
        raise ValueError(f"expected one canonical row for {TASK_ID}, found {len(rows)}")
    if not isinstance(rows[0].get("program_solution"), str):
        raise ValueError("canonical row is missing program_solution")
    return rows[0]


def racket_program(corner_basis: str = DEFAULT_CORNER_BASIS) -> str:
    """Materialize the exact Racket authority for one parameter setting."""
    setting = _validate_basis(corner_basis)
    program = canonical_record()["program_solution"]
    if setting == DEFAULT_CORNER_BASIS:
        return program
    count = program.count(_CANONICAL_CORNER_BLOCK)
    if count != 1:
        raise ValueError(
            "canonical corner-selection block changed; refusing an unsafe mutation"
        )
    return program.replace(_CANONICAL_CORNER_BLOCK, _MISSING_CORNER_BLOCK, 1)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_json(value: Any) -> str:
    body = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return sha256_text(body)


def rule_sha256(corner_basis: str = DEFAULT_CORNER_BASIS) -> str:
    return sha256_text(racket_program(corner_basis))


def _components(grid: list[list[int]], bg: int) -> list[tuple[int, list[tuple[int, int]]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result = []
    for row in range(h):
        for col in range(w):
            color = grid[row][col]
            if color == bg or (row, col) in seen:
                continue
            todo = [(row, col)]
            seen.add((row, col))
            cells = []
            while todo:
                r, c = todo.pop()
                cells.append((r, c))
                for dr, dc in _NEIGHBORS:
                    rr, cc = r + dr, c + dc
                    if (
                        0 <= rr < h
                        and 0 <= cc < w
                        and (rr, cc) not in seen
                        and grid[rr][cc] == color
                    ):
                        seen.add((rr, cc))
                        todo.append((rr, cc))
            result.append((color, cells))
    return result


def _mode(grid: list[list[int]]) -> int:
    counts: dict[int, int] = {}
    for row in grid:
        for value in row:
            counts[value] = counts.get(value, 0) + 1
    return max(counts, key=counts.get)


def python_reference(
    grid: list[list[int]], *, corner_basis: str = DEFAULT_CORNER_BASIS
) -> list[list[int]]:
    """Independent executable mirror for the bounded prototype."""
    setting = _validate_basis(corner_basis)
    errors = GENERATOR.self_check(grid)
    if errors:
        raise ValueError(f"input is outside the tiny-L grammar: {errors}")
    size = len(grid)
    bg = _mode(grid)
    output = [[bg for _ in range(size)] for _ in range(size)]
    k = (size - 1) // 2
    vertices = {(0, 0), (0, 1), (1, 0), (1, 1)}

    for color, cells in _components(grid, bg):
        row0 = min(row for row, _ in cells)
        col0 = min(col for _, col in cells)
        normalized = {(row - row0, col - col0) for row, col in cells}
        missing = next(iter(vertices - normalized))
        if setting == "elbow":
            corner = (1 - missing[0], 1 - missing[1])
        else:
            corner = missing
        bottom, right = bool(corner[0]), bool(corner[1])
        rr = size - 1 if bottom else 0
        cc = size - 1 if right else 0
        for offset in range(k):
            output[rr + (-offset if bottom else offset)][cc] = color
            output[rr][cc + (-offset if right else offset)] = color
    return output


def _build_input(episode_seed: int, pair_index: int) -> list[list[int]]:
    """Use the production input grammar while forcing a distinguishing scene."""
    if type(pair_index) is not int or pair_index < 0:
        raise ValueError("pair_index must be a nonnegative integer")
    sizes = (5, 7, 9, 11, 13, 15)
    counts = (1, 2, 3, 4)
    n_corners = counts[pair_index % len(counts)]
    grid = GENERATOR.generate(
        episode_seed,
        pair_index,
        difficulty="medium",
        canvas_size=sizes[pair_index % len(sizes)],
        n_corners=n_corners,
        palette_size=n_corners,
        layout=("scatter", "clustered", "separated")[pair_index % 3],
    )
    elbow = python_reference(grid, corner_basis="elbow")
    missing = python_reference(grid, corner_basis="missing")
    if elbow == missing:
        raise AssertionError("prototype input failed to distinguish corner_basis")
    return grid


def build_episode(
    episode_seed: int,
    *,
    corner_basis: str | None = None,
    train_count: int = 3,
    query_count: int = 1,
) -> dict[str, Any]:
    """Build one complete private episode with a single fixed rule setting."""
    if type(episode_seed) is not int:
        raise TypeError("episode seed must be an integer (not bool)")
    if type(train_count) is not int or not 1 <= train_count <= 8:
        raise ValueError("train_count must be an integer in 1..8")
    if type(query_count) is not int or not 1 <= query_count <= 4:
        raise ValueError("query_count must be an integer in 1..4")
    setting = (
        choose_parameters(episode_seed)["corner_basis"]
        if corner_basis is None
        else _validate_basis(corner_basis)
    )
    pairs = []
    for pair_index in range(train_count + query_count):
        grid = _build_input(episode_seed, pair_index)
        pairs.append(
            {
                "input": grid,
                "output": python_reference(grid, corner_basis=setting),
            }
        )
    episode = {
        "schema": "3ab9aab86992-corner-basis-private-v1",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "episode_seed": episode_seed,
        "parameter": {"corner_basis": setting},
        "program": racket_program(setting),
        "program_sha256": rule_sha256(setting),
        "generator_source": str(SELECTED_SOURCE),
        "generator_source_sha256": SELECTED_SOURCE_SHA256,
        "train": pairs[:train_count],
        "test": pairs[train_count:],
    }
    findings = parameter_rival_findings(episode)
    if findings:
        raise AssertionError(findings)
    return episode


def parameter_rival_findings(episode: dict[str, Any]) -> list[str]:
    """Check the one declared parameter rival against demos and queries."""
    setting = episode["parameter"]["corner_basis"]
    _validate_basis(setting)
    rival = next(value for value in ALLOWED_CORNER_BASES if value != setting)
    findings: list[str] = []
    demos = episode.get("train", [])
    if not demos:
        findings.append("episode has no demonstrations")
    for index, pair in enumerate(demos):
        selected = python_reference(pair["input"], corner_basis=setting)
        rival_output = python_reference(pair["input"], corner_basis=rival)
        if selected != pair.get("output"):
            findings.append(f"demonstration {index} disagrees with selected setting")
        if rival_output == pair.get("output"):
            findings.append(f"demonstration {index} does not distinguish rival {rival}")
    for index, pair in enumerate(episode.get("test", [])):
        selected = python_reference(pair["input"], corner_basis=setting)
        rival_output = python_reference(pair["input"], corner_basis=rival)
        if selected != pair.get("output"):
            findings.append(f"query {index} disagrees with selected setting")
        if rival_output == pair.get("output"):
            findings.append(f"query {index} does not distinguish rival {rival}")
    return findings


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Remove hidden setting, programs, provenance, and query answers."""
    return {
        "schema": "3ab9aab86992-parametric-public-v1",
        "train": copy.deepcopy(episode["train"]),
        "test": [
            {"input": copy.deepcopy(pair["input"])} for pair in episode["test"]
        ],
    }


def _rule_body(program: str) -> str:
    text = program.strip()
    if not text.startswith("(rule!") or not text.endswith(")"):
        raise ValueError("prototype program must be a (rule! BODY) form")
    return text[len("(rule!") : -1].strip()


def execute(
    bridge: RacketBridge, program: str, grid: list[list[int]]
) -> list[list[int]]:
    """Execute a materialized ``(rule! (lambda (g) ...))`` program."""
    bridge.define_grid("g", grid)
    return bridge.eval_text(f"({_rule_body(program)} g)")


def _find_seed_for(setting: str, start: int, used: set[int]) -> int:
    seed = start
    while seed in used or choose_parameters(seed)["corner_basis"] != setting:
        seed += 1
    return seed


def write_evidence(
    out_dir: Path, *, seed_start: int = 7300, seeds: list[int] | None = None
) -> dict[str, Any]:
    """Execute complete episodes in Racket and retain private/public evidence."""
    out_dir = Path(out_dir)
    rules_dir = out_dir / "rules"
    private_dir = out_dir / "private"
    public_dir = out_dir / "public"
    for directory in (out_dir, rules_dir, private_dir, public_dir):
        directory.mkdir(parents=True, exist_ok=True)

    for setting in ALLOWED_CORNER_BASES:
        (rules_dir / f"{setting}.rkt").write_text(
            racket_program(setting), encoding="utf-8"
        )

    if seeds is None:
        used: set[int] = set()
        selected_seeds = [
            _find_seed_for(setting, seed_start + index, used)
            for index, setting in enumerate(ALLOWED_CORNER_BASES)
        ]
    else:
        selected_seeds = list(seeds)
    episodes = []
    cross_witnesses = []

    with RacketBridge(max_calls_before_restart=128) as bridge:
        for seed in selected_seeds:
            episode = build_episode(seed)
            setting = episode["parameter"]["corner_basis"]
            program = episode["program"]
            for split in ("train", "test"):
                for pair_index, pair in enumerate(episode[split]):
                    actual = execute(bridge, program, pair["input"])
                    expected = python_reference(pair["input"], corner_basis=setting)
                    if actual != expected:
                        raise AssertionError(
                            f"Racket/Python mismatch seed={seed} {split}[{pair_index}]"
                        )
                    pair["output"] = actual
            findings = parameter_rival_findings(episode)
            if findings:
                raise AssertionError(findings)

            public = public_challenge(episode)
            private_path = private_dir / f"episode_seed_{seed}.json"
            public_path = public_dir / f"challenge_seed_{seed}.json"
            private_path.write_text(json.dumps(episode, indent=2) + "\n")
            public_path.write_text(json.dumps(public, indent=2) + "\n")

            witness_grid = episode["train"][0]["input"]
            outputs = {
                basis: execute(bridge, racket_program(basis), witness_grid)
                for basis in ALLOWED_CORNER_BASES
            }
            if outputs["elbow"] == outputs["missing"]:
                raise AssertionError("cross-setting Racket witness did not differ")
            witness = {
                "episode_seed": seed,
                "input": witness_grid,
                "outputs": outputs,
                "output_sha256": {
                    basis: sha256_json(output) for basis, output in outputs.items()
                },
            }
            cross_witnesses.append(witness)
            episodes.append(
                {
                    "episode_seed": seed,
                    "corner_basis": setting,
                    "program_path": str((rules_dir / f"{setting}.rkt").relative_to(out_dir)),
                    "program_text": program,
                    "program_sha256": sha256_text(program),
                    "private_path": str(private_path.relative_to(out_dir)),
                    "private_sha256": hashlib.sha256(private_path.read_bytes()).hexdigest(),
                    "public_path": str(public_path.relative_to(out_dir)),
                    "public_sha256": hashlib.sha256(public_path.read_bytes()).hexdigest(),
                    "train_count": len(episode["train"]),
                    "query_count": len(episode["test"]),
                    "parameter_rival_findings": findings,
                }
            )

    if {row["corner_basis"] for row in episodes} != set(ALLOWED_CORNER_BASES):
        raise ValueError("evidence seeds must cover both corner_basis settings")

    source_path = Path(__file__).resolve()
    canonical = canonical_record()
    report = {
        "schema": "3ab9aab86992-parametric-evidence-v1",
        "status": STATUS,
        "task_id": TASK_ID,
        "parameter": PARAMETER,
        "prototype_source": str(source_path),
        "prototype_source_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "selected_generator_source": str(SELECTED_SOURCE),
        "selected_generator_source_sha256": SELECTED_SOURCE_SHA256,
        "canonical_content_hash": canonical.get("content_hash"),
        "canonical_program_sha256": sha256_text(canonical["program_solution"]),
        "programs": {
            basis: {
                "path": f"rules/{basis}.rkt",
                "text": racket_program(basis),
                "sha256": rule_sha256(basis),
            }
            for basis in ALLOWED_CORNER_BASES
        },
        "episodes": episodes,
        "cross_setting_witnesses": cross_witnesses,
        "run_command": [
            "python3",
            "review.py",
            "run",
            "python3",
            f"generators/{TASK_ID}/workspace/parametric/prototype.py",
            "--out",
            "../checks/parametric",
        ],
        "limitations": [
            "Prototype only: it is not wired into production generation, canonical authority, catalog approval, or training admission.",
            "Evidence covers two deterministic complete episodes and the single declared parameter rival, not every seed or every conceivable rival rule.",
            "The generator deliberately uses incomplete orientation sets or distinct colors; a four-orientation same-color scene would make the two settings answer-equivalent.",
        ],
    }
    (out_dir / "cross_setting_witnesses.json").write_text(
        json.dumps(cross_witnesses, indent=2) + "\n"
    )
    (out_dir / "evidence.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


materialize = write_evidence


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--seed-start", type=int, default=7300)
    args = parser.parse_args()
    report = write_evidence(args.out, seed_start=args.seed_start)
    print(
        json.dumps(
            {
                "status": report["status"],
                "parameter": report["parameter"],
                "episodes": [
                    {
                        "episode_seed": row["episode_seed"],
                        "corner_basis": row["corner_basis"],
                        "program_sha256": row["program_sha256"],
                    }
                    for row in report["episodes"]
                ],
                "evidence": str(args.out / "evidence.json"),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
