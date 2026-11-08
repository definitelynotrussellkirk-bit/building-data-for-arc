#!/usr/bin/env python3
"""Isolated episode-level edge-selection parameter for e3be2a9d8ce2.

The production generator and canonical authority stay unchanged.  The hidden
``edge_mode`` is chosen once per episode:

* ``near`` (canonical/default): each emitter sends its two arms to nearer edges;
  exact center ties point down/right.
* ``far`` (proposed): the same emitter sends its arms to farther edges; exact
  center ties point up/left.

Inputs contain one lawful interior emitter, so all object/color roles and the
L-ray construction remain unchanged while every pair distinguishes the modes.
Retained labels are checked by executing the exact materialized Racket program.
"""
from __future__ import annotations

import argparse
from contextlib import nullcontext
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import canonical_path, find_root, normalize_grid

TASK_ID = "e3be2a9d8ce2"
PROTOTYPE_VERSION = "1.0.0"
EDGE_MODES = ("near", "far")
DEFAULT_EDGE_MODE = "near"


def _root(root=None) -> Path:
    return Path(root).resolve() if root is not None else find_root(__file__)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def canonical_record(root=None) -> dict[str, Any]:
    """Return one canonical row, tolerating byte-identical duplicate records."""
    matches: list[dict[str, Any]] = []
    with canonical_path(_root(root)).open(encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                matches.append(row)
    if not matches:
        raise ValueError(f"no canonical record found for {TASK_ID}")
    programs = {row.get("program_solution") for row in matches}
    if len(programs) != 1:
        raise ValueError(
            f"canonical records for {TASK_ID} disagree on program_solution"
        )
    return matches[0]


def _validate_mode(edge_mode: Any) -> str:
    if type(edge_mode) is not str or edge_mode not in EDGE_MODES:
        raise ValueError(f"edge_mode must be one of {EDGE_MODES}, got {edge_mode!r}")
    return edge_mode


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative literal integer")
    return seed


def choose_edge_mode(seed: int) -> str:
    """Choose one hidden setting deterministically for the entire episode."""
    _validate_seed(seed)
    digest = hashlib.sha256(
        f"{TASK_ID}|edge_mode|{PROTOTYPE_VERSION}|{seed}".encode("utf-8")
    ).digest()
    return EDGE_MODES[digest[0] % len(EDGE_MODES)]


def program_for(edge_mode: str, *, root=None) -> str:
    """Materialize exact Racket for one bounded parameter setting."""
    mode = _validate_mode(edge_mode)
    canonical = canonical_record(root)["program_solution"]
    if mode == DEFAULT_EDGE_MODE:
        return canonical

    replacements = {
        "(go-up (< (* 2 pr) (- h 1)))": "(go-up (>= (* 2 pr) (- h 1)))",
        "(go-left (< (* 2 pc) (- w 1)))": "(go-left (>= (* 2 pc) (- w 1)))",
    }
    far = canonical
    for old, new in replacements.items():
        if far.count(old) != 1:
            raise ValueError(f"canonical source no longer has expected form: {old}")
        far = far.replace(old, new, 1)
    return far


def program_sha256(edge_mode: str, *, root=None) -> str:
    return _sha256_text(program_for(edge_mode, root=root))


def _generator_path() -> Path:
    return Path(__file__).resolve().parents[2] / "generator.py"


def _load_generator():
    source = _generator_path()
    spec = importlib.util.spec_from_file_location(
        "parametric_e3be2a9d8ce2_generator", source
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import selected generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def apply_python(grid: list[list[int]], edge_mode: str) -> list[list[int]]:
    """Diagnostic mirror; retained evidence labels come from Racket execution."""
    mode = _validate_mode(edge_mode)
    generator = _load_generator()
    errors = generator.self_check(grid)
    if errors:
        raise ValueError("invalid prototype input: " + "; ".join(errors))
    emitters = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    if len(emitters) != 1:
        raise ValueError("edge-mode prototype requires exactly one emitter")

    height, width = len(grid), len(grid[0])
    row, col, color = emitters[0]
    near_up = 2 * row < height - 1
    near_left = 2 * col < width - 1
    go_up = near_up if mode == "near" else not near_up
    go_left = near_left if mode == "near" else not near_left

    output = [[0 for _ in range(width)] for _ in range(height)]
    rows = range(0, row + 1) if go_up else range(row, height)
    cols = range(0, col + 1) if go_left else range(col, width)
    for target_row in rows:
        output[target_row][col] = color
    for target_col in cols:
        output[row][target_col] = color
    return output


def _episode_inputs(seed: int) -> list[list[list[int]]]:
    generator = _load_generator()
    return [
        generator.generate(
            seed,
            sample_index,
            difficulty="medium",
            n_pixels=1,
            palette_size=1,
        )
        for sample_index in range(4)
    ]


def build_episode(seed: int, edge_mode: str | None = None) -> dict[str, Any]:
    """Build three demonstrations and one query under one fixed setting."""
    _validate_seed(seed)
    mode = choose_edge_mode(seed) if edge_mode is None else _validate_mode(edge_mode)
    pairs = [
        {"input": copy.deepcopy(grid), "output": apply_python(grid, mode)}
        for grid in _episode_inputs(seed)
    ]
    return {
        "schema": "arcpuzzles-parametric-edge-mode-episode-v1",
        "train": pairs[:3],
        "test": pairs[3:],
        "program": program_for(mode),
        "meta": {
            "task_id": TASK_ID,
            "seed": seed,
            "edge_mode": mode,
            "canonical_default": DEFAULT_EDGE_MODE,
            "prototype_version": PROTOTYPE_VERSION,
            "sample_indices": [0, 1, 2, 3],
            "selection": "chosen once for the episode",
        },
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Return a solver-safe view with hidden parameter and query answer removed."""
    return {
        "schema": "arcpuzzles-parametric-edge-mode-public-v1",
        "train": copy.deepcopy(episode["train"]),
        "test": [{"input": copy.deepcopy(pair["input"])} for pair in episode["test"]],
    }


def parameter_rival_findings(episode: dict[str, Any]) -> list[str]:
    mode = _validate_mode(episode["meta"]["edge_mode"])
    rival = "far" if mode == "near" else "near"
    findings: list[str] = []
    if not any(
        apply_python(pair["input"], rival) != pair["output"]
        for pair in episode["train"]
    ):
        findings.append(f"rival setting {rival!r} fits every demonstration")
    if any(
        apply_python(pair["input"], rival) == pair["output"]
        for pair in episode["test"]
    ):
        findings.append(f"query does not distinguish rival setting {rival!r}")
    return findings


def execute_program(
    bridge: RacketBridge, program: str, grid: list[list[int]]
) -> list[list[int]]:
    """Execute an exact `(rule! (lambda ...))` program on one grid."""
    body = strip_rule_wrapper(program)
    if not body.lstrip().startswith(("(lambda", "(λ")):
        raise ValueError("prototype expects a lambda-bodied rule")
    bridge.define_grid("__edge_mode_input__", normalize_grid(grid))
    return normalize_grid(bridge.eval_text(f"({body} __edge_mode_input__)"))


def _bridge_context(bridge):
    return (
        nullcontext(bridge)
        if bridge is not None
        else RacketBridge(timeout=15, startup_timeout=60)
    )


def _find_seed_for(setting: str, start: int, used: set[int]) -> int:
    seed = start
    while seed in used or choose_edge_mode(seed) != setting:
        seed += 1
    return seed


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_evidence(seed: int, out_dir: str | Path) -> dict[str, Any]:
    """Execute both settings and retain private/public bounded evidence."""
    _validate_seed(seed)
    out = Path(out_dir)
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty evidence directory: {out}")
    out.mkdir(parents=True, exist_ok=True)

    used: set[int] = set()
    settings: dict[str, Any] = {}
    canonical = canonical_record()
    programs = {mode: program_for(mode) for mode in EDGE_MODES}

    with _bridge_context(None) as bridge:
        for offset, mode in enumerate(EDGE_MODES):
            episode_seed = _find_seed_for(mode, seed + offset, used)
            used.add(episode_seed)
            episode = build_episode(episode_seed, edge_mode=mode)
            rival = "far" if mode == "near" else "near"
            executed: list[dict[str, Any]] = []

            for split in ("train", "test"):
                for pair_index, pair in enumerate(episode[split]):
                    actual = execute_program(bridge, programs[mode], pair["input"])
                    rival_output = execute_program(
                        bridge, programs[rival], pair["input"]
                    )
                    python_output = apply_python(pair["input"], mode)
                    if actual != python_output or actual != pair["output"]:
                        raise AssertionError(
                            f"Racket/Python mismatch for {mode} {split}[{pair_index}]"
                        )
                    if actual == rival_output:
                        raise AssertionError(
                            f"{mode} {split}[{pair_index}] does not distinguish {rival}"
                        )
                    pair["output"] = actual
                    executed.append(
                        {
                            "split": split,
                            "pair_index": pair_index,
                            "input_sha256": _sha256_json(pair["input"]),
                            "racket_output": actual,
                            "rival_setting": rival,
                            "rival_racket_output": rival_output,
                            "settings_disagree": True,
                        }
                    )

            findings = parameter_rival_findings(episode)
            if findings:
                raise AssertionError("; ".join(findings))

            rule_path = out / "private" / "rules" / f"edge_mode_{mode}.rkt"
            rule_path.parent.mkdir(parents=True, exist_ok=True)
            rule_path.write_text(programs[mode] + "\n", encoding="utf-8")
            private_path = out / "private" / f"edge_mode_{mode}.json"
            public_path = out / "public" / f"edge_mode_{mode}.json"
            _write_json(private_path, episode)
            _write_json(public_path, public_challenge(episode))
            settings[mode] = {
                "seed": episode_seed,
                "selected_once_by_seed": choose_edge_mode(episode_seed),
                "is_canonical_default": mode == DEFAULT_EDGE_MODE,
                "program_path": str(rule_path.relative_to(out)),
                "program_text": programs[mode],
                "program_sha256": _sha256_text(programs[mode]),
                "private_episode_path": str(private_path.relative_to(out)),
                "public_challenge_path": str(public_path.relative_to(out)),
                "episode_sha256": _sha256_json(episode),
                "executed_pairs": executed,
                "all_pairs_match_racket": True,
                "every_demo_refutes_rival": True,
                "query_refutes_rival": True,
                "canonical_default_exact_text": (
                    mode != DEFAULT_EDGE_MODE
                    or programs[mode] == canonical["program_solution"]
                ),
            }

        witness_grid = settings["near"]["executed_pairs"][0]["racket_output"]
        runtime = racket_runtime_status()

    source = Path(__file__).resolve()
    generator_source = _generator_path()
    report = {
        "schema": "arcpuzzles-parametric-edge-mode-evidence-v1",
        "status": "pass",
        "prototype": "proposed; isolated; not selected or approved",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "parameter": {
            "name": "edge_mode",
            "allowed_values": list(EDGE_MODES),
            "canonical_default": DEFAULT_EDGE_MODE,
            "selection": "SHA-256(task_id|edge_mode|version|seed), once per episode",
            "input_constraints": (
                "exactly one lawful interior emitter per pair; this prevents overlap "
                "and makes near/far differ on every demonstration and query"
            ),
            "invariant_reasoning": [
                "find the nonzero emitter and preserve its color",
                "construct one vertical and one horizontal arm through the emitter",
                "extend each arm inclusively to a selected grid edge",
            ],
            "varied_reasoning": (
                "select nearer edges (ties down/right) versus farther edges "
                "(ties up/left)"
            ),
        },
        "prototype_source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "generator_source_sha256": hashlib.sha256(
            generator_source.read_bytes()
        ).hexdigest(),
        "canonical_program_sha256": _sha256_text(canonical["program_solution"]),
        "runtime": runtime,
        "settings": settings,
        "shared_output_witness_note": (
            "Each retained pair stores both setting outputs; the first near output "
            "hash is " + _sha256_json(witness_grid)
        ),
        "limitations": [
            "Finite evidence covers two settings and one complete episode per setting.",
            "Only the declared near/far parameter rival is tested; arbitrary rules are not exhausted.",
            "The single-emitter prototype deliberately excludes multi-emitter overlap questions.",
            "Production generation, canonical authority, and approval state remain unchanged.",
        ],
    }
    _write_json(out / "report.json", report)
    _write_json(
        out / "command.json",
        {
            "cwd": "WORK/repo",
            "argv": [
                "python3",
                "generators/e3be2a9d8ce2/workspace/parametric/prototype.py",
                "evidence",
                "--seed",
                str(seed),
                "--out",
                str(out_dir),
            ],
        },
    )

    files = {}
    for path in sorted(out.rglob("*")):
        if path.is_file() and path.name != "manifest.json":
            files[str(path.relative_to(out))] = hashlib.sha256(path.read_bytes()).hexdigest()
    _write_json(
        out / "manifest.json",
        {
            "schema": "arcpuzzles-parametric-evidence-manifest-v1",
            "task_id": TASK_ID,
            "files": files,
        },
    )
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("evidence", "episode"))
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--edge-mode", default="seeded", choices=("seeded",) + EDGE_MODES)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    if args.command == "evidence":
        payload = build_evidence(args.seed, args.out)
    else:
        selected = None if args.edge_mode == "seeded" else args.edge_mode
        payload = build_episode(args.seed, edge_mode=selected)
        _write_json(Path(args.out), payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
