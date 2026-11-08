#!/usr/bin/env python3
"""Proposed episode-level missing-column extension parameter for b88894a36787.

The selected production generator and canonical Racket authority remain fixed.
This task-local prototype varies one nearby count parameter once per episode:

* ``bottom`` (canonical/default): a header without a side dot reaches row h-1.
* ``penultimate``: the same unmatched header stops at row h-2.

Header detection, color matching, side-dot L paths, first-match priority, and all
input roles remain unchanged. Retained labels are executed by the exact Racket
program materialized for each setting; the Python implementation is diagnostic.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

TASK_ID = "b88894a36787"
PROTOTYPE_VERSION = "1.0.0"
ALLOWED_MISSING_EXTENSIONS = ("bottom", "penultimate")
DEFAULT_MISSING_EXTENSION = "bottom"
_CANONICAL_PROGRAM = '(rule! (lambda (g)\n         (let* ((h (rows g))\n                (w (cols g))\n                (header (filter (lambda (c2) (!= (at g 0 c2) 0)) (range 0 w)))\n                (header-colors (map (lambda (c2) (at g 0 c2)) header))\n                (dots (filter (lambda (x) x)\n                              (for*/list ((r (range 1 h)) (c2 (range 0 w)))\n                                (and (!= (at g r c2) 0) (list r c2 (at g r c2))))))\n                (entries (for/list ((i (range 0 (length header))))\n                           (let* ((hc (list-ref header i))\n                                  (hcol (list-ref header-colors i))\n                                  (dot (find (lambda (d) (= (third d) hcol)) dots)))\n                             (list hc\n                                   hcol\n                                   (if dot (first dot) (- h 1))\n                                   (and dot (second dot)))))))\n           (cellmap g\n                    (r c v)\n                    (let* ((match (find (lambda (e)\n                                          (let* ((ecol (first e))\n                                                 (ecolor (second e))\n                                                 (trow (third e))\n                                                 (tcol (fourth e)))\n                                            (or\n                                              (and (= c ecol) (<= r trow))\n                                              (and\n                                                tcol\n                                                (= r trow)\n                                                (if (< tcol ecol)\n                                                    (and (>= c tcol) (<= c ecol))\n                                                    (and (>= c ecol) (<= c tcol)))))))\n                                        entries)))\n                      (if match (second match) 0))))))'
_CANONICAL_FALLBACK = "(if dot (first dot) (- h 1))"
_PENULTIMATE_FALLBACK = "(if dot (first dot) (- h 2))"


def _validate_missing_extension(value: str) -> str:
    if value not in ALLOWED_MISSING_EXTENSIONS:
        raise ValueError(
            f"missing_extension must be one of {ALLOWED_MISSING_EXTENSIONS}, got {value!r}"
        )
    return value


def _validate_seed(seed: int) -> int:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    return seed


def choose_missing_extension(seed: int) -> str:
    """Select one hidden rule setting deterministically for the whole episode."""
    _validate_seed(seed)
    digest = hashlib.sha256(f"{TASK_ID}|missing_extension|{seed}".encode()).digest()
    return ALLOWED_MISSING_EXTENSIONS[digest[0] % len(ALLOWED_MISSING_EXTENSIONS)]


def _generator_path() -> Path:
    return Path(__file__).resolve().parents[2] / "generator.py"


def _load_generator():
    source = _generator_path()
    spec = importlib.util.spec_from_file_location(
        "parametric_b88894a36787_generator", source
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import selected generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def program_for(missing_extension: str) -> str:
    """Return the exact bounded Racket program for one parameter setting."""
    setting = _validate_missing_extension(missing_extension)
    if _CANONICAL_PROGRAM.count(_CANONICAL_FALLBACK) != 1:
        raise RuntimeError("canonical missing-dot fallback is not unique")
    if setting == "bottom":
        return _CANONICAL_PROGRAM
    return _CANONICAL_PROGRAM.replace(
        _CANONICAL_FALLBACK, _PENULTIMATE_FALLBACK, 1
    )


def program_sha256(missing_extension: str) -> str:
    return hashlib.sha256(program_for(missing_extension).encode()).hexdigest()


def apply_python(grid: list[list[int]], missing_extension: str) -> list[list[int]]:
    """Diagnostic mirror of one setting; Racket supplies retained labels."""
    setting = _validate_missing_extension(missing_extension)
    generator = _load_generator()
    h, w = len(grid), len(grid[0])
    entries = []
    for header_col, color, target_row, target_col in generator._entries(grid):
        if target_col is None:
            target_row = h - 1 if setting == "bottom" else h - 2
        entries.append((header_col, color, target_row, target_col))

    out = [[0 for _ in range(w)] for _ in range(h)]
    for row in range(h):
        for col in range(w):
            for header_col, color, target_row, target_col in entries:
                vertical = col == header_col and row <= target_row
                horizontal = (
                    target_col is not None
                    and row == target_row
                    and min(header_col, target_col) <= col <= max(header_col, target_col)
                )
                if vertical or horizontal:
                    out[row][col] = color
                    break
    return out


def _rule_body(program: str) -> str:
    text = program.strip()
    if not text.startswith("(rule!") or not text.endswith(")"):
        raise ValueError("prototype program must be a (rule! BODY) form")
    return text[len("(rule!") : -1].strip()


def _grid_literal(grid: list[list[int]]) -> str:
    rows = " ".join("(" + " ".join(map(str, row)) + ")" for row in grid)
    return f"'({rows})"


def apply_racket(bridge, program: str, grid: list[list[int]]) -> list[list[int]]:
    """Execute the exact materialized rule body in the protected Racket prelude."""
    body = _rule_body(program)
    expression = (
        f"(let* ((g {_grid_literal(grid)}) (h (rows g)) (w (cols g))) "
        f"({body} g))"
    )
    result = bridge.eval_text(expression)
    if not isinstance(result, list):
        raise RuntimeError(f"Racket returned a non-grid result: {result!r}")
    return result


def _episode_inputs(seed: int) -> list[list[list[int]]]:
    """Use four lawful one-missing-dot schedule slots for identifiable episodes."""
    _validate_seed(seed)
    generator = _load_generator()
    grids = [
        generator.generate(seed, sample_index, difficulty="medium", n_markers=4)
        for sample_index in (0, 1, 2, 3)
    ]
    for grid in grids:
        errors = generator.self_check(grid)
        if errors:
            raise AssertionError(f"prototype received invalid selected-generator input: {errors}")
        if sum(entry[3] is None for entry in generator._entries(grid)) != 1:
            raise AssertionError("prototype episodes require exactly one missing side dot")
    return grids


def build_episode(
    seed: int, missing_extension: str | None = None
) -> dict[str, Any]:
    """Build three demonstrations and one query under one fixed hidden setting."""
    _validate_seed(seed)
    setting = (
        choose_missing_extension(seed)
        if missing_extension is None
        else _validate_missing_extension(missing_extension)
    )
    sample_indices = [0, 1, 2, 3]
    pairs = [
        {"input": copy.deepcopy(grid), "output": apply_python(grid, setting)}
        for grid in _episode_inputs(seed)
    ]
    return {
        "schema": "arcpuzzles-parametric-missing-extension-episode-v1",
        "train": pairs[:3],
        "test": pairs[3:],
        "program": program_for(setting),
        "meta": {
            "task_id": TASK_ID,
            "seed": seed,
            "missing_extension": setting,
            "canonical_default": DEFAULT_MISSING_EXTENSION,
            "prototype_version": PROTOTYPE_VERSION,
            "sample_indices": sample_indices,
        },
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Remove the hidden setting, reference program, and query answer."""
    return {
        "schema": "arcpuzzles-parametric-missing-extension-public-v1",
        "train": copy.deepcopy(episode["train"]),
        "test": [{"input": copy.deepcopy(pair["input"])} for pair in episode["test"]],
    }


def parameter_rival_findings(episode: dict[str, Any]) -> list[str]:
    setting = episode["meta"]["missing_extension"]
    rival = next(value for value in ALLOWED_MISSING_EXTENSIONS if value != setting)
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


def _sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def _find_seed_for(setting: str, start: int, used: set[int]) -> int:
    seed = _validate_seed(start)
    while seed in used or choose_missing_extension(seed) != setting:
        seed += 1
    return seed


def materialize(out_dir: Path, seed_start: int = 7319) -> dict[str, Any]:
    """Execute both settings in Racket and retain public/private evidence."""
    from arc_repl.racket_bridge import RacketBridge
    from arcpuzzles import Catalog

    _validate_seed(seed_start)
    if out_dir.exists():
        raise FileExistsError(f"choose a new evidence directory: {out_dir}")
    out_dir.mkdir(parents=True)
    public_dir = out_dir / "public"
    private_dir = out_dir / "private"
    rule_dir = out_dir / "rules"
    public_dir.mkdir()
    private_dir.mkdir()
    rule_dir.mkdir()

    root = Path(__file__).resolve().parents[4]
    source = Path(__file__).resolve()
    generator_source = _generator_path()
    generator = _load_generator()
    catalog = Catalog(root)
    bridge = RacketBridge(max_calls_before_restart=128, timeout=30.0)
    settings: dict[str, Any] = {}
    used: set[int] = set()
    witness: dict[str, Any] | None = None
    try:
        for offset, setting in enumerate(ALLOWED_MISSING_EXTENSIONS):
            seed = _find_seed_for(setting, seed_start + offset, used)
            used.add(seed)
            episode = build_episode(seed, missing_extension=setting)
            program = program_for(setting)
            rival = next(
                value for value in ALLOWED_MISSING_EXTENSIONS if value != setting
            )
            rival_program = program_for(rival)
            executed: list[dict[str, Any]] = []
            inputs: list[list[list[int]]] = []

            for split in ("train", "test"):
                for pair_index, pair in enumerate(episode[split]):
                    input_grid = pair["input"]
                    actual = apply_racket(bridge, program, input_grid)
                    rival_output = apply_racket(bridge, rival_program, input_grid)
                    python_output = apply_python(input_grid, setting)
                    if actual != python_output or actual != pair["output"]:
                        raise AssertionError(
                            f"Racket/Python mismatch for {setting} {split}[{pair_index}]"
                        )
                    pair["output"] = actual
                    inputs.append(input_grid)
                    record = {
                        "split": split,
                        "pair_index": pair_index,
                        "input_sha256": _sha256_json(input_grid),
                        "racket_output": actual,
                        "rival_setting": rival,
                        "rival_racket_output": rival_output,
                        "settings_disagree": actual != rival_output,
                    }
                    executed.append(record)
                    if witness is None and record["settings_disagree"]:
                        witness = {
                            "input": input_grid,
                            "self_check": generator.self_check(input_grid),
                            "setting_outputs": {
                                setting: actual,
                                rival: rival_output,
                            },
                            "input_sha256": record["input_sha256"],
                        }

            canonical_parity = None
            if setting == DEFAULT_MISSING_EXTENSION:
                reference = catalog.apply(
                    TASK_ID, inputs, reference="canonical", timeout=180
                )
                if any(item.get("error") for item in reference["results"]):
                    raise RuntimeError(f"canonical reference failed: {reference}")
                reference_outputs = [item["output"] for item in reference["results"]]
                actual_outputs = [item["racket_output"] for item in executed]
                canonical_parity = reference_outputs == actual_outputs
                if not canonical_parity:
                    raise AssertionError(
                        "default bottom prototype diverges from canonical Racket"
                    )

            findings = parameter_rival_findings(episode)
            if findings:
                raise AssertionError("; ".join(findings))
            if not all(item["settings_disagree"] for item in executed):
                raise AssertionError(f"some {setting} pairs do not distinguish {rival}")

            rule_path = rule_dir / f"missing_extension_{setting}.rkt"
            rule_path.write_text(program + "\n")
            public_path = public_dir / f"missing_extension_{setting}.json"
            public_path.write_text(
                json.dumps(public_challenge(episode), indent=2, sort_keys=True) + "\n"
            )
            private_path = private_dir / f"missing_extension_{setting}.json"
            private_path.write_text(
                json.dumps(episode, indent=2, sort_keys=True) + "\n"
            )
            settings[setting] = {
                "seed": seed,
                "selected_once_by_seed": choose_missing_extension(seed),
                "is_canonical_default": setting == DEFAULT_MISSING_EXTENSION,
                "program_path": str(rule_path.relative_to(out_dir)),
                "program_text": program,
                "program_sha256": program_sha256(setting),
                "episode_path": str(private_path.relative_to(out_dir)),
                "episode_sha256": hashlib.sha256(private_path.read_bytes()).hexdigest(),
                "public_path": str(public_path.relative_to(out_dir)),
                "public_sha256": hashlib.sha256(public_path.read_bytes()).hexdigest(),
                "executed_pairs": executed,
                "all_pairs_match_racket": True,
                "every_demo_refutes_rival": all(
                    item["settings_disagree"]
                    for item in executed
                    if item["split"] == "train"
                ),
                "query_refutes_rival": all(
                    item["settings_disagree"]
                    for item in executed
                    if item["split"] == "test"
                ),
                "canonical_default_parity": canonical_parity,
            }
        runtime_identity = bridge.runtime_identity
    finally:
        bridge.shutdown()

    if witness is None:
        raise AssertionError("no lawful setting-disagreement witness was produced")
    witness_path = out_dir / "witness.json"
    witness_path.write_text(json.dumps(witness, indent=2, sort_keys=True) + "\n")

    evidence = {
        "schema": "arcpuzzles-parametric-missing-extension-evidence-v1",
        "status": "prototype",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "parameter": {
            "name": "missing_extension",
            "allowed_values": list(ALLOWED_MISSING_EXTENSIONS),
            "canonical_default": DEFAULT_MISSING_EXTENSION,
            "selection": "SHA-256(task_id|missing_extension|seed), once per episode",
            "input_constraints": (
                "Every pair is a lawful selected-generator input with exactly one "
                "header color lacking a side dot; both settings use the same input domain."
            ),
            "invariant_reasoning": [
                "find the contiguous colored header in row 0",
                "match each header color to its same-colored side dot when present",
                "draw the matched vertical-then-horizontal L paths",
                "preserve header order and first-match priority",
            ],
            "varied_reasoning": (
                "the terminal row of only the unmatched header column: h-1 versus h-2"
            ),
        },
        "prototype_source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "generator_source_sha256": hashlib.sha256(generator_source.read_bytes()).hexdigest(),
        "runtime_identity": runtime_identity,
        "witness_path": str(witness_path.relative_to(out_dir)),
        "witness_sha256": hashlib.sha256(witness_path.read_bytes()).hexdigest(),
        "settings": settings,
        "limitations": [
            "Two settings and one retained episode per setting; this is not a production API or approval.",
            "Production generation and the canonical authority remain fixed at bottom.",
            "The evidence exhausts only the declared bottom/penultimate rival, not arbitrary programs.",
        ],
    }
    evidence_path = out_dir / "evidence.json"
    evidence_path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    command = {
        "cwd": "WORK/repo",
        "argv": [
            "python3",
            "generators/b88894a36787/workspace/parametric/missing_extension.py",
            "--out",
            str(out_dir),
            "--seed-start",
            str(seed_start),
        ],
        "evidence_sha256": hashlib.sha256(evidence_path.read_bytes()).hexdigest(),
    }
    (out_dir / "command.json").write_text(
        json.dumps(command, indent=2, sort_keys=True) + "\n"
    )
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--seed-start", type=int, default=7319)
    args = parser.parse_args()
    evidence = materialize(args.out, seed_start=args.seed_start)
    print(json.dumps({
        "status": evidence["status"],
        "task_id": TASK_ID,
        "out": str(args.out),
        "settings": {
            name: {
                "seed": record["seed"],
                "program_sha256": record["program_sha256"],
                "every_demo_refutes_rival": record["every_demo_refutes_rival"],
                "query_refutes_rival": record["query_refutes_rival"],
                "canonical_default_parity": record["canonical_default_parity"],
            }
            for name, record in evidence["settings"].items()
        },
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
